#!/usr/bin/env python3
"""Render spritecheck.py's data the way the game draws it, for review by eye.

    tools/spritecheck/spritecheck.py --json /tmp/sc.json --level INFO > /tmp/sc.txt
    tools/spritecheck/sheet.py /tmp/sc.json --findings /tmp/sc.txt --html /tmp/sprites.html   # one page
    tools/spritecheck/sheet.py /tmp/sc.json --png /tmp/sheets [--only SPECIES_X ...]         # contact sheets

Each battle cell puts frame 1 where the battle code puts it: the enemy at its Y offset minus its
elevation over the ground line, the player's back sprite at its Y offset over the text box edge.
Colours come from the .pal files the ROM is built from, not from the PNGs' own palettes.
"""
import argparse
import base64
import html
import io
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spritecheck import FRAME, load_known, load_pal, load_png  # noqa: E402

GROUND = 80      # enemy stage: the ground line; the frame top sits at GROUND + yOffset - elevation - 64
TEXTBOX = 72     # player stage: the text box top; the frame top sits at TEXTBOX + yOffset - 64
STAGE_H = 88
BG = (248, 248, 240, 255)
PLATFORM = (196, 214, 168, 255)
BOX = (56, 64, 80, 255)


def rgb(c5):
    return tuple((v << 3) | (v >> 2) for v in c5)


def paint(img, pal, index=0, size=FRAME, width=None):
    """Frame `index` of an indexed sheet, coloured with `pal`, index 0 transparent."""
    if img is None or pal is None:
        return None
    w = width or img.size[0]
    frame = img.crop((0, index * size, w, index * size + size))
    colors = [rgb(c) + (255,) for c in pal] + [(255, 0, 255, 255)] * 16
    out = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    out.putdata([colors[p] if p else (0, 0, 0, 0) for p in frame.getdata()])
    return out


def place(stage, spr, top):
    """Draw a frame with its top edge at row `top`, clipping what falls above the stage."""
    if top >= 0:
        stage.alpha_composite(spr, (0, top))
    else:
        stage.alpha_composite(spr.crop((0, -top, spr.size[0], spr.size[1])), (0, 0))


def enemy_stage(row, pal, front=None, frame=0):
    stage = Image.new("RGBA", (FRAME, STAGE_H), BG)
    ImageDraw.Draw(stage).ellipse((6, GROUND - 5, FRAME - 7, GROUND + 5), fill=PLATFORM)
    spr = paint(load_png(front or row["front"]), load_pal(pal), frame)
    if spr:
        place(stage, spr, GROUND + row["frontY"] - row["elevation"] - FRAME)
    return stage


def player_stage(row, pal, back=None):
    stage = Image.new("RGBA", (FRAME, TEXTBOX + 8), BG)
    spr = paint(load_png(back or row["back"]), load_pal(pal))
    if spr:
        place(stage, spr, TEXTBOX + row["backY"] - FRAME)
    ImageDraw.Draw(stage).rectangle((0, TEXTBOX, FRAME, TEXTBOX + 8), fill=BOX)
    return stage


def icon_frames(png, slot, icon_pals):
    img = load_png(png) if png else None
    if img is None or slot >= len(icon_pals):
        return []
    return [paint(img, icon_pals[slot], i, 32) for i in range(img.size[1] // 32)]


def follower(row, shiny=False):
    img = load_png(row.get("ow"))
    pal = load_pal(row.get("owShiny" if shiny else "owPal"))
    w, h = row.get("owW") or 32, row.get("owH") or 32
    if img is None or pal is None or img.size[0] < w:
        return None
    return paint(img, pal, 0, h, w).crop((0, 0, w, h))


def png_uri(im):
    """An exact-palette PNG data URI: sprites have a few dozen colours, so this is lossless and
    about 40% smaller than RGBA."""
    colors = sorted(set(im.getdata()))
    index = {c: i for i, c in enumerate(colors)}
    pal = Image.new("P", im.size)
    pal.putpalette([v for c in colors for v in c[:3]])
    pal.putdata([index[c] for c in im.getdata()])
    buf = io.BytesIO()
    pal.save(buf, "PNG", optimize=True, transparency=bytes(c[3] for c in colors))
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def views(row, icon_pals):
    """(label, image) pairs for one species, in the order the page shows them."""
    out = [("Enemy", enemy_stage(row, row["palette"])), ("Shiny", enemy_stage(row, row["shiny"]))]
    if row.get("shinyModern"):
        out.append(("Modern shiny", enemy_stage(row, row["shinyModern"])))
    if load_png(row["front"]).size[1] > FRAME:
        out.append(("Frame 2", enemy_stage(row, row["palette"], frame=1)))
    if row.get("back"):
        out.append(("Player", player_stage(row, row["palette"])))
    if row.get("frontFemale"):
        out.append(("Female", enemy_stage(row, row.get("paletteFemale") or row["palette"], row["frontFemale"])))
    if row.get("backFemale"):
        out.append(("Female player", player_stage(row, row.get("paletteFemale") or row["palette"], row["backFemale"])))
    for i, im in enumerate(icon_frames(row.get("icon"), row["iconPal"], icon_pals)):
        out.append((f"Icon {i + 1}", im))
    if row.get("iconFemale"):
        out += [(f"Female icon {i + 1}", im)
                for i, im in enumerate(icon_frames(row["iconFemale"], row.get("iconPalFemale", 0), icon_pals))]
    out += [("Follower", follower(row)), ("Follower shiny", follower(row, True))]
    return [(label, im) for label, im in out if im is not None]


def contact_sheets(rows, out_dir, per_row=5, rows_per=8):
    os.makedirs(out_dir, exist_ok=True)
    cell_w, cell_h = FRAME * 4 + 12, STAGE_H + 14
    per_sheet, paths = per_row * rows_per, []
    for n in range(0, len(rows), per_sheet):
        chunk = rows[n:n + per_sheet]
        sheet = Image.new("RGBA", (per_row * cell_w, -(-len(chunk) // per_row) * cell_h), (255, 255, 255, 255))
        d = ImageDraw.Draw(sheet)
        for i, row in enumerate(chunk):
            x, y = (i % per_row) * cell_w, (i // per_row) * cell_h
            two = load_png(row["front"]).size[1] > FRAME
            cells = [enemy_stage(row, row["palette"]), enemy_stage(row, row["shiny"]),
                     enemy_stage(row, row["palette"], frame=1 if two else 0)]
            for k, im in enumerate(cells):
                sheet.alpha_composite(im, (x + k * (FRAME + 2), y))
            if row.get("back"):
                sheet.alpha_composite(player_stage(row, row["palette"]), (x + 3 * (FRAME + 2), y + STAGE_H - TEXTBOX - 8))
            d.text((x + 2, y + STAGE_H + 1), f"{row['id']} {row['species'][8:]}"[:34], fill=(0, 0, 0, 255))
        path = os.path.join(out_dir, f"sheet_{n // per_sheet:02d}.png")
        sheet.save(path)
        paths.append(path)
    return paths


def parse_findings(path):
    """spritecheck.py report text -> {species: [(level, check, text)]}."""
    flags, check, level = {}, None, None
    for line in open(path):
        if line.startswith("== "):
            check, level = line[3:].split(" (")[0], line.split("(")[1].split(",")[0]
        elif line.startswith("  ") and check and ": " in line:
            sp, text = line.strip().split(": ", 1)
            flags.setdefault(sp.split("/")[0], []).append((level, check, text))
    return flags


def page(rows, flags, out, note=None):
    icon_pals = [load_pal(f"graphics/pokemon/icon_palettes/pal{i}.pal") for i in range(6)]
    for (check, sp), reason in load_known().items():
        flags.setdefault(sp.split("/")[0], []).append(("KNOWN", check, reason))
    cards = []
    for row in rows:
        figs = "".join(f'<figure><img src="{png_uri(im)}" alt="{html.escape(label)}" '
                       f'width="{im.size[0] * 2}" height="{im.size[1] * 2}"><figcaption>{html.escape(label)}'
                       f"</figcaption></figure>" for label, im in views(row, icon_pals))
        tags = flags.get(row["species"], [])
        items = "".join(f'<li class="{lv.lower()}"><b>{html.escape(c)}</b> {"known: " if lv == "KNOWN" else ""}'
                        f'{html.escape(t)}</li>' for lv, c, t in tags)
        kinds = " ".join(sorted({c for lv, c, _ in tags if lv != "KNOWN"}))
        style = "gba" if "_gba" in row["front"] else "ds"
        traits = " ".join(t for t, on in (("female", row.get("frontFemale")), ("shiny-modern", row.get("shinyModern")),
                                          ("no-follower", row.get("owSubstitute"))) if on)
        name = row["species"][8:].replace("_", " ").title()
        cards.append(f'<section class="card" data-name="{html.escape(name.lower())}" data-flags="{kinds}" '
                     f'data-style="{style}" data-traits="{traits}"><h2>{html.escape(name)} '
                     f'<span>#{row["natDex"]} · {"GBA" if style == "gba" else "DS"} style</span></h2>'
                     f'<div class="figs">{figs}</div>{"<ul>" + items + "</ul>" if items else ""}</section>')
    kinds = sorted({c for v in flags.values() for lv, c, _ in v if lv != "KNOWN"})
    with open(out, "w") as f:
        f.write(PAGE.replace("{{options}}", "".join(f'<option value="{k}">{k}</option>' for k in kinds))
                .replace("{{note}}", open(note).read() if note else "")
                .replace("{{cards}}", "\n".join(cards)).replace("{{count}}", str(len(rows))))


PAGE = """<title>Sprite review</title>
<style>
:root{color-scheme:light;--bg:#f4f3ee;--card:#fff;--ink:#1c2230;--muted:#5d6577;--line:#e2dfd3;--accent:#3b5bdb;
--error:#b42318;--warn:#a15c07;--info:#475467;--known:#2f7d4f}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){color-scheme:dark;--bg:#13151b;--card:#1c1f28;
--ink:#e8eaf0;--muted:#9aa3b5;--line:#2c3040;--accent:#91a7ff;--error:#f97066;--warn:#fdb022;--info:#98a2b3;--known:#6ce9a6}}
:root[data-theme=dark]{color-scheme:dark;--bg:#13151b;--card:#1c1f28;--ink:#e8eaf0;--muted:#9aa3b5;--line:#2c3040;
--accent:#91a7ff;--error:#f97066;--warn:#fdb022;--info:#98a2b3;--known:#6ce9a6}
body{background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding-inline:16px;padding-block:0 48px}
header{position:sticky;top:env(safe-area-inset-top,0px);z-index:2;background:var(--bg);border-bottom:1px solid var(--line);
padding-block:12px;display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center}
h1{font-size:17px;margin:0 8px 0 0}
input,select{font:inherit;padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink)}
input{flex:1 1 180px;min-width:0}
#n{color:var(--muted);font-variant-numeric:tabular-nums}
.note{margin-top:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;margin-top:12px;padding:10px 14px 12px;
content-visibility:auto;contain-intrinsic-size:auto 230px}
h2{font-size:15px;margin:0 0 8px}h2 span{color:var(--muted);font-weight:400;font-size:13px;margin-left:6px}
.figs{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end}
figure{margin:0;text-align:center}img{image-rendering:pixelated;display:block;max-width:100%;height:auto}
figcaption{font-size:11px;color:var(--muted);margin-top:2px}
ul{margin:10px 0 0;padding-left:18px;font-size:12.5px}li{margin:2px 0}
li.error{color:var(--error)}li.warn{color:var(--warn)}li.info{color:var(--info)}li.known{color:var(--known)}
li b{font-weight:600;margin-right:4px}
</style>
<div class="wrap">
<header><h1>Sprite review</h1>
<input id="q" type="search" placeholder="Search species" aria-label="Search species">
<select id="f" aria-label="Filter by finding"><option value="">Every species</option><option value="*">Any open finding</option>{{options}}</select>
<select id="s" aria-label="Filter by sprite style"><option value="">Both styles</option><option value="gba">GBA style (Gen 1-3)</option><option value="ds">DS style (Gen 4-9)</option></select>
<select id="t" aria-label="Filter by trait"><option value="">Any trait</option><option value="female">Female sprites</option><option value="shiny-modern">Modern shiny</option><option value="no-follower">Substitute follower</option></select>
<span id="n" aria-live="polite">{{count}} species</span></header>
<div class="note">{{note}}</div>
<main id="list">{{cards}}</main>
</div>
<script>
const $=id=>document.getElementById(id),cards=[...document.querySelectorAll('.card')];
function apply(){const q=$('q').value.trim().toLowerCase(),f=$('f').value,s=$('s').value,t=$('t').value;let c=0;
for(const el of cards){const fl=el.dataset.flags.split(' ').filter(Boolean);
const ok=(!q||el.dataset.name.includes(q))&&(!f||(f==='*'?fl.length>0:fl.includes(f)))&&(!s||el.dataset.style===s)
&&(!t||el.dataset.traits.split(' ').includes(t));el.hidden=!ok;if(ok)c++}
$('n').textContent=c+(c===1?' species':' species')}
for(const id of ['q','f','s','t'])$(id).addEventListener(id==='q'?'input':'change',apply);
</script>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data", help="spritecheck.py --json output")
    ap.add_argument("--png", help="write contact sheets to this directory")
    ap.add_argument("--html", help="write one browsable page")
    ap.add_argument("--findings", help="spritecheck.py report text, to list each species' findings")
    ap.add_argument("--note", help="an HTML fragment to show above the list")
    ap.add_argument("--only", nargs="*", help="species constants to include")
    args = ap.parse_args()
    rows = [r for r in json.load(open(args.data)) if not r.get("placeholder")]
    if args.only:
        keep = set(args.only)
        rows = [r for r in rows if r["species"] in keep or r["species"][8:] in keep]
    if args.png:
        for p in contact_sheets(rows, args.png):
            print(p)
    if args.html:
        page(rows, parse_findings(args.findings) if args.findings else {}, args.html, args.note)
        print(args.html)


if __name__ == "__main__":
    main()
