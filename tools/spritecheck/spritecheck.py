#!/usr/bin/env python3
"""Check every Pokémon sprite the ROM ships: placement, frames, palettes, icons, followers.

Reads what the build actually ships, after every #if: gSpeciesInfo from the ROM, its layout from
a -g compile of the game headers, each pointer's symbol from the ELF, and the PNG/PAL each symbol
was built from (cpp of src/pokemon.c). Measures every image and compares it with the data.

    tools/spritecheck/spritecheck.py                   # pokehns.gba + .elf: ERROR and WARN findings
    tools/spritecheck/spritecheck.py --level INFO      # and the review-by-eye ones
    tools/spritecheck/spritecheck.py --strict          # exit 1 on an ERROR/WARN not in known.txt
    tools/spritecheck/spritecheck.py --json out.json   # per-species data, for sheet.py

Checks (ERROR = visibly wrong in game, WARN = probably wrong, INFO = review by eye):
  front-y, back-y        the Y offset isn't the blank rows under frame 0's drawing, so the
                         Pokémon floats over or sinks into its platform (female sprites too)
  frame-range            the front animation shows a frame the sheet doesn't have (garbage tiles)
  shiny-same             the shiny palette is the normal one: a shiny looks like any other
  female-style           a GBA-style species would show a DS-style female sprite
  icon-pal               the icon's palette slot isn't the closest of the six to its own colours
  ow-missing             the follower is the substitute doll
  ow-shiny-same          the follower's shiny palette is the normal one
  front-size, back-size  the size battle animations aim at isn't the drawing's (INFO)
  static-front, icon-static, stray, pal-drift, levitate   (INFO)

The Y offset rule ("pixels between the drawn area and the bottom edge", include/pokemon.h)
gives Emerald's own front offset for all 385 Gen 1-3 species and its back offset for 382; of the
other three, Castform's and Deoxys's art isn't Emerald's and Ninjask's float is (known.txt).
known.txt lists findings that are right as they are, with the reason.

Check a ROM built from this tree as it is now: symbols map to files through this tree's
preprocessed source, so a config flip (P_GBA_STYLE_SPECIES_GFX) needs the same flip here.
Needs arm-none-eabi-{gcc,cpp,nm,gdb} on PATH and Pillow.
"""
import argparse
import collections
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
KNOWN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "known.txt")
CPPFLAGS = ["-iquote", "include", "-Wno-trigraphs", "-DMODERN=1", "-DTESTING=0", "-DPOKEMON_HNS",
            "-std=gnu17"]
CFLAGS = ["-mthumb", "-mthumb-interwork", "-O2", "-mabi=apcs-gnu", "-mtune=arm7tdmi", "-march=armv4t"]
ROM_BASE = 0x08000000
FRAME = 64
LEVEL = {"ERROR": 0, "WARN": 1, "INFO": 2}


def tool(name):
    path = shutil.which("arm-none-eabi-" + name)
    if not path:
        sys.exit(f"spritecheck: arm-none-eabi-{name} isn't on PATH")
    return path


def run(args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True).stdout


# --- what the build ships -------------------------------------------------------------------

LAYOUT_LINE = re.compile(r"^/\*\s*(\d+)(?::\s*(\d+))?\s*\|\s*(\d+)\s*\*/\s*(.*)$")


def struct_layout(tmp, name="SpeciesInfo", header="pokemon.h"):
    """Field -> (offset, bit, size, bits, signed) of a struct, and its size, from gdb's `ptype /o`
    of a -g probe object. Nested struct fields come back as "outer.inner"."""
    probe = os.path.join(tmp, f"probe_{name}.c")
    with open(probe, "w") as f:
        f.write(f'#include "global.h"\n#include "pokemon.h"\n#include "{header}"\nstruct {name} probe{name};\n')
    obj = os.path.join(tmp, f"probe_{name}.o")
    run([tool("gcc")] + CPPFLAGS + CFLAGS + ["-g", "-c", probe, "-o", obj])
    fields, nested, total = {}, None, None
    for line in run([tool("gdb"), "-batch", "-ex", f"ptype /o struct {name}", obj]).splitlines():
        m = LAYOUT_LINE.match(line.strip())
        if m:
            off, bit, size, decl = int(m[1]), int(m[2] or 0), int(m[3]), m[4].strip()
            if decl.endswith("{"):
                nested = {}
                continue
            decl, bits = decl.rstrip(";"), None
            if " : " in decl:
                decl, bits = decl.rsplit(" : ", 1)
                bits = int(bits)
            name = re.sub(r"\[.*\]$", "", decl.split()[-1]).lstrip("*")
            signed = bool(re.match(r"(const\s+)?(s8|s16|s32)\b", decl))
            (nested if nested is not None else fields)[name] = (off, bit, size, bits, signed)
            continue
        closer = re.match(r"^\}\s*(\w+);$", line.strip())
        if closer and nested is not None:
            fields.update({f"{closer[1]}.{k}": v for k, v in nested.items()})
            nested = None
        total_m = re.search(r"total size \(bytes\):\s*(\d+)", line)
        if total_m and nested is None:
            total = int(total_m[1])
    return fields, total


def symbols(elf):
    """Address -> name for every defined symbol, and name -> (address, size)."""
    by_addr, by_name = {}, {}
    for line in run([tool("nm"), "-S", "--defined-only", elf]).splitlines():
        parts = line.split()
        if len(parts) == 4:
            addr, size, name = int(parts[0], 16), int(parts[1], 16), parts[3]
        elif len(parts) == 3:
            addr, size, name = int(parts[0], 16), 0, parts[2]
        else:
            continue
        by_name.setdefault(name, (addr, size))
        by_addr.setdefault(addr, name)
    return by_addr, by_name


def asset_paths(tmp):
    """Symbol -> source file, from the INCBINs cpp leaves in place (preproc expands them later):
    the species art in src/pokemon.c and the DS-style art in src/species_gfx_style.c."""
    paths = {}
    for src in ("src/pokemon.c", "src/species_gfx_style.c"):
        if os.path.exists(os.path.join(ROOT, src)):
            text = run([tool("cpp")] + CPPFLAGS + [src])
            paths.update(re.findall(r"\b(\w+)\[\]\s*=\s*INCBIN_\w+\(\"([^\"]+)\"\)", text))
    return paths


def constants(tmp, header, prefix):
    """Value -> first NAME for every `#define PREFIX_NAME <expr>` or `PREFIX_NAME = <n>,` in a header."""
    text = open(os.path.join(ROOT, header)).read()
    values = {int(v): n for n, v in reversed(re.findall(rf"^\s*({prefix}\w+)\s*=\s*(\d+)\s*,", text, re.M))}
    probe = os.path.join(tmp, "consts.c")
    with open(probe, "w") as f:
        f.write(f'#include "global.h"\n#include "{header[len("include/"):]}"\n')
        # A quoted name isn't expanded, so each line keeps its name next to its value.
        f.writelines(f'@@ "{n}" = {n}\n' for n in re.findall(rf"^#define ({prefix}\w+)\s", text, re.M))
    for line in run([tool("cpp")] + CPPFLAGS + [probe]).splitlines():
        if line.startswith("@@ "):
            name, expr = line[3:].split(" = ", 1)
            if re.fullmatch(r"[\d\s()+\-*<>|&]+", expr):
                values.setdefault(int(eval(expr)), name.strip('"'))
    return values


class Rom:
    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = f.read()

    def read(self, addr, n):
        off = addr - ROM_BASE
        return self.data[off:off + n] if 0 <= off < len(self.data) else b""

    def u32(self, addr):
        b = self.read(addr, 4)
        return struct.unpack("<I", b)[0] if len(b) == 4 else 0


def field(raw, layout, name):
    off, bit, size, bits, signed = layout[name]
    if bits is None:
        return int.from_bytes(raw[off:off + size], "little", signed=signed)
    return (int.from_bytes(raw[off:off + 4].ljust(4, b"\0"), "little") >> bit) & ((1 << bits) - 1)


def anim_frames(rom, table_ptr):
    """(frame, duration) pairs of the front animation. ANIM_FRAMES puts the static
    sAnim_GeneralFrame0 at index 0 and the species' own animation at index 1."""
    frames, cmd = [], rom.u32(table_ptr + 4) if table_ptr else 0
    for _ in range(64):
        word = rom.u32(cmd) if cmd else 0xFFFF
        if word & 0xFFFF >= 0xFFFC:  # END, JUMP, LOOP
            break
        frames.append((word & 0xFFFF, (word >> 16) & 0x3F))
        cmd += 4
    return frames


# --- images ---------------------------------------------------------------------------------

def png_for(path):
    return re.sub(r"\.(4bpp|8bpp|1bpp)(\.smol|\.fastSmol|\.lz)?$", "", path) + ".png" if path else None


def pal_for(path):
    return re.sub(r"\.gbapal(\.lz)?$", ".pal", path) if path else None


_img_cache, _pal_cache = {}, {}


def load_png(rel):
    if rel not in _img_cache:
        full = os.path.join(ROOT, rel) if rel else ""
        _img_cache[rel] = Image.open(full) if os.path.exists(full) else None
    return _img_cache[rel]


def load_pal(rel):
    """A JASC .pal as 5-bit (r, g, b) colours, as the GBA sees them."""
    if rel not in _pal_cache:
        full, colors = os.path.join(ROOT, rel) if rel else "", None
        if os.path.exists(full):
            lines = open(full).read().split("\n")
            colors = [tuple(int(x) >> 3 for x in lines[3 + i].split()[:3]) for i in range(int(lines[2]))]
        _pal_cache[rel] = colors
    return _pal_cache[rel]


def png_colors(img):
    raw = img.getpalette() or []
    return [tuple(raw[i + k] >> 3 for k in range(3)) for i in range(0, len(raw), 3)]


def frame_pixels(img, index, size=FRAME):
    """Palette indices of frame `index` in a vertical sheet of size-tall frames, and the width."""
    w = img.size[0]
    return list(img.crop((0, index * size, w, index * size + size)).getdata()), w


def bbox(pixels, w):
    rows = [i // w for i, p in enumerate(pixels) if p]
    cols = [i % w for i, p in enumerate(pixels) if p]
    return (min(cols), min(rows), max(cols), max(rows)) if rows else None


def coords_size(box):
    """MON_COORDS_SIZE the battle code needs: it centres the box on the frame, so the width is
    twice the drawing's furthest reach from the centre column."""
    left, top, right, bottom = box
    width = 2 * max(FRAME // 2 - left, right + 1 - FRAME // 2)
    return (-(-width // 8)) << 4 | (-(-(bottom - top + 1) // 8))


def size_str(size):
    return f"{(size >> 4) * 8}x{(size & 0xF) * 8}"


def strays(pixels, w, h):
    """Opaque specks of 1-2 px touching no other opaque pixel (8-connected)."""
    seen, out = set(), []
    for i, p in enumerate(pixels):
        if not p or i in seen:
            continue
        region, stack = [], [i]
        seen.add(i)
        while stack:
            k = stack.pop()
            region.append(k)
            x, y = k % w, k // w
            for nx, ny in ((x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                j = ny * w + nx
                if 0 <= nx < w and 0 <= ny < h and pixels[j] and j not in seen:
                    seen.add(j)
                    stack.append(j)
        if len(region) <= 2:
            out.append((region[0] % w, region[0] // w))
    return out


def color_distance(a, b):
    """Weighted RGB distance on 5-bit channels ("redmean"), 0 for equal colours."""
    r = (a[0] + b[0]) / 2
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return ((2 + r / 32) * dr * dr + 4 * dg * dg + (2 + (31 - r) / 32) * db * db) ** 0.5


# --- the audit ------------------------------------------------------------------------------

def audit(args):
    tmp = tempfile.mkdtemp(prefix="spritecheck-")
    layout, size = struct_layout(tmp)
    by_addr, by_name = symbols(args.elf)
    assets = asset_paths(tmp)
    species_names = constants(tmp, "include/constants/species.h", "SPECIES_")
    levitate = {n: v for v, n in constants(tmp, "include/constants/abilities.h", "ABILITY_").items()}.get(
        "ABILITY_LEVITATE")
    rom = Rom(args.rom)
    base, table_size = by_name["gSpeciesInfo"]
    icon_pals = [load_pal(f"graphics/pokemon/icon_palettes/pal{i}.pal") for i in range(6)]
    substitute = by_name.get("gObjectEventPic_Substitute", (None,))[0]
    sheet_starts = sorted((a, n) for n, (a, _) in by_name.items() if n.startswith("gObjectEventPic_"))
    rows, findings = [], []

    def find(level, check, sp, detail):
        findings.append((level, check, sp, detail))

    def sheet_at(ptr):
        """The follower sheet a frame pointer lands in (frames point inside their sheet)."""
        hit = None
        for addr, name in sheet_starts:
            if addr > ptr:
                break
            hit = name
        return hit

    def check_y(sp, check, png, frame, data_y):
        img = load_png(png)
        box = bbox(*frame_pixels(img, frame)) if img is not None else None
        if not box:
            return None, None
        want = FRAME - 1 - box[3]
        if data_y != want:
            d = data_y - want
            find("ERROR" if abs(d) >= 3 else "WARN", check, sp,
                 f"Y offset {data_y}, the drawing ends {want} px above the frame bottom: "
                 f"{'sinks' if d > 0 else 'floats'} {abs(d)} px [{png}]")
        return want, coords_size(box)

    def check_icon(sp, png, slot):
        icon = load_png(png)
        if icon is None:
            return None
        if icon.size[1] >= 64 and frame_pixels(icon, 0, 32) == frame_pixels(icon, 1, 32):
            find("INFO", "icon-static", sp, f"both icon frames are the same, the party icon won't move [{png}]")
        px, own = [p for p in icon.getdata() if p], png_colors(icon)
        cost = [sum(color_distance(own[p], pal[p]) for p in px if p < len(own)) / max(len(px), 1)
                for pal in icon_pals]
        best = min(range(6), key=lambda k: cost[k])
        if slot < 6 and best != slot and cost[slot] - cost[best] > args.icon_margin:
            find("WARN", "icon-pal", sp, f"icon palette {slot} is off its colours by {cost[slot]:.1f}, "
                 f"palette {best} by {cost[best]:.1f} [{png}]")
        return [round(c, 1) for c in cost]

    def check_battle(sp, row, gba=True):
        """Every check on one style's battle art: placement, frames, palettes, female art, icons."""
        img = load_png(row["front"])
        if img is None:
            find("ERROR", "front-missing", sp, f"no PNG for {row['front']}")
            return
        nframes = img.size[1] // FRAME
        f0, w = frame_pixels(img, 0)
        row["frontMeasuredY"], measured = check_y(sp, "front-y", row["front"], 0, row["frontY"])
        if measured is not None and row["frontSize"] != measured:
            find("INFO", "front-size", sp, f"frontPicSize {size_str(row['frontSize'])}, drawing {size_str(measured)}")
        if nframes >= 2 and f0 == frame_pixels(img, 1)[0]:
            find("INFO", "static-front", sp, f"frames 1 and 2 are the same: no idle motion [{row['front']}]")
        bad = sorted({fr for fr, _ in row["frames"] if fr >= nframes})
        if bad:
            find("ERROR", "frame-range", sp, f"the animation shows frame {bad}, the sheet has {nframes} [{row['front']}]")
        specks = strays(f0, w, FRAME)
        if specks:
            find("INFO", "stray", sp, f"{len(specks)} detached speck(s) of 1-2 px at {specks[:4]} [{row['front']}]")

        if row["back"]:
            row["backMeasuredY"], measured = check_y(sp, "back-y", row["back"], 0, row["backY"])
            if measured is not None and row["backSize"] != measured:
                find("INFO", "back-size", sp, f"backPicSize {size_str(row['backSize'])}, drawing {size_str(measured)}")
        for key, check, data_y in (("frontFemale", "front-y", row["frontY"]), ("backFemale", "back-y", row["backY"])):
            if row.get(key):
                check_y(sp + "/female", check, row[key], 0, data_y)
                if gba and "_gba" in (row["front"] or "") and "_gba" not in row[key]:
                    find("WARN", "female-style", sp, f"GBA-style sprite, DS-style female [{row[key]}]")

        normal, shiny = load_pal(row["palette"]), load_pal(row["shiny"])
        if normal and shiny and normal[1:] == shiny[1:]:
            find("ERROR", "shiny-same", sp, f"{row['shiny']} is the same as {row['palette']}")
        if normal and os.path.dirname(row["palette"]) == os.path.dirname(row["front"]) \
                and os.path.basename(row["palette"]).startswith("normal"):  # not a recolour form's palette
            used, pngc = sorted({p for p in f0 if p}), png_colors(img)
            off = [i for i in used if i < min(len(pngc), len(normal)) and color_distance(pngc[i], normal[i]) > 6]
            if off:
                find("INFO", "pal-drift", sp, f"{len(off)} of {len(used)} colours in {row['front']} differ "
                     f"from {row['palette']}")

        if row.get("icon"):
            row["iconCost"] = check_icon(sp, row["icon"], row["iconPal"])
        if row.get("iconFemale"):
            check_icon(sp + "/female", row["iconFemale"], row["iconPalFemale"])

    for idx in range(1, table_size // size):
        raw = rom.read(base + idx * size, size)
        if not field(raw, layout, "frontPic"):
            continue
        sp = species_names.get(idx, f"#{idx}")

        def asset(f):
            return assets.get(by_addr.get(field(raw, layout, f), ""))

        row = {
            "id": idx, "species": sp, "natDex": field(raw, layout, "natDexNum"),
            "front": png_for(asset("frontPic")), "back": png_for(asset("backPic")),
            "palette": pal_for(asset("palette")), "shiny": pal_for(asset("shinyPalette")),
            "shinyModern": pal_for(asset("shinyPaletteModern")),
            "icon": png_for(asset("iconSprite")), "iconPal": field(raw, layout, "iconPalIndex"),
            "frontSize": field(raw, layout, "frontPicSize"), "frontY": field(raw, layout, "frontPicYOffset"),
            "backSize": field(raw, layout, "backPicSize"), "backY": field(raw, layout, "backPicYOffset"),
            "elevation": field(raw, layout, "enemyMonElevation"),
            "abilities": list(struct.unpack_from("<3H", raw, layout["abilities"][0])),
            "frames": anim_frames(rom, field(raw, layout, "frontAnimFrames")),
        }
        for key, f, conv in (("frontFemale", "frontPicFemale", png_for), ("backFemale", "backPicFemale", png_for),
                             ("paletteFemale", "paletteFemale", pal_for), ("shinyFemale", "shinyPaletteFemale", pal_for),
                             ("iconFemale", "iconSpriteFemale", png_for)):
            if f in layout and field(raw, layout, f):
                row[key] = conv(asset(f))
        if row.get("iconFemale"):
            row["iconPalFemale"] = field(raw, layout, "iconPalIndexFemale")
        if "overworldData.images" in layout:
            images = field(raw, layout, "overworldData.images")
            first = rom.u32(images) if images else 0
            row["owSubstitute"] = not first or first == substitute
            row["ow"] = None if row["owSubstitute"] else png_for(assets.get(sheet_at(first) or ""))
            row["owW"] = field(raw, layout, "overworldData.width")
            row["owH"] = field(raw, layout, "overworldData.height")
            row["owPal"] = pal_for(assets.get(by_addr.get(field(raw, layout, "overworldPalette"), "")))
            row["owShiny"] = pal_for(assets.get(by_addr.get(field(raw, layout, "overworldShinyPalette"), "")))
        row["placeholder"] = "question_mark" in (row["front"] or "")
        rows.append(row)

        if row["placeholder"]:
            find("WARN", "placeholder", sp, f"the front sprite is the question mark [{row['front']}]")
            continue
        check_battle(sp, row)

        if "owSubstitute" in row:
            if row["owSubstitute"] or not row["ow"]:
                find("WARN", "ow-missing", sp, "the follower is the substitute doll")
            else:
                op, osh = load_pal(row["owPal"]), load_pal(row["owShiny"])
                if op and osh and op[1:] == osh[1:]:
                    find("WARN", "ow-shiny-same", sp, f"{row['owShiny']} is the same as {row['owPal']}")

        if levitate in row["abilities"] and not row["elevation"]:
            find("INFO", "levitate", sp, "has Levitate and stands on the ground (enemyMonElevation 0)")

    # DS style (the SPRITES option): the same checks on src/data/pokemon/species_gfx_ds.h as built.
    if "sSpeciesGfxDs" in by_name:
        ds_layout, ds_size = struct_layout(tmp, "SpeciesGfxDs", "species_gfx_style.h")
        index_addr, table_addr = by_name["sSpeciesGfxDsIndex"][0], by_name["sSpeciesGfxDs"][0]
        for row in rows:
            k = struct.unpack("<H", rom.read(index_addr + 2 * row["id"], 2))[0]
            if not k:
                continue
            raw = rom.read(table_addr + (k - 1) * ds_size, ds_size)

            def ds_asset(f):
                return assets.get(by_addr.get(field(raw, ds_layout, f), ""))

            ds = {"front": png_for(ds_asset("frontPic")), "back": png_for(ds_asset("backPic")),
                  "palette": pal_for(ds_asset("palette")), "shiny": pal_for(ds_asset("shinyPalette")),
                  "frontSize": field(raw, ds_layout, "frontPicSize"), "frontY": field(raw, ds_layout, "frontPicYOffset"),
                  "backSize": field(raw, ds_layout, "backPicSize"), "backY": field(raw, ds_layout, "backPicYOffset"),
                  "elevation": field(raw, ds_layout, "enemyMonElevation"),
                  "frames": anim_frames(rom, field(raw, ds_layout, "frontAnimFrames")) or row["frames"]}
            for key, f, conv in (("frontFemale", "frontPicFemale", png_for), ("backFemale", "backPicFemale", png_for),
                                 ("paletteFemale", "paletteFemale", pal_for), ("shinyFemale", "shinyPaletteFemale", pal_for)):
                if field(raw, ds_layout, f):
                    ds[key] = conv(ds_asset(f))
            if field(raw, ds_layout, "iconSpriteFemale") and ds_asset("iconSpriteFemale") != row.get("iconFemale"):
                ds["iconFemale"] = png_for(ds_asset("iconSpriteFemale"))
                ds["iconPalFemale"] = field(raw, ds_layout, "iconPalIndexFemale")
            row["ds"] = ds
            check_battle(row["species"] + "/ds", ds, gba=False)

    return rows, findings


def load_known():
    known = {}
    if os.path.exists(KNOWN):
        for line in open(KNOWN):
            if line.strip() and not line.startswith("#"):
                check, sp, reason = line.split(None, 2)
                known[(check, sp)] = reason.strip()
    return known


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", default="pokehns.gba")
    ap.add_argument("--elf", help="default: the ROM's name with .elf")
    ap.add_argument("--json", help="write per-species data here")
    ap.add_argument("--check", action="append", help="only this check (repeatable)")
    ap.add_argument("--level", default="WARN", choices=list(LEVEL), help="lowest level to print")
    ap.add_argument("--icon-margin", type=float, default=2.0,
                    help="icon-pal: how much closer the best palette must be to report")
    ap.add_argument("--strict", action="store_true", help="exit 1 on an ERROR or WARN not in known.txt")
    args = ap.parse_args()
    args.rom = os.path.abspath(args.rom)
    args.elf = os.path.abspath(args.elf or re.sub(r"\.gba$", ".elf", args.rom))
    rows, findings = audit(args)
    if args.json:
        with open(args.json, "w") as f:
            json.dump(rows, f, indent=1)
    known = load_known()
    is_known = lambda x: (x[1], x[2]) in known
    by_check = collections.defaultdict(list)
    for x in findings:
        if LEVEL[x[0]] <= LEVEL[args.level] and (not args.check or x[1] in args.check) and not is_known(x):
            by_check[(LEVEL[x[0]], x[1])].append(x)
    for (_, check), items in sorted(by_check.items()):
        print(f"\n== {check} ({items[0][0]}, {len(items)})")
        for _, _, sp, detail in items:
            print(f"  {sp}: {detail}")
    new = collections.Counter(x[0] for x in findings if not is_known(x))
    print(f"\n{len(rows)} species: {new['ERROR']} ERROR, {new['WARN']} WARN, {new['INFO']} INFO; "
          f"{sum(map(is_known, findings))} known and fine (known.txt)")
    if args.strict and (new["ERROR"] or new["WARN"]):
        sys.exit(1)


if __name__ == "__main__":
    main()
