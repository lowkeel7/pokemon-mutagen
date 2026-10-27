#!/usr/bin/env python3
"""Generate src/data/pokemon/species_gfx_ds.h, the DS-style art behind the SPRITES option (SG-23).

The game builds with P_GBA_STYLE_SPECIES_GFX TRUE (HnS's look). This compares that build with a
DS-style build of the same tree and writes, for every species whose art differs, the DS build's
pictures, palettes, coordinates and animation, so both styles ship in one ROM.

    tools/spritecheck/gen_ds_style.py --ds-rom /tmp/ds.gba            # GBA build: pokehns.gba
    tools/spritecheck/gen_ds_style.py --ds-rom /tmp/ds.gba --check    # exit 1 if the header is stale

Make the DS build first: set P_GBA_STYLE_SPECIES_GFX to FALSE in include/config/pokemon.h,
`make hns`, copy pokehns.gba and .elf aside, set it back and `make hns` again. Rerun after any
change to Pokémon graphics or their coordinates (the RHH upgrade, new species).
Needs arm-none-eabi-{gcc,cpp,nm,gdb} on PATH.
"""
import argparse
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spritecheck import ROOT, Rom, constants, field, run, struct_layout, symbols, tool, CPPFLAGS  # noqa: E402

OUT = os.path.join(ROOT, "src", "data", "pokemon", "species_gfx_ds.h")
GFX = ["frontPic", "backPic", "palette", "shinyPalette",
       "frontPicFemale", "backPicFemale", "paletteFemale", "shinyPaletteFemale", "iconSpriteFemale"]
NUMS = ["frontPicSize", "frontPicYOffset", "backPicSize", "backPicYOffset", "frontPicSizeFemale",
        "backPicSizeFemale", "enemyMonElevation", "frontAnimId", "backAnimId", "frontAnimDelay",
        "iconPalIndexFemale"]
INCBIN = re.compile(r"\b(\w+)\[\]\s*=\s*(INCBIN_\w+)\(\"([^\"]+)\"\)")


def incbins(tmp, ds):
    """Symbol -> (macro, path) for every INCBIN of src/pokemon.c, in GBA or DS style."""
    wrapper = os.path.join(tmp, f"pokemon_{'ds' if ds else 'gba'}.c")
    with open(wrapper, "w") as f:
        f.write('#include "global.h"\n')
        if ds:
            f.write("#undef P_GBA_STYLE_SPECIES_GFX\n#define P_GBA_STYLE_SPECIES_GFX FALSE\n")
        f.write(f'#include "{os.path.join(ROOT, "src", "pokemon.c")}"\n')
    text = run([tool("cpp")] + CPPFLAGS + [wrapper])
    return {m[1]: (m[2], m[3]) for m in INCBIN.finditer(text)}


def anim_cmds(rom, table):
    """The species' front animation (entry 1 of ANIM_FRAMES) as raw command words, END included."""
    words, cmd = [], rom.u32(table + 4) if table else 0
    while cmd and len(words) < 64:
        word = rom.u32(cmd)
        words.append(word)
        if word & 0xFFFF in (0xFFFF, 0xFFFE, 0xFFFD):  # END, JUMP, LOOP end the list
            break
        cmd += 4
    return words


def anim_c(words):
    out = []
    for w in words:
        kind = w & 0xFFFF
        if kind == 0xFFFF:
            out.append("ANIMCMD_END")
        elif kind == 0xFFFE:
            out.append(f"ANIMCMD_JUMP({(w >> 16) & 0x3F})")
        elif kind == 0xFFFD:
            out.append(f"ANIMCMD_LOOP({(w >> 16) & 0x3F})")
        else:
            flips = (", .hFlip = TRUE" if w >> 22 & 1 else "") + (", .vFlip = TRUE" if w >> 23 & 1 else "")
            out.append(f"ANIMCMD_FRAME({kind}, {(w >> 16) & 0x3F}{flips})")
    return ("(const union AnimCmd *const[]) { sAnim_GeneralFrame0, (const union AnimCmd[]) { "
            + ", ".join(out) + " } }")


def generate(args):
    tmp = tempfile.mkdtemp(prefix="gen-ds-")
    layout, size = struct_layout(tmp)
    names = constants(tmp, "include/constants/species.h", "SPECIES_")
    gba_elf = args.gba_elf or re.sub(r"\.gba$", ".elf", args.gba_rom)
    ds_elf = args.ds_elf or re.sub(r"\.gba$", ".elf", args.ds_rom)
    (g_addr, g_name), (d_addr, d_name) = symbols(gba_elf), symbols(ds_elf)
    g_bin, d_bin = incbins(tmp, False), incbins(tmp, True)
    by_path = {path: sym for sym, (_, path) in g_bin.items()}  # symbols the GBA build already has
    g_rom, d_rom = Rom(args.gba_rom), Rom(args.ds_rom)
    g_base, table = g_name["gSpeciesInfo"]
    d_base, _ = d_name["gSpeciesInfo"]
    new_syms, externs, entries = {}, set(), []

    def path_of(ptr, addr_map, bins):
        sym = addr_map.get(ptr)
        return bins.get(sym, (None, None))[1] if sym else None

    def symbol_for(ptr):
        """A GBA-build symbol for a DS-build pointer, adding an INCBIN when the GBA build has none."""
        sym = d_addr.get(ptr)
        macro, path = d_bin[sym]
        if path in by_path:
            externs.add((by_path[path], macro))
            return by_path[path]
        new = re.sub(r"^gMon(\w+?)_", r"gMon\1Ds_", sym)
        new_syms[new] = (macro, path)
        return new

    for idx in range(1, table // size):
        g_raw, d_raw = g_rom.read(g_base + idx * size, size), d_rom.read(d_base + idx * size, size)
        if not field(g_raw, layout, "frontPic"):
            continue
        g_gfx = [path_of(field(g_raw, layout, f), g_addr, g_bin) for f in GFX]
        d_gfx = [path_of(field(d_raw, layout, f), d_addr, d_bin) for f in GFX]
        g_num = [field(g_raw, layout, f) for f in NUMS]
        d_num = [field(d_raw, layout, f) for f in NUMS]
        g_anim = anim_cmds(g_rom, field(g_raw, layout, "frontAnimFrames"))
        d_anim = anim_cmds(d_rom, field(d_raw, layout, "frontAnimFrames"))
        if g_gfx == d_gfx and g_num == d_num and g_anim == d_anim:
            continue
        e = {"species": names[idx]}
        for f in GFX:
            ptr = field(d_raw, layout, f)
            e[f] = symbol_for(ptr) if ptr else "NULL"
        for f, v in zip(NUMS, d_num):
            e[f] = v
        e["frontAnimFrames"] = anim_c(d_anim) if d_anim != g_anim else "NULL"
        entries.append(e)
    return render(entries, new_syms, externs)


def render(entries, new_syms, externs):
    types = {"INCBIN_U32": "u32", "INCBIN_U16": "u16", "INCBIN_U8": "u8"}
    lines = ["// Generated by tools/spritecheck/gen_ds_style.py from a DS-style build. Don't edit by hand:",
             "// rerun it after any change to Pokémon graphics or their coordinates.",
             "// The DS-style art of every species whose art differs from the GBA-style build (SG-23).",
             "", "#if P_GBA_STYLE_SPECIES_GFX", ""]
    for sym, macro in sorted(externs):
        lines.append(f"extern const {types[macro]} {sym}[];")
    lines.append("")
    for sym, (macro, path) in sorted(new_syms.items()):
        lines.append(f'static const {types[macro]} {sym}[] = {macro}("{path}");')
    lines += ["", "static const struct SpeciesGfxDs sSpeciesGfxDs[] =", "{"]
    for e in entries:
        body = [f"        .{f} = {e[f]}," for f in GFX if e[f] != "NULL"]
        body += [f"        .{f} = {e[f]}," for f in NUMS if e[f]]
        if e["frontAnimFrames"] != "NULL":
            body.append(f"        .frontAnimFrames = {e['frontAnimFrames']},")
        lines += ["    {", f"        // {e['species']}"] + body + ["    },"]
    lines += ["};", "", "// 1 + the row of each species in sSpeciesGfxDs; 0 = the same art in both styles.",
              "static const u16 sSpeciesGfxDsIndex[NUM_SPECIES] =", "{"]
    lines += [f"    [{e['species']}] = {i + 1}," for i, e in enumerate(entries)]
    lines += ["};", "", "#endif // P_GBA_STYLE_SPECIES_GFX", ""]
    return "\n".join(lines), len(entries), len(new_syms)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gba-rom", default="pokehns.gba")
    ap.add_argument("--gba-elf")
    ap.add_argument("--ds-rom", required=True)
    ap.add_argument("--ds-elf")
    ap.add_argument("--check", action="store_true", help="exit 1 if the header differs from what would be written")
    args = ap.parse_args()
    args.gba_rom, args.ds_rom = os.path.abspath(args.gba_rom), os.path.abspath(args.ds_rom)
    text, n, new = generate(args)
    if args.check:
        same = os.path.exists(OUT) and open(OUT).read() == text
        print(f"{os.path.relpath(OUT, ROOT)}: {'up to date' if same else 'STALE, rerun without --check'}")
        sys.exit(0 if same else 1)
    with open(OUT, "w") as f:
        f.write(text)
    print(f"{os.path.relpath(OUT, ROOT)}: {n} species, {new} new pictures and palettes")


if __name__ == "__main__":
    main()
