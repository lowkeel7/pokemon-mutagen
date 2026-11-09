#!/usr/bin/env python3
"""The SPRITES option's two art styles (BACKLOG SG-23) as a docs page with sprite sheets.

    tools/site/sprites.py        # writes docs/pokerom/sprite-styles.md and docs/pokerom/sheets/*.png

FEATURES → SPRITES is GBA (zero, Heart & Soul's look) or DS. For every species whose folder under
graphics/pokemon holds both the Emerald-era front (*_gba.png) and the DS-era one, the page shows the
two first frames side by side, the shiny palettes and the DS female forms on toggles, and the icon
in both styles. Cells come from sprite sheets (16 a row, one sheet per kind) coloured from the .pal
files the ROM is built from, as tools/spritecheck/sheet.py does. Styled by docs/pokerom/brand/mutagen.css (.styles).
"""
import os
import re
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evolutions  # noqa: E402  (species_blocks, pretty, the paths)

ROOT = evolutions.ROOT
GRAPHICS = evolutions.GRAPHICS
SPECIES_INFO = evolutions.SPECIES_INFO
OUT_MD = os.path.join(ROOT, "docs/pokerom/sprite-styles.md")
OUT_SHEETS = os.path.join(ROOT, "docs/pokerom/sheets")
COLUMNS = 16
FRAME, ICON = 64, 32
SHEETS = ["front-gba", "front-ds", "front-gba-shiny", "front-ds-shiny", "front-ds-female", "front-ds-female-shiny",
          "icon-gba", "icon-ds"]


def dex_numbers():
    """NATIONAL_DEX_X -> number, from the enum's order."""
    numbers, n = {}, 0
    with open(os.path.join(ROOT, "include/constants/pokedex.h")) as f:
        for line in f:
            m = re.match(r"\s*NATIONAL_DEX_(\w+),", line)
            if m:
                numbers[m.group(1)] = n
                n += 1
    return numbers


def species_by_gen():
    """[(gen, SPECIES constant)] in the files' order (national dex order within a generation)."""
    out = []
    for gen in range(1, 10):
        path = os.path.join(SPECIES_INFO, f"gen_{gen}_families.h")
        with open(path) as f:
            for m in re.finditer(r"^\s*\[SPECIES_(\w+)\]\s*=", f.read(), re.M):
                out.append((gen, m.group(1)))
    return out


def folder(species):
    """graphics/pokemon/<species>, <base>/<form>, or <base> for a _NORMAL base form (Castform, Deoxys)."""
    name = species.lower()
    parts = name.split("_")
    candidates = [os.path.join(GRAPHICS, name)]
    if len(parts) > 1:
        candidates.append(os.path.join(GRAPHICS, "_".join(parts[:-1]), parts[-1]))
        if parts[-1] == "normal":
            candidates.append(os.path.join(GRAPHICS, "_".join(parts[:-1])))
    for candidate in candidates:
        if os.path.isdir(candidate) and (os.path.exists(os.path.join(candidate, "anim_front_gba.png")) or os.path.exists(os.path.join(candidate, "front_gba.png"))):
            return candidate
    return None


def first(path, size):
    """The first frame of a sprite sheet PNG as an indexed image, or None."""
    if not os.path.exists(path):
        return None
    image = Image.open(path)
    return image.crop((0, 0, size, min(image.height, size)))


def palette(path):
    if not os.path.exists(path):
        return None
    lines = open(path).read().split("\n")
    return [tuple(int(x) for x in lines[3 + i].split()[:3]) for i in range(int(lines[2]))]


def coloured(frame, pal):
    """An indexed frame with the given palette (or its own), index 0 transparent -> RGBA."""
    if frame is None:
        return None
    frame = frame.copy()
    if frame.mode != "P":
        return frame.convert("RGBA")
    if pal:
        flat = []
        for colour in pal[:16]:
            flat.extend(colour)
        flat.extend([0, 0, 0] * (256 - len(pal[:16])))
        frame.putpalette(flat)
    rgba = frame.convert("RGBA")
    rgba.putalpha(frame.point(lambda i: 0 if i == 0 else 255, "L"))
    return rgba


def pick(folder_path, *names):
    for name in names:
        path = os.path.join(folder_path, name)
        if os.path.exists(path):
            return path
    return None


def cells_for(folder_path):
    """kind -> RGBA cell (or None) for one species."""
    gba = pick(folder_path, "anim_front_gba.png", "front_gba.png")
    ds = pick(folder_path, "anim_front.png", "front.png")
    female = pick(folder_path, "anim_frontf.png", "frontf.png")
    normal_gba = palette(os.path.join(folder_path, "normal_gba.pal")) or palette(os.path.join(folder_path, "normal.pal"))
    shiny_gba = palette(os.path.join(folder_path, "shiny_gba.pal")) or palette(os.path.join(folder_path, "shiny.pal"))
    normal = palette(os.path.join(folder_path, "normal.pal"))
    shiny = palette(os.path.join(folder_path, "shiny.pal"))
    normal_f = palette(os.path.join(folder_path, "normalf.pal")) or normal
    shiny_f = palette(os.path.join(folder_path, "shinyf.pal")) or shiny
    return {
        "front-gba": coloured(first(gba, FRAME), normal_gba),
        "front-ds": coloured(first(ds, FRAME), normal),
        "front-gba-shiny": coloured(first(gba, FRAME), shiny_gba),
        "front-ds-shiny": coloured(first(ds, FRAME), shiny),
        "front-ds-female": coloured(first(female, FRAME), normal_f) if female else None,
        "front-ds-female-shiny": coloured(first(female, FRAME), shiny_f) if female else None,
        "icon-gba": coloured(first(pick(folder_path, "icon_gba.png") or "", ICON), None),
        "icon-ds": coloured(first(pick(folder_path, "icon.png") or "", ICON), None),
    }


def main():
    numbers = dex_numbers()
    blocks = evolutions.species_blocks()
    rows = []   # (gen, species, name, dex, has_female)
    cells = {kind: [] for kind in SHEETS}
    for gen, species in species_by_gen():
        if species in ("NONE", "EGG") or species.startswith("QUESTION"):
            continue
        folder_path = folder(species)
        if not folder_path:
            continue
        block = blocks.get(species, "")
        m = re.search(r"\.natDexNum\s*=\s*NATIONAL_DEX_(\w+)", block)
        dex = numbers.get(m.group(1), 0) if m else 0
        species_cells = cells_for(folder_path)
        if species_cells["front-gba"] is None or species_cells["front-ds"] is None:
            continue
        rows.append((gen, species, evolutions.pretty("SPECIES_" + species), dex, species_cells["front-ds-female"] is not None))
        for kind in SHEETS:
            cells[kind].append(species_cells[kind])

    os.makedirs(OUT_SHEETS, exist_ok=True)
    count = len(rows)
    sheet_rows = (count + COLUMNS - 1) // COLUMNS
    for kind in SHEETS:
        size = ICON if kind.startswith("icon") else FRAME
        sheet = Image.new("RGBA", (COLUMNS * size, sheet_rows * size), (0, 0, 0, 0))
        for i, cell in enumerate(cells[kind]):
            if cell is not None:
                sheet.alpha_composite(cell, ((i % COLUMNS) * size, (i // COLUMNS) * size))
        sheet.save(os.path.join(OUT_SHEETS, kind + ".png"), optimize=True)

    females = sum(1 for r in rows if r[4])
    lines = ["# Sprite styles", "",
             "Heart & Soul draws the Gen 1 to 3 Pokémon with their Game Boy Advance art. The option FEATURES →",
             "SPRITES (GBA, the default, or DS) swaps in the DS-era art for every species that has both, with",
             "the DS shadows under wild Pokémon and the female forms the DS games drew. This page puts the two",
             f"styles side by side for all {count} of them; the shiny colours and the {females} female forms are",
             "a toggle away, and the party icons follow the option too. Generated from the game's own art by",
             "`tools/site/sprites.py`.", "",
             '<div class="styles icons" id="styles">',
             '<p class="controls"><label><input type="checkbox" id="st-shiny"> Shiny</label>'
             f'<label><input type="checkbox" id="st-female"> Female forms ({females})</label>'
             '<label><input type="checkbox" id="st-icons" checked> Party icons</label></p>']
    current_gen = None
    index = 0
    for gen, species, name, dex, has_female in rows:
        if gen != current_gen:
            if current_gen is not None:
                lines.append("</div>")
            current_gen = gen
            gen_count = sum(1 for r in rows if r[0] == gen)
            lines.append(f'<h2 id="generation-{gen}">Generation {gen} <small>{gen_count} species</small></h2>')
            lines.append('<div class="grid">')
        x, y = index % COLUMNS, index // COLUMNS
        pos = f"--x:{x};--y:{y}"
        number = f"#{dex:03d}" if dex else ""
        female_cell = f'<figure class="f"><div class="sp dsf" style="{pos}"></div><figcaption>DS ♀</figcaption></figure>' if has_female else ""
        lines.append(f'<div class="card"{" data-f=1" if has_female else ""}><div class="name">{name} <small>{number}</small></div>'
                     f'<div class="cells"><figure><div class="sp gba" style="{pos}"></div><figcaption>GBA</figcaption></figure>'
                     f'<figure><div class="sp ds" style="{pos}"></div><figcaption>DS</figcaption></figure>{female_cell}</div>'
                     f'<div class="icons"><span class="ic gba" style="{pos}"></span><span class="ic ds" style="{pos}"></span></div></div>')
        index += 1
    lines += ["</div>", "</div>", "",
              "<script>(function(){var root=document.getElementById('styles');['shiny','female','icons'].forEach(function(k){"
              "var box=document.getElementById('st-'+k);function apply(){root.classList.toggle(k,box.checked)}"
              "box.addEventListener('change',apply);apply()})})();</script>", ""]
    with open(OUT_MD, "w") as f:
        f.write("\n".join(lines))
    total = sum(os.path.getsize(os.path.join(OUT_SHEETS, k + ".png")) for k in SHEETS)
    print(f"sprites: {count} species ({females} with female forms) -> {os.path.relpath(OUT_MD, ROOT)}, "
          f"{len(SHEETS)} sheets in {os.path.relpath(OUT_SHEETS, ROOT)} ({total / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
