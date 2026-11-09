"""The species parts as a docs page: docs/pokerom/relics.md with each part's bag icon and the part worn
by a Pokémon, facing you and from behind.

Called by `tools/relics/cut.py --docs`. The icons and sheets are written to docs/pokerom/relics/ from
the same cuts the ROM is built from; the page is styled by docs/pokerom/brand/mutagen.css (.relics).
"""
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_MD = os.path.join(ROOT, "docs/pokerom/relics.md")
OUT_DIR = os.path.join(ROOT, "docs/pokerom/relics")
WEARERS = ("chikorita", "cyndaquil", "totodile")  # the Johto starters in turn, one a part
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


def worn_view(cut, wearer, cell, pal, spec, back):
    """The part on the wearer as the ROM draws it, at 2x: placed by the wearer's own first frame
    (cut.anchor_point is src/relic.c's FindAnchor), behind the Pokémon when it sits on the back of
    one facing you, in front otherwise. Front is the summary's and a foe's view, back your own
    Pokémon's in battle."""
    front_path, back_path, pal_path = cut.donor_files(wearer)
    rows = cut.frame(back_path if back else front_path)
    mon = rgba(rows, cut.read_pal(pal_path))
    piece = rgba(cell, pal)
    ax, ay = cut.anchor_point(rows, spec["anchor"], spec.get("dy", 0), back=back)
    at = (ax - cut.CELL // 2, ay - cut.CELL)
    scene = Image.new("RGBA", mon.size, (0, 0, 0, 0))
    layers = [(piece, at), (mon, (0, 0))] if spec["anchor"] == "BACK" and not back else [(mon, (0, 0)), (piece, at)]
    for im, xy in layers:
        scene.paste(im, xy, im)
    return scene.resize((scene.width * 2, scene.height * 2), Image.NEAREST)


def write(parts, build, cut):
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    for n, (part, spec) in enumerate(parts.items()):
        sheet, icon, pal, _, _ = build(part, spec)
        cell = len(sheet) // 2
        wearer = WEARERS[n % len(WEARERS)]
        rgba(icon, pal).save(os.path.join(OUT_DIR, part + "-icon.png"))
        worn_view(cut, wearer, sheet[:cell], pal, spec, back=False).save(os.path.join(OUT_DIR, part + "-worn-front.png"))
        worn_view(cut, wearer, sheet[cell:], pal, spec, back=True).save(os.path.join(OUT_DIR, part + "-worn-back.png"))
        on = wearer.title()
        donor = spec["donor"].replace("_", " ").title()
        source = spec.get("recolour", (None,))[0]
        taken = f"cut from {donor}'s own sprites" if not source else f"the Cubone skull in {source.title()}'s colours"
        worn = spec.get("effect") or spec["ability"]
        if spec.get("poached"):
            worn += " (poached: no wild drop; the black market's, later)"
        rows.append(
            f'<tr><td><img src="relics/{part}-icon.png" alt="" width="48" height="48"></td>'
            f'<td><b>{spec["name"]}</b><span class="sub">{taken}</span>'
            f'<span class="sub">lends {spec["lends"]}; sits {PLACES[spec["anchor"]]}</span></td>'
            f'<td>{worn}</td>'
            f'<td class="worn"><img src="relics/{part}-worn-front.png" alt="{spec["name"]} on {on}, facing you" width="128" height="128">'
            f'<img src="relics/{part}-worn-back.png" alt="{spec["name"]} on {on}, from behind" width="128" height="128">'
            f'<span class="sub">on {on}</span></td></tr>'
        )
    body = "\n".join(rows)
    with open(OUT_MD, "w") as f:
        f.write(f"""# Relics: the species parts

> **Work in progress.** The parts' sprites are a first pass, cut from the donors' own art by a script,
> and they will be redone. What each part does in battle is built and tested.

With **MUTAGEN → RELICS** on, a species part used from the bag on a party Pokémon is *worn*: it shows
on the Pokémon's battle sprite, front and back, and in its summary, and the Pokémon has what the part
gives, whatever its species: an ability; a family of moves that hits harder (slash, stab, bite,
punch, sound, wind, ballistic or blunt; a few parts add a critical-hit stage or venom to those
moves); or a stat raised by a fifth while a wearer of the part's type has it on (Shuckle's shell:
both defenses by a tenth, for any wearer); or one thing of its own (the misc parts: more HP from
draining moves, surer sleep moves, HP back in the sun, a hit lived through once a battle). Using another part asks to swap; the party menu's ITEM → TAKE OFF (or using the same part
again) takes it off, and the part goes back to the bag. Nothing is written to the Pokémon but the
part's index, so taking a part off gives it back exactly as it was. Every part is the donor
species' own pixels, cut by `tools/relics/cut.py` (nothing is drawn); the ROM colours it with the
donor's palette.

Where they come from: a wild Pokémon of the donor species drops its part one time in four when it
faints (RELICS on). **CHEAT SHELF → ALL** sells every part in every Poké Mart, and the sandbox build
starts with one of each. Generated from the same table the ROM is built from: {len(rows)} parts.

Each part is shown worn by a Johto starter, placed the way the ROM places it: facing you, as in the
summary or on a foe, and from behind, as your own Pokémon in battle. A part on the back sits behind a
Pokémon that faces you, so only what rises above or beside it shows. These are the GBA sprites; with
**FEATURES → SPRITES → DS** the ROM places each part by the DS art's outline the same way.

<div class="relics-wrap">
<table class="relics">
<thead><tr><th></th><th>Part</th><th>Worn, it gives</th><th>On a Pokémon, facing you and from behind</th></tr></thead>
<tbody>
{body}
</tbody>
</table>
</div>

The type a part lends is its donor's first type (its second when the first is Normal, so a bird's
part lends Flying): with **MUTAGEN → THIRD TYPE** on it is the wearer's third type while the part
is worn, in the summary and in battle. A Pokémon that already
has a third type of its own is asked which to show; its own type is never written over, and comes
back when the part comes off. A stat part asks for a wearer of that same type, so with THIRD TYPE on
every wearer qualifies unless it keeps a third type of its own (design note: [Species items](design/items.md)).
""")
    print(f"wrote {OUT_MD} and {3 * len(rows)} images")
