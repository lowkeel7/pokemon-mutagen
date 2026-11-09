#!/usr/bin/env python3
"""The species parts' art (BACKLOG SG-09), cut from the donors' own sprites. No drawing, ever.

    tools/relics/cut.py                 # writes graphics/relics/<part>.png and graphics/items/icons/<part>.png
    tools/relics/cut.py --palettes OUT  # the donors' 16 colours with their indices, to write the keep lists
    tools/relics/cut.py --preview OUT   # every part's two cells at 4x, and each on a sample wearer
    tools/relics/cut.py --docs          # docs/pokerom/relics.md and its icons

Each part is a box of the donor's first front frame (anim_front_gba.png, or anim_front.png where
only DS art exists) and one of its back sprite, keeping only the palette indices named for it, so
the part comes away from the body. The cut sits bottom-centred in a 32x32 cell: the front view in
the top cell of a 32x64 sheet, the back view in the lower one, index 0 transparent, in the donor's
own palette (the ROM points the part at the donor's palette, so no copy of it is stored). The bag
icon is the front cut in a 24x24 cell, shrunk by whole pixels only when it does not fit.

The sheet feeds src/relic.c (RELIC_CELL, the anchors) and the table in src/data/relics.h; the two
must agree on the cell size. PARTS below is the record of what was taken from where.
"""
import argparse
import os
import re
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GRAPHICS = os.path.join(ROOT, "graphics/pokemon")
OUT_RELICS = os.path.join(ROOT, "graphics/relics")
OUT_ICONS = os.path.join(ROOT, "graphics/items/icons")
CELL = 32
ICON = 24
MIRROR = "mirror"  # the back view is the front cut flipped: a part the camera sees the same from behind

# name: donor folder, front (box, keep indices), back (box, keep) or MIRROR, and how the ROM places it:
# anchor HEAD (on the head line), FACE (over the face), BODY (the middle), BACK (the shoulders, behind
# the Pokémon in the front view); dy nudges in pixels (positive is down). Boxes are x0, y0, x1, y1
# in the 64x64 frame, x1 and y1 exclusive. pair=N puts the cut beside its mirror image, N px apart, overlapping
# when N is negative (one eye or wing makes two). front_from="back" cuts the front view from the back sprite instead
# (Kabutops raises a cleaver only there). drop=[box, ...] blanks those boxes of the frame the front view
# is cut from before the cut (and drop_back the back sprite's): another part of the donor sharing the
# box and the colours, such as an arm over a shell. Recolour: the part's pixels mapped, colour by colour,
# to the nearest luminance in another species' palette (the Charizard skull is Cubone's skull in
# Charizard's colours; still Game Freak's pixels and colours, nothing drawn).
PARTS = {
    "cubone_skull":     dict(donor="cubone",    front=((20, 11, 44, 30), {5, 6, 7, 8, 14, 15}), back=((18, 12, 46, 30), {5, 6, 7, 8, 14, 15}),
                             anchor="HEAD", ability="Rock Head", lends="Ground", name="CUBONE SKULL"),
    "charizard_skull":  dict(donor="cubone",    front=((20, 11, 44, 30), {5, 6, 7, 8, 14, 15}), back=((18, 12, 46, 30), {5, 6, 7, 8, 14, 15}),
                             recolour=("charizard", {6, 7, 8, 9, 10, 11, 12, 13, 14, 15}), anchor="HEAD", ability="Solar Power", lends="Fire", name="CHARIZARD SKULL"),
    "head_shell":       dict(donor="onix",      front=((30, 14, 58, 34), None), back=((32, 8, 60, 26), None),
                             anchor="HEAD", ability="Rock Head", lends="Rock", name="HEAD SHELL"),
    "arbok_venom":      dict(donor="arbok",     front=((32, 26, 56, 44), {4, 5, 6, 7, 8}), back=MIRROR,
                             anchor="FACE", ability="Poison Touch", lends="Poison", name="ARBOK VENOM"),
    "togepi_shell":     dict(donor="togepi",    front=((18, 26, 42, 48), {1, 2, 3, 4, 5, 9, 10, 11, 12, 13}), back=((16, 24, 48, 56), {1, 2, 3, 4, 5, 9, 10, 11, 12, 13}),
                             anchor="BODY", ability="Serene Grace", lends="Fairy", name="TOGEPI SHELL"),
    "pupitar_shell":    dict(donor="pupitar",   front=((16, 8, 48, 28), None), back=((16, 12, 48, 30), None),
                             anchor="HEAD", ability="Shed Skin", lends="Rock", name="PUPITAR SHELL"),
    "lotad_lily":       dict(donor="lotad",     front=((18, 20, 50, 40), {6, 7, 8, 9, 10, 15}), back=((16, 20, 48, 44), {6, 7, 8, 9, 10, 15}),
                             anchor="HEAD", ability="Rain Dish", lends="Water", name="LOTAD LILY"),
    "swellow_tail":     dict(donor="swellow",   front=((34, 8, 60, 40), None), back=MIRROR,
                             anchor="BACK", ability="Guts", lends="Flying", name="SWELLOW TAIL"),
    "kirlia_antenna":   dict(donor="kirlia",    front=((20, 4, 48, 20), {8, 9, 10}), back=((18, 4, 48, 20), {8, 9, 10}),
                             anchor="HEAD", ability="Telepathy", lends="Psychic", name="KIRLIA ANTENNA"),
    "breloom_cap":      dict(donor="breloom",   front=((28, 4, 60, 28), {7, 8, 9, 10, 11, 12, 13, 15}), back=((30, 4, 62, 36), {7, 8, 9, 10, 11, 12, 13, 15}),
                             anchor="HEAD", ability="Effect Spore", lends="Grass", name="BRELOOM CAP"),
    "hariyama_pants":   dict(donor="hariyama",  front=((16, 36, 48, 62), {9, 10, 11, 12, 13}), back=((16, 30, 48, 57), {5, 6, 7, 8, 9, 10}),
                             anchor="BODY", dy=8, ability="Thick Fat", lends="Fighting", name="HARIYAMA PANTS"),
    "sableye_eyes":     dict(donor="sableye",   front=((20, 22, 44, 36), {5, 6, 7, 9, 10}), back=MIRROR,
                             anchor="FACE", ability="Keen Eye", lends="Dark", name="SABLEYE EYES"),
    "roselia_rose":     dict(donor="roselia",   front=((8, 26, 32, 50), {10, 11, 12}), back=((42, 26, 64, 50), {10, 11, 12}),
                             anchor="HEAD", ability="Natural Cure", lends="Grass", name="ROSELIA ROSE"),
    "sharpedo_skin":    dict(donor="sharpedo",  front=((34, 4, 56, 24), {1, 2, 3, 4, 5, 14}), back=((22, 2, 44, 24), {1, 2, 3, 4, 5, 14}),
                             anchor="HEAD", ability="Rough Skin", lends="Water", name="SHARPEDO SKIN"),
    "flygon_eyes":      dict(donor="flygon",    front=((38, 7, 46, 14), {11, 12, 13, 15}), back=MIRROR, pair=6,
                             anchor="FACE", ability="Compound Eyes", lends="Ground", name="FLYGON EYES"),
    "duskull_mask":     dict(donor="duskull",   front=((14, 22, 42, 52), {4, 5, 6, 7, 8, 12}), back=MIRROR,
                             anchor="FACE", ability="Infiltrator", lends="Ghost", name="DUSKULL MASK"),
    "metagross_cross":  dict(donor="metagross", front=((22, 22, 48, 48), {2, 3, 4, 5, 14}), back=MIRROR,
                             anchor="FACE", ability="Clear Body", lends="Steel", name="METAGROSS CROSS"),
    "bastiodon_shield": dict(donor="bastiodon", front=((12, 10, 44, 42), None), back=((14, 10, 46, 42), None),
                             anchor="FACE", ability="Sturdy", lends="Rock", name="BASTIODON SHIELD"),
    "skuntank_oil":     dict(donor="skuntank",  front=((24, 4, 56, 30), {1, 2, 3, 4, 5, 6, 7, 8}), back=((12, 8, 44, 40), {1, 2, 3, 4, 5, 6, 7, 8}),
                             anchor="HEAD", ability="Stench", lends="Poison", name="SKUNTANK OIL"),
    "scyther_wings":    dict(donor="scyther",   front=((41, 3, 61, 21), {7, 8, 9, 10, 12, 13, 14, 15}), back=MIRROR, pair=-8,
                             anchor="BACK", ability="Technician", lends="Bug", name="SCYTHER WINGS"),
    "lapras_shell":     dict(donor="lapras",    front=((10, 10, 42, 40), {6, 7, 8, 9, 10, 15}), back=((8, 32, 40, 64), {6, 7, 8, 9, 10, 15}),
                             anchor="BACK", ability="Shell Armor", lends="Water", name="LAPRAS SHELL"),
    "mareep_wool":      dict(donor="mareep",    front=((18, 18, 50, 50), {1, 2, 3, 4, 5}), back=((16, 20, 48, 52), {1, 2, 3, 4, 5}),
                             anchor="BODY", ability="Static", lends="Electric", name="MAREEP WOOL"),
    "sneasel_feather":  dict(donor="sneasel",   front=((34, 4, 54, 22), {6, 7, 8, 9}), back=((18, 4, 38, 22), {6, 7, 8, 9}),
                             anchor="HEAD", ability="Pickpocket", lends="Dark", name="SNEASEL FEATHER"),
    "magcargo_shell":   dict(donor="magcargo",  front=((28, 10, 60, 42), {9, 10, 11, 12, 13, 14, 15}), back=((26, 18, 58, 50), {9, 10, 11, 12, 13, 14, 15}),
                             anchor="BACK", ability="Flame Body", lends="Fire", name="MAGCARGO SHELL"),
    # The move-family parts (slice 4, 2026-11-09): what each strengthens is the row in src/data/relics.h;
    # `effect` is the docs' wording of it, `poached` marks a part no wild donor drops (the black market's).
    "kabutops_cleavers":  dict(donor="kabutops",   front=((45, 36, 57, 59), {1, 2, 3, 4, 5}), front_from="back", back=MIRROR, pair=8,
                             anchor="BACK", effect="slash moves ×1.2", lends="Rock", name="KABUTOPS CLEAVERS"),
    "pinsir_horns":       dict(donor="pinsir",     front=((15, 4, 30, 28), {1, 2, 3, 4, 5}), back=MIRROR, pair=2,
                             anchor="HEAD", effect="stab moves ×1.2", lends="Bug", name="PINSIR HORNS"),
    "beedrill_stinger":   dict(donor="beedrill",   front=((5, 32, 19, 50), {1, 6, 7, 8, 9}), back=MIRROR, pair=4,
                             anchor="BODY", effect="stab moves ×1.2; a stab that hits poisons one time in ten", lends="Bug", name="BEEDRILL STINGER"),
    "pidgeot_feathers":   dict(donor="pidgeot",    front=((5, 5, 37, 24), {3, 4, 5, 6, 7, 8, 9}), back=MIRROR,
                             anchor="HEAD", effect="wind moves ×1.2", lends="Flying", name="PIDGEOT FEATHERS"),
    "predator_teeth":     dict(donor="feraligatr", front=((5, 16, 27, 29), {1, 11, 12, 13, 14}), back=((42, 29, 60, 40), {1, 11, 12, 13, 14}),
                             anchor="FACE", dy=4, effect="bite moves ×1.2", lends="Water", name="PREDATOR TEETH"),
    "sandslash_claws":    dict(donor="sandslash",  front=((20, 29, 42, 50), {1, 6, 7, 8, 9}), back=((33, 36, 59, 53), {1, 6, 7, 8, 9}),
                             anchor="BODY", dy=6, effect="slash moves ×1.1 and a critical-hit stage", lends="Ground", name="SANDSLASH CLAWS"),
    "drill_horn":         dict(donor="rhydon",     front=((4, 19, 16, 28), {1, 2, 3, 4, 5}), back=((49, 16, 57, 27), {1, 2, 3, 4, 5}),
                             anchor="FACE", effect="stab moves ×1.2", lends="Ground", name="DRILL HORN"),
    "bayleef_leaf_blade": dict(donor="bayleef",    front=((25, 6, 57, 18), {7, 8, 9, 10}), back=((23, 8, 55, 28), {7, 8, 9, 10}),
                             anchor="HEAD", effect="slash moves ×1.2", lends="Grass", name="BAYLEEF LEAF BLADE"),
    "loudred_ears":       dict(donor="loudred",    front=((6, 5, 24, 24), {2, 3, 4, 5, 9, 10, 11, 12, 15}), back=MIRROR, pair=-4,
                             anchor="HEAD", effect="sound moves ×1.2", lends="Normal", name="LOUDRED EARS"),
    "seviper_venom":      dict(donor="seviper",    front=((7, 25, 17, 38), {1, 6, 7, 8}), back=MIRROR,
                             anchor="FACE", dy=4, effect="bite moves ×1.1; a bite that hits poisons one time in ten", lends="Poison", name="SEVIPER VENOM"),
    "absol_blade":        dict(donor="absol",      front=((27, 1, 52, 31), {11, 12, 13, 14, 15}), back=MIRROR,
                             anchor="HEAD", effect="slash moves ×1.1 and a critical-hit stage", lends="Dark", name="ABSOL BLADE"),
    "empoleon_trident":   dict(donor="empoleon",   front=((28, 0, 46, 14), {1, 2, 3, 4, 5}), back=MIRROR,
                             anchor="HEAD", effect="stab moves ×1.2", lends="Water", name="EMPOLEON TRIDENT"),
    "mamoswine_tusk":     dict(donor="mamoswine",  front=((0, 24, 19, 47), {4, 7, 8}), back=MIRROR, pair=-6,
                             anchor="FACE", dy=6, effect="stab moves ×1.2", lends="Ice", poached=True, name="MAMOSWINE TUSK"),
    "octillery_cannon":   dict(donor="octillery",  front=((10, 34, 20, 46), {2, 3, 4, 5, 7, 8, 9, 10, 15}), back=MIRROR,
                             anchor="FACE", dy=4, effect="ballistic moves ×1.2", lends="Water", name="OCTILLERY CANNON"),
    "haxorus_blade":      dict(donor="haxorus",    front=((4, 0, 25, 31), {3, 5}), back=MIRROR,
                             anchor="FACE", dy=2, effect="slash moves ×1.2", lends="Dragon", name="HAXORUS BLADE"),
    "tinkaton_hammer":    dict(donor="tinkaton",   front=((2, 7, 64, 61), {6, 7, 8, 9, 10, 15}), front_from="back", back=MIRROR,
                             anchor="BACK", effect="blunt moves ×1.2", lends="Fairy", name="TINKATON HAMMER"),
    "boxing_gloves":      dict(donor="hitmonchan", front=((36, 20, 50, 32), {6, 7, 8, 9}), back=MIRROR, pair=4,
                             anchor="BODY", dy=4, effect="punch moves ×1.1", lends="Fighting", name="BOXING GLOVES"),
    # The stat parts (slice 5, 2026-11-09): a stat raised for a wearer of the part's type (Shuckle's for any);
    # the row is in src/data/relics.h, `effect` the docs' wording of it.
    "sceptile_tail":      dict(donor="sceptile",   front=((45, 31, 64, 63), None), front_from="back", back=MIRROR,
                             anchor="BACK", effect="Speed ×1.2 for a Grass-type wearer", lends="Grass", name="SCEPTILE TAIL"),
    "bulbasaur_bulb":     dict(donor="bulbasaur",  front=((18, 13, 44, 28), {10, 11, 12, 13, 14}), back=((10, 16, 42, 48), {11, 12, 13, 14}),
                             anchor="BACK", dy=-4, effect="Sp. Def ×1.2 for a Grass-type wearer", lends="Grass", name="BULBASAUR BULB"),
    "heracross_shell":    dict(donor="heracross",  front=((9, 36, 41, 53), {2, 3, 4, 5, 15}), front_from="back", drop=[(39, 34, 46, 39)], back=MIRROR,
                             anchor="BACK", effect="Defense ×1.2 for a Bug-type wearer", lends="Bug", name="HERACROSS SHELL"),
    "shiftry_bark":       dict(donor="shiftry",    front=((24, 35, 48, 50), {1, 4, 5, 6, 7}), back=((28, 36, 46, 51), {1, 4, 5, 15}),
                             anchor="BODY", effect="Defense ×1.2 for a Grass-type wearer", lends="Grass", name="SHIFTRY BARK"),
    "spoink_pearl":       dict(donor="spoink",     front=((26, 7, 42, 22), {5, 6, 7, 8, 9, 13}), back=((16, 11, 41, 33), {5, 6, 7, 8, 9, 13}),
                             anchor="HEAD", effect="Sp. Atk ×1.2 for a Psychic-type wearer", lends="Psychic", name="SPOINK PEARL"),
    "shinx_star":         dict(donor="shinx",      front=((42, 28, 55, 39), {4, 6, 7}), back=MIRROR,
                             anchor="HEAD", effect="Speed ×1.2 for an Electric-type wearer", lends="Electric", name="SHINX STAR"),
    "shuckle_shell":      dict(donor="shuckle",    front=((18, 27, 50, 49), {8, 9, 11, 12, 13, 14, 15}), back=MIRROR,
                             anchor="BODY", effect="Defense and Sp. Def ×1.1 for any wearer", lends="Bug", name="SHUCKLE SHELL"),
}


def donor_files(donor):
    d = os.path.join(GRAPHICS, donor)
    front = os.path.join(d, "anim_front_gba.png")
    if not os.path.exists(front):
        front = os.path.join(d, "anim_front.png")
    if not os.path.exists(front):
        front = os.path.join(d, "front.png")  # a species with a still front sprite only
    back = os.path.join(d, "back_gba.png")
    if not os.path.exists(back):
        back = os.path.join(d, "back.png")
    pal = os.path.join(d, "normal_gba.pal")
    if not os.path.exists(pal):
        pal = os.path.join(d, "normal.pal")
    return front, back, pal


def read_pal(path):
    with open(path) as f:
        lines = [l.strip() for l in f]
    assert lines[0] == "JASC-PAL", path
    n = int(lines[2])
    return [tuple(int(v) for v in lines[3 + i].split()) for i in range(n)]


def frame(path, index=0):
    """The 64x64 frame `index` of an indexed sprite PNG, as a list of rows of palette indices."""
    im = Image.open(path)
    assert im.mode == "P", path
    w, h = im.size
    assert w == 64 and h % 64 == 0, (path, im.size)
    px = im.load()
    y0 = 64 * index
    return [[px[x, y0 + y] for x in range(64)] for y in range(64)]


def blank(rows, boxes):
    """A copy of the frame with these boxes (x0, y0, x1, y1 in the frame) emptied: another part of the
    donor that shares the cut's box and colours, such as an arm resting on a shell."""
    rows = [list(r) for r in rows]
    for x0, y0, x1, y1 in boxes:
        for y in range(y0, y1):
            for x in range(x0, x1):
                rows[y][x] = 0
    return rows


def cut(rows, box, keep):
    x0, y0, x1, y1 = box
    out = []
    for y in range(y0, y1):
        out.append([(v if (keep is None or v in keep) else 0) for v in rows[y][x0:x1]])
    return trim(out)


def trim(rows):
    """Drop blank rows and columns around the drawn pixels."""
    ys = [y for y, r in enumerate(rows) if any(r)]
    if not ys:
        return [[0]]
    rows = rows[ys[0]:ys[-1] + 1]
    xs = [x for x in range(len(rows[0])) if any(r[x] for r in rows)]
    return [r[xs[0]:xs[-1] + 1] for r in rows]


def mirror(rows):
    return [list(reversed(r)) for r in rows]


def pair(rows, gap):
    """The cut and its mirror image side by side, `gap` pixels apart (overlapping at the middle when
    negative, the left one on top): one eye or one wing makes two."""
    w = len(rows[0])
    out = []
    for r in rows:
        left, right = r, list(reversed(r))
        row = [0] * (2 * w + gap)
        for x in range(w):
            if right[x]:
                row[w + gap + x] = right[x]
        for x in range(w):
            if left[x]:
                row[x] = left[x]
        out.append(row)
    return out


def place(rows, w, h, bottom=True):
    """Bottom-centred (or centred) in a w x h cell, cropped to it if larger."""
    ph, pw = len(rows), len(rows[0])
    if pw > w or ph > h:
        rows = shrink(rows, w, h)
        ph, pw = len(rows), len(rows[0])
    cell = [[0] * w for _ in range(h)]
    ox = (w - pw) // 2
    oy = (h - ph) if bottom else (h - ph) // 2
    for y in range(ph):
        cell[oy + y][ox:ox + pw] = rows[y]
    return cell


def shrink(rows, w, h):
    """Whole-pixel subsampling to fit: the only resize ever done, and only for the bag icon."""
    ph, pw = len(rows), len(rows[0])
    step = 1
    while pw / step > w or ph / step > h:
        step += 1
    return [[rows[y][x] for x in range(0, pw, step)] for y in range(0, ph, step)]


def luminance(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def recolour_map(src_pal, dst_pal, allowed):
    """Index i of src_pal -> the index of dst_pal among `allowed` whose colour has the nearest luminance."""
    m = {0: 0}
    for i in range(1, 16):
        li = luminance(src_pal[i])
        m[i] = min(allowed, key=lambda j: abs(luminance(dst_pal[j]) - li))
    return m


def write_indexed(path, cell, pal):
    im = Image.new("P", (len(cell[0]), len(cell)))
    flat = []
    for c in pal:
        flat.extend(c)
    im.putpalette(flat + [0] * (768 - len(flat)))
    im.putdata([v for r in cell for v in r])
    im.save(path, optimize=True)


def build(part, spec):
    front_path, back_path, pal_path = donor_files(spec["donor"])
    pal = read_pal(pal_path)
    # front_from="back": the front view is cut from the back sprite, where the donor shows the part better
    front = cut(blank(frame(back_path if spec.get("front_from") == "back" else front_path), spec.get("drop", ())), *spec["front"])
    if "pair" in spec:
        front = pair(front, spec["pair"])
    back = mirror(front) if spec["back"] == MIRROR else cut(blank(frame(back_path), spec.get("drop_back", ())), *spec["back"])
    if "recolour" in spec:
        species, allowed = spec["recolour"]
        _, _, other = donor_files(species)
        other_pal = read_pal(other)
        m = recolour_map(pal, other_pal, allowed)
        front = [[m[v] for v in r] for r in front]
        back = [[m[v] for v in r] for r in back]
        pal = other_pal
    bottom = spec["anchor"] == "HEAD"
    sheet = place(front, CELL, CELL, bottom) + place(back, CELL, CELL, bottom)
    icon = place(front, ICON, ICON, bottom=False)
    return sheet, icon, pal, (len(front[0]), len(front)), (len(back[0]), len(back))


def write_all():
    os.makedirs(OUT_RELICS, exist_ok=True)
    for part, spec in PARTS.items():
        sheet, icon, pal, fsize, bsize = build(part, spec)
        write_indexed(os.path.join(OUT_RELICS, part + ".png"), sheet, pal)
        write_indexed(os.path.join(OUT_ICONS, part + ".png"), icon, pal)
        print(f"{part:18s} front {fsize[0]}x{fsize[1]}  back {bsize[0]}x{bsize[1]}  anchor {spec['anchor']}")


def palettes_sheet(out):
    donors = sorted({(s["donor"]) for s in PARTS.values()} | {s.get("recolour") for s in PARTS.values() if "recolour" in s})
    im = Image.new("RGB", (16 * 36 + 120, len(donors) * 40 + 10), (24, 24, 24))
    dr = ImageDraw.Draw(im)
    for r, donor in enumerate(donors):
        pal = read_pal(donor_files(donor)[2])
        y = 10 + r * 40
        dr.text((4, y + 10), donor, fill=(230, 230, 230))
        for i, c in enumerate(pal):
            x = 110 + i * 36
            dr.rectangle([x, y, x + 32, y + 22], fill=c, outline=(90, 90, 90))
            dr.text((x + 10, y + 24), str(i), fill=(230, 230, 230))
    im.save(out)


def preview(out, wearer="treecko", only=None):
    """Every part's two cells at 4x beside the cut's source, and placed on a sample wearer by the
    same head-line rule as src/relic.c (FindAnchor), so the anchors can be judged."""
    S = 4
    parts = [(k, v) for k, v in PARTS.items() if not only or k in only]
    im = Image.new("RGB", (4 * (CELL * S + 8) + 2 * (64 * S + 8) + 24, len(parts) * (64 * S + 20) + 10), (24, 24, 24))
    dr = ImageDraw.Draw(im)
    wf, wb, wp = donor_files(wearer)
    wpal = read_pal(wp)
    wfront, wback = frame(wf), frame(wb)
    for r, (part, spec) in enumerate(parts):
        sheet, icon, pal, _, _ = build(part, spec)
        y = 10 + r * (64 * S + 20)
        x = 8
        for cell in (sheet[:CELL], sheet[CELL:]):
            im.paste(render(cell, pal, S, (60, 60, 60)), (x, y))
            x += CELL * S + 8
        im.paste(render(icon, pal, S, (60, 60, 60)), (x, y))
        x += CELL * S + 8
        for view, (wrows, cell) in enumerate(((wfront, sheet[:CELL]), (wback, sheet[CELL:]))):
            scene = render(wrows, wpal, S, (40, 40, 40))
            ax, ay = anchor_point(wrows, spec["anchor"], spec.get("dy", 0), back=(view == 1))
            overlay = render(cell, pal, S, None)
            scene.paste(overlay, ((ax - CELL // 2) * S, (ay - CELL) * S), overlay)
            im.paste(scene, (x, y))
            x += 64 * S + 8
        dr.text((8, y + 64 * S + 4), f"{part}: {spec['name']} ({spec['donor']}, {spec['anchor']})", fill=(255, 255, 160))
    im.save(out)


def render(rows, pal, scale, bg):
    h, w = len(rows), len(rows[0])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0) if bg is None else bg + (255,))
    px = im.load()
    for y in range(h):
        for x in range(w):
            v = rows[y][x]
            if v:
                px[x, y] = pal[v] + (255,)
    return im.resize((w * scale, h * scale), Image.NEAREST)


def anchor_point(rows, anchor, dy, back=False):
    """The cell's bottom-centre for a view of the wearer, as src/relic.c computes it: the head line
    is the first row whose drawn width is 7/20 of the sprite's (at least 6 px); the cell's bottom
    sits RELIC_SINK (6) below it for HEAD; FACE centres the cell 10 px under the head line, BODY on
    the drawn box's middle, BACK 4 px under the head line facing us (the part rises over the
    shoulders, behind the body) and 14 px facing away (on the back itself)."""
    counts = [sum(1 for v in r if v) for r in rows]
    xs = [x for x in range(64) if any(r[x] for r in rows)]
    ys = [y for y, c in enumerate(counts) if c]
    if not xs:
        return 32, 32
    threshold = max(6, (xs[-1] - xs[0] + 1) * 7 // 20)
    head = next((y for y in ys if counts[y] >= threshold), ys[0])
    row = rows[head]
    first = next(x for x in range(64) if row[x])
    last = max(x for x in range(64) if row[x])
    cx = (first + last) // 2
    if anchor == "HEAD":
        by = head + 6
    elif anchor == "FACE":
        by = head + 10 + CELL // 2
    elif anchor == "BACK":
        by = head + (14 if back else 4) + CELL // 2
    else:  # BODY
        cx = (xs[0] + xs[-1]) // 2
        by = (ys[0] + ys[-1]) // 2 + CELL // 2
    return cx, by + dy


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--palettes", metavar="OUT", help="write the donors' palettes with indices")
    ap.add_argument("--preview", metavar="OUT", help="write a preview of every part, alone and worn")
    ap.add_argument("--wearer", default="treecko", help="the sample wearer for --preview")
    ap.add_argument("--only", nargs="*", help="preview these parts only")
    ap.add_argument("--docs", action="store_true", help="write docs/pokerom/relics.md")
    args = ap.parse_args()
    if args.palettes:
        palettes_sheet(args.palettes)
    elif args.preview:
        preview(args.preview, args.wearer, args.only)
    elif args.docs:
        import relics_docs  # noqa: F401
        relics_docs.write(PARTS, build)
    else:
        write_all()


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
