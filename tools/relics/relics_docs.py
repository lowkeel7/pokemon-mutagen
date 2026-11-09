"""The species parts as a docs page: docs/pokerom/relics.md with each part's bag icon and both views.

Called by `tools/relics/cut.py --docs`. The icons and sheets are written to docs/pokerom/relics/ from
the same cuts the ROM is built from; the page is styled by docs/pokerom/brand/mutagen.css (.relics).
"""
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_MD = os.path.join(ROOT, "docs/pokerom/relics.md")
OUT_DIR = os.path.join(ROOT, "docs/pokerom/relics")
PLACES = {
    "HEAD": "on the head",
    "FACE": "over the face",
    "BODY": "around the body",
    "BACK": "on the back (behind the Pokémon when it faces you)",
}


def rgba(rows, pal):
    h, w = len(rows), len(rows[0])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            v = rows[y][x]
            if v:
                px[x, y] = pal[v] + (255,)
    return im


def write(parts, build):
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    for part, spec in parts.items():
        sheet, icon, pal, _, _ = build(part, spec)
        cell = len(sheet) // 2
        rgba(icon, pal).save(os.path.join(OUT_DIR, part + "-icon.png"))
        rgba(sheet[:cell], pal).save(os.path.join(OUT_DIR, part + "-front.png"))
        rgba(sheet[cell:], pal).save(os.path.join(OUT_DIR, part + "-back.png"))
        donor = spec["donor"].replace("_", " ").title()
        source = spec.get("recolour", (None,))[0]
        taken = f"cut from {donor}'s own sprites" if not source else f"the Cubone skull in {source.title()}'s colours"
        worn = spec.get("effect") or spec["ability"]
        if spec.get("poached"):
            worn += " (poached: no wild drop; the black market's, later)"
        rows.append(
            f'<tr><td><img src="relics/{part}-icon.png" alt="" width="48" height="48"></td>'
            f'<td><b>{spec["name"]}</b><br><span class="sub">{taken}</span></td>'
            f'<td>{worn}</td><td>{spec["lends"]}</td><td>{PLACES[spec["anchor"]]}</td>'
            f'<td><img src="relics/{part}-front.png" alt="front view" width="64" height="64">'
            f'<img src="relics/{part}-back.png" alt="back view" width="64" height="64"></td></tr>'
        )
    body = "\n".join(rows)
    with open(OUT_MD, "w") as f:
        f.write(f"""# Relics: the species parts

With **MUTAGEN → RELICS** on, a species part used from the bag on a party Pokémon is *worn*: it shows
on the Pokémon's battle sprite, front and back, and in its summary, and the Pokémon has what the part
gives, whatever its species: an ability; a family of moves that hits harder (slash, stab, bite,
punch, sound, wind, ballistic or blunt; a few parts add a critical-hit stage or venom to those
moves); or a stat raised by a fifth while a wearer of the part's type has it on (Shuckle's shell:
both defenses by a tenth, for any wearer). Using another part asks to swap; the party menu's ITEM → TAKE OFF (or using the same part
again) takes it off, and the part goes back to the bag. Nothing is written to the Pokémon but the
part's index, so taking a part off gives it back exactly as it was. Every part is the donor
species' own pixels, cut by `tools/relics/cut.py` (nothing is drawn); the ROM colours it with the
donor's palette.

Where they come from: a wild Pokémon of the donor species drops its part one time in four when it
faints (RELICS on). **CHEAT SHELF → ALL** sells every part in every Poké Mart, and the sandbox build
starts with one of each. Generated from the same table the ROM is built from: {len(rows)} parts.

<table class="relics">
<thead><tr><th></th><th>Part</th><th>Worn, it gives</th><th>Type lent</th><th>Where it sits</th><th>Front and back</th></tr></thead>
<tbody>
{body}
</tbody>
</table>

The type a part lends is its donor's first type (its second when the first is Normal, so a bird's
part lends Flying): with **MUTAGEN → THIRD TYPE** on it is the wearer's third type while the part
is worn, in the summary and in battle. A Pokémon that already
has a third type of its own is asked which to show; its own type is never written over, and comes
back when the part comes off. A stat part asks for a wearer of that same type, so with THIRD TYPE on
every wearer qualifies unless it keeps a third type of its own (design note: [Species items](design/items.md)).
""")
    print(f"wrote {OUT_MD} and {3 * len(rows)} images")
