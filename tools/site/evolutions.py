#!/usr/bin/env python3
"""The Mutagen evolution tree (BACKLOG SG-24) as a docs page with sprite thumbnails.

    tools/site/evolutions.py        # writes docs/pokerom/evolutions.md and docs/pokerom/sprites/*.png

Reads the species data (src/data/pokemon/species_info/*.h): every species with an evolution that
needs the Mutagen (IF_MUTAGEN, IF_MUTAGEN_ANCIENT, IF_MUTAGEN_FUTURE), its other evolutions, what
evolves into it, and the first frame of each one's front sprite (graphics/pokemon/<species>/
anim_front.png), so the page shows each family as a tree: the Pokémon it comes from, the Pokémon
itself, and its two lines, the usual one and the Mutagen's.
"""
import glob
import os
import re
import sys

from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "brand"))
import brand  # noqa: E402  (tools/brand/brand.py: the fork mark)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPECIES_INFO = os.path.join(ROOT, "src/data/pokemon/species_info")
GRAPHICS = os.path.join(ROOT, "graphics/pokemon")
OUT_MD = os.path.join(ROOT, "docs/pokerom/evolutions.md")
OUT_SPRITES = os.path.join(ROOT, "docs/pokerom/sprites")
MARK = brand.mark_svg("currentColor", brand.C["strain"]).strip()   # styled by docs/pokerom/brand/mutagen.css (.evo)
MUTAGEN_CONDITIONS = {"IF_MUTAGEN": "Mutagen", "IF_MUTAGEN_ANCIENT": "Mutagen, even strain",
                      "IF_MUTAGEN_FUTURE": "Mutagen, odd strain"}
NAMES = {"MR_RIME": "Mr. Rime", "MR_MIME": "Mr. Mime", "MIME_JR": "Mime Jr.", "SIRFETCHD": "Sirfetch'd",
         "FARFETCHD": "Farfetch'd", "HO_OH": "Ho-Oh", "PORYGON_Z": "Porygon-Z", "TYPE_NULL": "Type: Null",
         "JANGMO_O": "Jangmo-o", "HAKAMO_O": "Hakamo-o", "KOMMO_O": "Kommo-o", "TAPU_KOKO": "Tapu Koko",
         "NIDORAN_F": "Nidoran♀", "NIDORAN_M": "Nidoran♂", "FLABEBE": "Flabébé", "WO_CHIEN": "Wo-Chien",
         "CHIEN_PAO": "Chien-Pao", "TING_LU": "Ting-Lu", "CHI_YU": "Chi-Yu"}
REGIONS = {"ALOLA": "Alolan", "GALAR": "Galarian", "HISUI": "Hisuian", "PALDEA": "Paldean"}
METHODS = {"EVO_LEVEL": "Lv. {p}", "EVO_FRIENDSHIP": "Friendship", "EVO_FRIENDSHIP_DAY": "Friendship, day",
           "EVO_FRIENDSHIP_NIGHT": "Friendship, night", "EVO_TRADE": "Trade", "EVO_TRADE_ITEM": "Trade holding {i}",
           "EVO_ITEM": "{i}", "EVO_LEVEL_DAY": "Lv. {p}, day", "EVO_LEVEL_NIGHT": "Lv. {p}, night",
           "EVO_LEVEL_ATK_GT_DEF": "Lv. {p}, Atk > Def", "EVO_LEVEL_ATK_EQ_DEF": "Lv. {p}, Atk = Def",
           "EVO_LEVEL_ATK_LT_DEF": "Lv. {p}, Atk < Def", "EVO_ITEM_HOLD_DAY": "Hold {i}, day, level up",
           "EVO_ITEM_HOLD_NIGHT": "Hold {i}, night, level up", "EVO_MOVE": "Knows {m}", "EVO_LEVEL_RAIN": "Lv. {p} in rain",
           "EVO_SPECIFIC_MON_IN_PARTY": "Lv. up with {s} in the party", "EVO_LEVEL_DUSK": "Lv. {p}, dusk",
           "EVO_ITEM_HOLD": "Hold {i}, level up", "EVO_CRITICAL_HITS": "{p} critical hits in a battle",
           "EVO_SCRIPT_TRIGGER_DMG": "Take {p} damage, then walk", "EVO_DARK_SCROLL": "Scroll of Darkness",
           "EVO_WATER_SCROLL": "Scroll of Waters", "EVO_ITEM_NIGHT": "{i}, night", "EVO_ITEM_DAY": "{i}, day",
           "EVO_LEVEL_FOG": "Lv. {p} in fog", "EVO_LEVEL_NATURE_AMPED": "Lv. {p}, amped nature",
           "EVO_LEVEL_NATURE_LOW_KEY": "Lv. {p}, low-key nature", "EVO_USE_MOVE_TWENTY_TIMES": "Use {m} 20 times",
           "EVO_RECOIL_DAMAGE_MALE": "{p} recoil damage, male", "EVO_RECOIL_DAMAGE_FEMALE": "{p} recoil damage, female",
           "EVO_LEVEL_FAMILY_OF_THREE": "Lv. {p} (family of three)", "EVO_LEVEL_FAMILY_OF_FOUR": "Lv. {p} (family of four)",
           "EVO_LEVEL_MALE": "Lv. {p}, male", "EVO_LEVEL_FEMALE": "Lv. {p}, female", "EVO_NONE": "—"}
CONDITIONS = {"IF_TIME": "{a}", "IF_MIN_FRIENDSHIP": "friendship {a}", "IF_GENDER": "{a}", "IF_HOLD_ITEM": "holding {a}",
              "IF_KNOWS_MOVE": "knows {a}", "IF_MIN_LEVEL": "Lv. {a}", "IF_WEATHER": "{a}", "IF_IN_MAPSEC": "at {a}",
              "IF_IN_MAP": "at {a}", "IF_TYPE_IN_PARTY": "a {a} type in the party", "IF_REGION": "in {a}",
              "IF_NOT_REGION": "not in {a}", "IF_PID_UPPER_MODULO_10_EQ": "",
              "IF_PID_UPPER_MODULO_10_GT": "", "IF_PID_UPPER_MODULO_10_LT": "", "IF_PID_MODULO_100_GT": "",
              "IF_PID_MODULO_100_LT": "", "IF_PID_MODULO_100_EQ": ""}


def pretty(constant):
    """SPECIES_WOOPER_PALDEA -> Paldean Wooper; ITEM_THUNDER_STONE -> Thunder Stone."""
    if constant == "FRIENDSHIP_EVO_THRESHOLD":
        return "high"
    for prefix in ("SPECIES_", "ITEM_", "MOVE_", "TIME_", "WEATHER_", "MON_", "GENDER_", "MAPSEC_", "MAP_", "TYPE_", "REGION_"):
        if constant.startswith(prefix):
            constant = constant[len(prefix):]
            break
    if constant in NAMES:
        return NAMES[constant]
    parts = constant.split("_")
    if len(parts) > 1 and parts[-1] in REGIONS:
        return REGIONS[parts[-1]] + " " + pretty("_".join(parts[:-1]))
    if "_".join(parts[:-1]) in NAMES and len(parts) > 1:
        return NAMES["_".join(parts[:-1])] + " (" + parts[-1].title() + ")"
    return " ".join(p.title() for p in parts)


def species_blocks():
    """species constant -> the text of its species info block, over every file."""
    blocks = {}
    header = re.compile(r"\[SPECIES_(\w+)\]\s*=\s*\n?\s*\{")
    for path in sorted(glob.glob(os.path.join(SPECIES_INFO, "*.h"))):
        text = open(path).read()
        matches = list(header.finditer(text))
        for i, m in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            blocks.setdefault("SPECIES_" + m.group(1), text[m.end():end])
    return blocks


def evolutions_of(block):
    """-> [(method, parameter, target species, [condition tokens...])] from `.evolutions = EVOLUTION(...)`."""
    start = block.find(".evolutions")
    if start < 0:
        return []
    start = block.index("EVOLUTION(", start) + len("EVOLUTION(")
    depth, i = 1, start
    while depth and i < len(block):
        depth += {"(": 1, ")": -1}.get(block[i], 0)
        i += 1
    body = block[start:i - 1]
    out = []
    for m in re.finditer(r"\{\s*(EVO_\w+)\s*,\s*([^,}]+?)\s*,\s*(SPECIES_\w+)\s*(?:,\s*CONDITIONS\((.*?)\)\s*)?\}", body, re.S):
        conditions = re.findall(r"\{([^{}]*)\}", m.group(4) or "")
        out.append((m.group(1), m.group(2).strip(), m.group(3), [c.strip() for c in conditions]))
    return out


def method_text(method, parameter, conditions):
    text = METHODS.get(method, pretty(method[4:]).replace("Lv", "Lv.") + " {p}")
    text = text.format(p=parameter, i=pretty(parameter) if parameter.startswith("ITEM_") else parameter,
                       m=pretty(parameter) if parameter.startswith("MOVE_") else parameter,
                       s=pretty(parameter) if parameter.startswith("SPECIES_") else parameter)
    extras = []
    for condition in conditions:
        tokens = [t.strip() for t in condition.split(",")]
        if tokens[0] in MUTAGEN_CONDITIONS:
            extras.append(MUTAGEN_CONDITIONS[tokens[0]])
        elif tokens[0] in CONDITIONS:
            piece = CONDITIONS[tokens[0]].format(a=pretty(tokens[1]).lower() if len(tokens) > 1 else "")
            if piece:
                extras.append(piece)
        else:
            extras.append(" ".join(pretty(t).lower() for t in tokens))
    if method == "EVO_LEVEL" and parameter == "0":
        text = "Level up"
    return ", ".join([text] + extras) if extras else text


def sprite(species):
    """The first frame of the species' front sprite, as docs/pokerom/sprites/<name>.png -> its file name."""
    name = species[len("SPECIES_"):].lower()
    parts = name.split("_")
    candidates = [os.path.join(GRAPHICS, name), os.path.join(GRAPHICS, "_".join(parts[:-1]), parts[-1]) if len(parts) > 1 else None]
    for folder in filter(None, candidates):
        for file in ("anim_front.png", "front.png"):
            path = os.path.join(folder, file)
            if os.path.exists(path):
                image = Image.open(path)
                frame = image.crop((0, 0, image.width, min(image.height, image.width)))
                rgba = frame.convert("RGBA")
                if frame.mode == "P":
                    alpha = frame.point(lambda index: 0 if index == 0 else 255, "L")
                    rgba.putalpha(alpha)
                os.makedirs(OUT_SPRITES, exist_ok=True)
                out = name + ".png"
                rgba.save(os.path.join(OUT_SPRITES, out), optimize=True)
                return out
    return None


def card(species):
    file = sprite(species)
    image = f'<img src="sprites/{file}" alt="" width="64" height="64">' if file else '<span class="nosprite"></span>'
    return f'<div class="mon">{image}<span>{pretty(species)}</span></div>'


def arrow(label, mutagen=False):
    """The usual line gets a plain arrow (CSS); the Mutagen's line the brand's fork mark."""
    if mutagen:
        return f'<div class="arrow mutagen"><span>{label}</span>{MARK}</div>'
    return f'<div class="arrow"><span>{label}</span></div>'


def main():
    blocks = species_blocks()
    evolutions = {species: evolutions_of(block) for species, block in blocks.items()}
    into = {}   # target -> [(source, method text)]
    for species, evos in evolutions.items():
        for method, parameter, target, conditions in evos:
            into.setdefault(target, []).append((species, method_text(method, parameter, conditions)))
    families = sorted(species for species, evos in evolutions.items()
                      if any(c.split(",")[0].strip() in MUTAGEN_CONDITIONS for _, _, _, cs in evos for c in cs))
    lines = ["# Mutagen evolutions", "",
             "A Pokémon that carries the Mutagen, the mutant strain of Pokérus, and outlives it can evolve along",
             "a second line when it next levels up: the Mutagen's twin of its usual evolution, a form the game's",
             "data already held (the Paradox and regional relatives). The usual line stays open; the Mutagen",
             "line is the one marked with the fork. The strain's parity decides Donphan's two twins. Generated",
             f"from the species data by `tools/site/evolutions.py`: {len(families)} families.", "",
             ""]
    for species in families:
        chain = []      # what evolves into this species, nearest first, up to two steps
        current = species
        for _ in range(2):
            sources = into.get(current, [])
            if not sources:
                break
            source, how = sources[0]
            chain.insert(0, (source, how))
            current = source
        html = ['<div class="evo">']
        for source, how in chain:
            html.append(card(source))
            html.append(arrow(how))
        html.append(card(species))
        html.append('<div class="lines">')
        for method, parameter, target, conditions in evolutions[species]:
            mutagen = any(c.split(",")[0].strip() in MUTAGEN_CONDITIONS for c in conditions)
            html.append(f'<div class="line{" mutagen" if mutagen else ""}">{arrow(method_text(method, parameter, conditions), mutagen)}{card(target)}</div>')
        html.append("</div></div>")
        lines.append("".join(html))
        lines.append("")
    with open(OUT_MD, "w") as f:
        f.write("\n".join(lines))
    print(f"evolutions: {len(families)} families -> {os.path.relpath(OUT_MD, ROOT)}, sprites in {os.path.relpath(OUT_SPRITES, ROOT)}")
    for species in families:
        print("  " + pretty(species) + ": " + "; ".join(
            f"{pretty(t)} ({method_text(m, p, c)})" for m, p, t, c in evolutions[species]))


if __name__ == "__main__":
    sys.exit(main())
