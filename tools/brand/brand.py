#!/usr/bin/env python3
"""Pokémon Mutagen's brand assets, generated from the game's own pixels (docs/pokerom/design/brand.md).

    tools/brand/brand.py                      # everything into docs/pokerom/brand/ and docs/theme/
    tools/brand/brand.py variants --out DIR   # the cover's three compositions, to pick from
    tools/brand/brand.py cover --variant a --out cover.png [--size 1280x640]
    tools/brand/brand.py titlecard --subtitle "voxel view" --size 1920x1080 --out card.png
    tools/brand/brand.py contrast             # the palette's WCAG contrast table (pasted into brand.md)

Nothing here is drawn by a model. The wordmark is the title screen's own MUTAGEN banner
(graphics/title_screen/hns/emerald_version.png, Heart & Soul's pixel small caps) traced pixel for
pixel; the fork mark is a grid of squares written below; the Pokémon are the game's front sprites
(docs/pokerom/sprites, cut by tools/site/evolutions.py) scaled by whole numbers; the type chips are
the game's type icons; the texture is seeded dots. Fonts: tools/brand/fonts.py.
"""
import argparse
import os
import random
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRAND = os.path.join(ROOT, "docs/pokerom/brand")
FONTS = os.path.join(BRAND, "fonts")
THEME = os.path.join(ROOT, "docs/theme")
SPRITES = os.path.join(ROOT, "docs/pokerom/sprites")
TYPES = os.path.join(ROOT, "graphics/types")
BANNER = os.path.join(ROOT, "graphics/title_screen/hns/emerald_version.png")

# --- the palette ----------------------------------------------------------------------------------
# The first five are the title banner's own pixels (emerald_version.gbapal); the strain and the graft
# are the brand's two accents; paper is the light theme's ground.
PALETTE = {
    "ink":         ("#181018", "the banner's outline; the dark ground, text on paper"),
    "pill":        ("#292929", "the banner's fill; panels and cards on ink"),
    "seam":        ("#4A4A4A", "the banner's mid grey; borders and rules on ink"),
    "ash":         ("#9C9C9C", "the banner's light grey; muted text on ink"),
    "bone":        ("#EEEEEE", "the banner's letters; text on ink"),
    "strain":      ("#C43AD6", "the Mutagen: the second line, the highlight, the lower arm of the mark"),
    "strain-deep": ("#8A1E9C", "the strain on paper: links and labels on light grounds"),
    "strain-soft": ("#E39BEE", "the strain on ink: links and labels on dark grounds"),
    "graft":       ("#A6F23A", "the graft: the third type, success, the odd accent on ink"),
    "graft-deep":  ("#3F7A0A", "the graft on paper"),
    "paper":       ("#F7F4F8", "the light ground"),
    "paper-2":     ("#ECE6EE", "panels and cards on paper"),
}
C = {name: value[0] for name, value in PALETTE.items()}

# --- the fork mark: 12 x 12 squares, two strokes thick. The stem and the upper arm are one colour
# (the usual line), the lower arm the strain (the Mutagen's line).
MARK_W = MARK_H = 12
_UPPER = [(0, 5), (1, 5), (2, 5), (3, 5), (4, 5), (5, 5), (6, 5),       # the stem, two rows
          (0, 6), (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 6)]
_LOWER = []
for _i in range(5):                                                      # 2x2 blocks stepping one square
    for _dx in (0, 1):
        for _dy in (0, 1):
            _UPPER.append((6 + _i + _dx, 4 - _i + _dy))
            _LOWER.append((6 + _i + _dx, 6 + _i + _dy))
MARK = {"upper": sorted(set(_UPPER)), "lower": sorted(set(_LOWER))}


def hex2rgb(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def luminance(h):
    def channel(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b, _ = hex2rgb(h)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# --- the banner's letters --------------------------------------------------------------------------

def banner_glyphs():
    """letter -> list of row strings ('#' set) of the MUTAGEN banner: 11 rows, one-pixel strokes.
    The sheet is 64 wide; the word wraps after G and two columns of E into a second block."""
    sheet = Image.open(BANNER)
    px = sheet.load()
    palette = sheet.getpalette()
    white = next(i for i in range(256) if tuple(palette[i * 3:i * 3 + 3]) == (255, 255, 255))
    rows = []
    for y in range(11):
        first = "".join("#" if px[x, 11 + y] == white else "." for x in range(32, 64))
        second = "".join("#" if px[x, 43 + y] == white else "." for x in range(0, 8))
        rows.append(first + second)
    width = len(rows[0])
    columns = [any(row[x] == "#" for row in rows) for x in range(width)]
    spans, start = [], None
    for x, filled in enumerate(columns + [False]):
        if filled and start is None:
            start = x
        elif not filled and start is not None:
            spans.append((start, x))
            start = None
    letters = "MUTAGEN"
    if len(spans) != len(letters):
        sys.exit(f"brand: expected {len(letters)} letters in the banner, found {len(spans)}")
    return {letter: [row[a:b] for row in rows] for letter, (a, b) in zip(letters, spans)}


def word_bitmap(word="MUTAGEN", gap=1):
    """The word as rows of '#'/'.' from the banner's glyphs, one empty column between letters."""
    glyphs = banner_glyphs()
    rows = [""] * 11
    for i, letter in enumerate(word):
        for y in range(11):
            rows[y] += ("." * gap if i else "") + glyphs[letter][y]
    return rows


def bitmap_cells(rows):
    return [(x, y) for y, row in enumerate(rows) for x, ch in enumerate(row) if ch == "#"]


def cells_to_path(cells, scale=1, dx=0, dy=0):
    """An SVG path of unit squares merged along each row (crisp at any size)."""
    by_row = {}
    for x, y in cells:
        by_row.setdefault(y, []).append(x)
    parts = []
    for y in sorted(by_row):
        xs = sorted(by_row[y])
        start = prev = xs[0]
        for x in xs[1:] + [None]:
            if x is None or x != prev + 1:
                parts.append(f"M{(start + dx) * scale} {(y + dy) * scale}h{(prev - start + 1) * scale}v{scale}h-{(prev - start + 1) * scale}z")
                if x is not None:
                    start = x
            if x is not None:
                prev = x
    return "".join(parts)


def draw_cells(image, cells, colour, scale, x0, y0):
    draw = ImageDraw.Draw(image)
    for x, y in cells:
        draw.rectangle([x0 + x * scale, y0 + y * scale, x0 + (x + 1) * scale - 1, y0 + (y + 1) * scale - 1], fill=hex2rgb(colour))


def wordmark_image(scale, colour=C["bone"]):
    rows = word_bitmap()
    image = Image.new("RGBA", (len(rows[0]) * scale, len(rows) * scale), (0, 0, 0, 0))
    draw_cells(image, bitmap_cells(rows), colour, scale, 0, 0)
    return image


def mark_image(scale, upper=C["bone"], lower=C["strain"]):
    image = Image.new("RGBA", (MARK_W * scale, MARK_H * scale), (0, 0, 0, 0))
    draw_cells(image, MARK["upper"], upper, scale, 0, 0)
    draw_cells(image, MARK["lower"], lower, scale, 0, 0)
    return image


# --- SVG ---------------------------------------------------------------------------------------------

def svg(width, height, body, attrs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'shape-rendering="crispEdges"{attrs}>{body}</svg>\n')


def wordmark_svg(fill):
    rows = word_bitmap()
    return svg(len(rows[0]), len(rows), f'<path fill="{fill}" d="{cells_to_path(bitmap_cells(rows))}"/>',
               ' role="img" aria-label="MUTAGEN"')


def mark_svg(upper, lower):
    body = f'<path fill="{upper}" d="{cells_to_path(MARK["upper"])}"/><path fill="{lower}" d="{cells_to_path(MARK["lower"])}"/>'
    return svg(MARK_W, MARK_H, body, ' role="img" aria-label="the Mutagen fork"')


def fork_cells(length=40, height=24, t=2):
    """A wide fork on a grid: a stem, then two stair arms to the top and bottom right corners."""
    upper, lower = [], []
    mid = height // 2 - t // 2
    rise = mid // t
    stem = length - rise * t - t
    for x in range(stem):
        for dy in range(t):
            upper.append((x, mid + dy))
    for i in range(rise):
        for dx in range(t):
            for dy in range(t):
                upper.append((stem + i * t + dx - t + t, mid - (i + 1) * t + dy))
                lower.append((stem + i * t + dx - t + t, mid + (i + 1) * t + dy))
    return {"upper": sorted(set(upper)), "lower": sorted(set(lower)), "w": length, "h": height}


def fork_svg(upper, lower, length=40, height=24):
    cells = fork_cells(length, height)
    body = (f'<path fill="{upper}" d="{cells_to_path(cells["upper"])}"/>'
            f'<path fill="{lower}" d="{cells_to_path(cells["lower"])}"/>')
    return svg(cells["w"], cells["h"], body, ' role="img" aria-label="one line becomes two"')


def favicon_svg():
    body = (f'<rect width="16" height="16" rx="3" fill="{C["ink"]}"/>'
            f'<path fill="{C["bone"]}" d="{cells_to_path(MARK["upper"], 1, 2, 2)}"/>'
            f'<path fill="{C["strain"]}" d="{cells_to_path(MARK["lower"], 1, 2, 2)}"/>')
    return svg(16, 16, body)


def font_face_css(embed=True, prefix="fonts/"):
    """@font-face rules for the brand's web fonts; `embed` inlines the woff2 files as data URIs so a
    page that is opened from disk (the voxel view) still gets them."""
    import base64
    faces = [("Space Grotesk", "SpaceGrotesk-Variable.woff2", "300 700"),
             ("Silkscreen", "Silkscreen-Regular.woff2", "400"), ("Silkscreen", "Silkscreen-Bold.woff2", "700")]
    rules = []
    for family, file, weight in faces:
        if embed:
            with open(os.path.join(FONTS, file), "rb") as f:
                url = "data:font/woff2;base64," + base64.b64encode(f.read()).decode()
        else:
            url = prefix + file
        rules.append(f'@font-face {{ font-family: "{family}"; src: url({url}) format("woff2"); font-weight: {weight}; font-display: swap; }}')
    return "\n".join(rules)


# --- raster helpers ---------------------------------------------------------------------------------

def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name + ".ttf"), size)


def text(image, xy, string, fnt, colour, pixel=False, spacing=0, anchor="la"):
    """Draw text; pixel fonts are drawn without anti-aliasing and may be letter-spaced."""
    draw = ImageDraw.Draw(image)
    draw.fontmode = "1" if pixel else "L"
    if spacing:
        x, y = xy
        for ch in string:
            draw.text((x, y), ch, font=fnt, fill=hex2rgb(colour), anchor=anchor)
            x += draw.textlength(ch, font=fnt) + spacing
        return x - spacing - xy[0]
    draw.text(xy, string, font=fnt, fill=hex2rgb(colour), anchor=anchor)
    return draw.textlength(string, font=fnt)


def text_width(string, fnt, spacing=0):
    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    if spacing:
        return sum(draw.textlength(ch, font=fnt) + spacing for ch in string) - spacing
    return draw.textlength(string, font=fnt)


def sprite(name, scale, dim=False):
    """The species' front sprite cropped to its visible pixels and scaled by a whole number; `dim`
    fades it for the usual line."""
    image = Image.open(os.path.join(SPRITES, name + ".png")).convert("RGBA")
    image = image.crop(image.getbbox())
    if dim:
        rgb = ImageEnhance.Color(image.convert("RGB")).enhance(0.55)
        alpha = image.getchannel("A").point(lambda a: a * 70 // 100)
        image = rgb.convert("RGBA")
        image.putalpha(alpha)
    return image.resize((image.width * scale, image.height * scale), Image.NEAREST)


def place(image, layer, centre):
    """Paste a layer by its centre; returns its box."""
    x = int(centre[0] - layer.width / 2)
    y = int(centre[1] - layer.height / 2)
    paste(image, layer, (x, y))
    return x, y, x + layer.width, y + layer.height


def species_name(name):
    names = {"sirfetchd": "SIRFETCH'D", "farfetchd": "FARFETCH'D", "mr_rime": "MR. RIME", "mr_mime": "MR. MIME"}
    return names.get(name, name.replace("_", " ").upper())


def type_chip(type_name, scale):
    """The game's type icon (graphics/types/<type>.png, 32x16, index 0 transparent) scaled up."""
    image = Image.open(os.path.join(TYPES, type_name + ".png"))
    rgba = image.convert("RGBA")
    mask = image.point(lambda i: 0 if i == 0 else 255, "L") if image.mode == "P" else None
    if mask:
        rgba.putalpha(mask)
    return rgba.resize((rgba.width * scale, rgba.height * scale), Image.NEAREST)


def paste(image, layer, xy):
    image.alpha_composite(layer, (int(xy[0]), int(xy[1])))


def ground(size, texture=True, seed=7):
    """Ink with the spore texture: seeded dots of the strain, sparse, denser towards the lower right."""
    w, h = size
    image = Image.new("RGBA", size, hex2rgb(C["ink"]))
    if not texture:
        return image
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    rng = random.Random(seed)
    unit = max(2, w // 640 * 2)
    for _ in range(w * h // 9000):
        x = int(rng.triangular(0, w, w * 0.8))
        y = int(rng.triangular(0, h, h * 0.9))
        s = unit * rng.choice((1, 1, 1, 2))
        alpha = rng.randint(18, 60)
        x -= x % unit
        y -= y % unit
        draw.rectangle([x, y, x + s - 1, y + s - 1], fill=hex2rgb(C["strain"], alpha))
    image.alpha_composite(layer)
    return image


def glow(image, centre, radius, colour=C["strain"], alpha=110):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    cx, cy = centre
    draw.ellipse([cx - radius, cy - radius * 0.8, cx + radius, cy + radius * 0.8], fill=hex2rgb(colour, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.45))
    image.alpha_composite(layer)


def pill(image, box, fill=None, outline=None, width=2):
    draw = ImageDraw.Draw(image)
    x0, y0, x1, y1 = box
    r = (y1 - y0) // 2
    draw.rounded_rectangle(box, radius=r, fill=hex2rgb(fill) if fill else None,
                           outline=hex2rgb(outline) if outline else None, width=width)


def chip(image, xy, label, fnt, colour=C["ash"], outline=C["seam"], pad=14, height=32):
    w = text_width(label, fnt) + pad * 2
    x, y = xy
    pill(image, (x, y, x + w, y + height), outline=outline)
    text(image, (x + pad, y + height // 2), label, fnt, colour, pixel=True, anchor="lm")
    return w


def fork(image, x0, y0, x1, y_up, y_down, thickness, upper=C["bone"], lower=C["strain"]):
    """A fork from (x0, y0) to the right: a stem, then two stair diagonals to y_up and y_down ending
    at x1 with a short lead. Drawn as squares of `thickness`, like the mark."""
    draw = ImageDraw.Draw(image)
    t = thickness
    rise_up, rise_down = y0 - y_up, y_down - y0
    stem_end = x1 - max(rise_up, rise_down) - t * 2
    draw.rectangle([x0, y0 - t // 2, stem_end + t, y0 + t // 2 - 1], fill=hex2rgb(upper))
    for rise, colour, sign in ((rise_up, upper, -1), (rise_down, lower, 1)):
        steps = rise // t
        x, y = stem_end + t, y0 - t // 2
        for i in range(steps):
            x += t
            y += sign * t
            draw.rectangle([x, y, x + t - 1, y + t - 1], fill=hex2rgb(colour))
        draw.rectangle([x + t, y, x1, y + t - 1], fill=hex2rgb(colour))


# --- the compositions --------------------------------------------------------------------------------

def wordmark_block(image, x, y, scale, eyebrow=True, tagline=None, colour=C["bone"], centre=False):
    """Eyebrow POKÉMON, the MUTAGEN wordmark and a tagline, stacked; returns the block's height."""
    mark = wordmark_image(scale, colour)
    eye = font("Silkscreen-Bold", scale * 2)
    tag = font("SpaceGrotesk-Medium", int(scale * 2.9))
    width = mark.width
    cx = x + width // 2
    cursor = y
    if eyebrow:
        label = "POKÉMON"
        w = text_width(label, eye, spacing=scale)
        text(image, (cx - w // 2 if centre else x, cursor), label, eye, C["ash"], pixel=True, spacing=scale)
        cursor += scale * 2 + int(scale * 1.6)
    paste(image, mark, (x, cursor))
    cursor += mark.height
    if tagline:
        cursor += int(scale * 2.2)
        w = text_width(tagline, tag)
        text(image, (cx - w // 2 if centre else x, cursor), tagline, tag, C["strain-soft"])
        cursor += int(scale * 3.6)
    return cursor - y, width


def cover_a(size):
    """The fork: the wordmark at the left, one Pokémon and its two lines at the right."""
    w, h = size
    s = w // 107                          # 12 at 1280: the wordmark is 480 wide
    x = w // 18
    tagline = "A second line of evolution."
    block_h, block_w = wordmark_block(Image.new("RGBA", size), x, 0, s, tagline=tagline)
    image = ground(size)
    top = (h - block_h - s * 4) // 2
    wordmark_block(image, x, top, s, tagline=tagline)
    small = font("Silkscreen-Regular", 16)
    cx = x
    for label in ("GBA · FLASH CART · mGBA", "PATCH, NEVER A ROM", "V0.1.0"):
        cx += chip(image, (cx, top + block_h + s), label, small) + 12

    label = font("Silkscreen-Regular", 16)
    base = sprite("wooper", 4)
    bx0, by0, bx1, by1 = place(image, base, (w * 0.54, h * 0.5))
    text(image, ((bx0 + bx1) // 2, by1 + 12), "WOOPER", label, C["ash"], pixel=True, anchor="ma")
    tx = w * 0.875
    y_up, y_down = h * 0.29, h * 0.68
    usual = sprite("quagsire", 3, dim=True)
    twin = sprite("clodsire", 4)
    left = int(tx - max(usual.width, twin.width) / 2)
    fork(image, bx1 + s, h // 2, left - s * 2, int(y_up), int(y_down), s // 2 + 2)
    ux0, uy0, ux1, uy1 = place(image, usual, (tx, y_up))
    text(image, ((ux0 + ux1) // 2, uy1 + 10), "QUAGSIRE", label, C["ash"], pixel=True, anchor="ma")
    glow(image, (tx, y_down), twin.width * 0.6)
    cx0, cy0, cx1, cy1 = place(image, twin, (tx, y_down))
    text(image, ((cx0 + cx1) // 2, cy1 + 10), "CLODSIRE", label, C["strain-soft"], pixel=True, anchor="ma")
    chips = [type_chip(t, 2) for t in ("poison", "ground", "dragon")]
    total = sum(c.width for c in chips) + 6 * (len(chips) - 1)
    cx = (cx0 + cx1) // 2 - total // 2
    for c in chips:
        paste(image, c, (cx, cy1 + 36))
        cx += c.width + 6
    return image


def cover_b(size):
    """The lineup: the wordmark above, seven of the Mutagen's twins in a row below."""
    w, h = size
    s = w // 107
    tagline = "Twenty-six Pokémon with a second line."
    block_h, block_w = wordmark_block(Image.new("RGBA", size), 0, 0, s, tagline=tagline)
    image = ground(size)
    wordmark_block(image, (w - block_w) // 2, int(h * 0.11), s, tagline=tagline, centre=True)
    names = ["clodsire", "kleavor", "flutter_mane", "great_tusk", "iron_treads", "sirfetchd", "sneasler"]
    sprites = [sprite(n, 2) for n in names]
    margin = w // 16
    gap = (w - margin * 2 - sum(sp.width for sp in sprites)) // (len(sprites) - 1)
    x = margin
    baseline = int(h * 0.80)
    label = font("Silkscreen-Regular", 16)
    for n, sp in zip(names, sprites):
        glow(image, (x + sp.width // 2, baseline - sp.height // 3), sp.width * 0.6, alpha=70)
        paste(image, sp, (x, baseline - sp.height))
        text(image, (x + sp.width // 2, baseline + 12), species_name(n), label, C["ash"], pixel=True, anchor="ma")
        x += sp.width + gap
    draw = ImageDraw.Draw(image)
    draw.rectangle([margin, baseline + 40, w - margin, baseline + 43], fill=hex2rgb(C["strain"]))
    return image


def cover_c(size):
    """The pill: the title screen's banner shape carrying the mark and the word."""
    w, h = size
    image = ground(size, seed=3)
    s = w // 80                           # 16 at 1280
    mark = mark_image(s - 4)
    word = wordmark_image(s)
    pad_x, pad_y = s * 3, s * 2
    inner_w = mark.width + s * 2 + word.width
    box_w, box_h = inner_w + pad_x * 2, word.height + pad_y * 2
    x0, y0 = (w - box_w) // 2, (h - box_h) // 2 - s * 2
    pill(image, (x0, y0, x0 + box_w, y0 + box_h), fill=C["pill"], outline=C["seam"], width=s // 4)
    paste(image, mark, (x0 + pad_x, y0 + pad_y + (word.height - mark.height) // 2))
    paste(image, word, (x0 + pad_x + mark.width + s * 2, y0 + pad_y))
    eye = font("Silkscreen-Bold", 24)
    label = "POKÉMON"
    text(image, (w // 2 - text_width(label, eye, spacing=12) // 2, y0 - 24 - s * 2), label, eye, C["ash"], pixel=True, spacing=12)
    tag = font("SpaceGrotesk-Medium", 34)
    line = "A mutant strain of Pokérus. A second line of evolution."
    text(image, (w // 2 - text_width(line, tag) // 2, y0 + box_h + s * 2), line, tag, C["strain-soft"])
    small = font("Silkscreen-Regular", 16)
    labels = ("GBA · FLASH CART · mGBA", "PATCH, NEVER A ROM", "V0.1.0")
    total = sum(text_width(l, small) + 28 for l in labels) + 12 * (len(labels) - 1)
    cx = w // 2 - total // 2
    for l in labels:
        cx += chip(image, (cx, y0 + box_h + s * 2 + 70), l, small) + 12
    return image


COVERS = {"a": cover_a, "b": cover_b, "c": cover_c}


def titlecard(size, subtitle, eyebrow="POKÉMON"):
    w, h = size
    image = ground(size, seed=11)
    s = max(6, w // 120)
    word = wordmark_image(s)
    mark = mark_image(s - 2)
    eye = font("Silkscreen-Bold", s * 2)
    sub = font("SpaceGrotesk-Medium", int(s * 3.4))
    total_w = mark.width + s * 2 + word.width
    x0 = (w - total_w) // 2
    y0 = h // 2 - word.height // 2 - s * 2
    text(image, (w // 2 - text_width(eyebrow, eye, spacing=s) // 2, y0 - s * 2 - int(s * 1.6)), eyebrow, eye, C["ash"], pixel=True, spacing=s)
    paste(image, mark, (x0, y0 + (word.height - mark.height) // 2))
    paste(image, word, (x0 + mark.width + s * 2, y0))
    if subtitle:
        text(image, (w // 2 - text_width(subtitle, sub) // 2, y0 + word.height + int(s * 2.4)), subtitle, sub, C["strain-soft"])
    return image


def icon(size):
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=size * 3 // 16, fill=hex2rgb(C["ink"]))
    unit = size * 3 // 4 // MARK_W
    mark = mark_image(unit)
    paste(image, mark, ((size - mark.width) // 2, (size - mark.height) // 2))
    return image


# --- the command line -------------------------------------------------------------------------------

def parse_size(value):
    w, h = value.lower().split("x")
    return int(w), int(h)


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(path, mode) as f:
        f.write(data)
    print(f"{os.path.relpath(path, ROOT)}  {os.path.getsize(path):,} B")


def save(path, image):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path, optimize=True)
    print(f"{os.path.relpath(path, ROOT)}  {os.path.getsize(path):,} B  {image.width}x{image.height}")


def contrast_table():
    pairs = [("bone", "ink"), ("ash", "ink"), ("strain", "ink"), ("strain-soft", "ink"), ("graft", "ink"),
             ("ink", "paper"), ("strain-deep", "paper"), ("strain", "paper"), ("graft-deep", "paper"),
             ("bone", "pill"), ("strain-soft", "pill"), ("ink", "strain"), ("bone", "strain")]
    lines = ["| Text | On | Ratio | Use |", "|---|---|---|---|"]
    for fg, bg in pairs:
        ratio = contrast(C[fg], C[bg])
        use = "any text" if ratio >= 7 else "body text" if ratio >= 4.5 else "large text, UI" if ratio >= 3 else "decoration only"
        lines.append(f"| {fg} `{C[fg]}` | {bg} `{C[bg]}` | {ratio:.1f}:1 | {use} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="command")
    sub.add_parser("all", help="every asset into docs/pokerom/brand and docs/theme (the default)")
    p = sub.add_parser("variants", help="cover-a/b/c.png into a folder, to choose from")
    p.add_argument("--out", required=True)
    p.add_argument("--size", default="1280x640")
    p = sub.add_parser("cover")
    p.add_argument("--variant", default="a", choices=sorted(COVERS))
    p.add_argument("--size", default="1280x640")
    p.add_argument("--out", required=True)
    p = sub.add_parser("titlecard")
    p.add_argument("--subtitle", default="")
    p.add_argument("--size", default="1920x1080")
    p.add_argument("--out", required=True)
    sub.add_parser("contrast")
    args = ap.parse_args()
    command = args.command or "all"

    if command == "contrast":
        print(contrast_table())
    elif command == "variants":
        for key, fn in COVERS.items():
            save(os.path.join(args.out, f"cover-{key}.png"), fn(parse_size(args.size)))
    elif command == "cover":
        save(args.out, COVERS[args.variant](parse_size(args.size)))
    elif command == "titlecard":
        save(args.out, titlecard(parse_size(args.size), args.subtitle))
    else:
        variant = os.environ.get("MUTAGEN_COVER", "a")
        write(os.path.join(BRAND, "wordmark.svg"), wordmark_svg(C["bone"]))
        write(os.path.join(BRAND, "wordmark-ink.svg"), wordmark_svg(C["ink"]))
        write(os.path.join(BRAND, "wordmark-inline.svg"), wordmark_svg("currentColor").replace("<svg ", '<svg class="wordmark" ', 1))
        write(os.path.join(BRAND, "mark.svg"), mark_svg(C["bone"], C["strain"]))
        write(os.path.join(BRAND, "mark-ink.svg"), mark_svg(C["ink"], C["strain"]))
        write(os.path.join(BRAND, "mark-inline.svg"), mark_svg("currentColor", C["strain"]).replace("<svg ", '<svg class="mark" ', 1))
        write(os.path.join(BRAND, "fork.svg"), fork_svg(C["bone"], C["strain"]))
        write(os.path.join(BRAND, "fork-inline.svg"), fork_svg("currentColor", C["strain"]).replace("<svg ", '<svg class="fork" ', 1))
        rows = word_bitmap()
        write(os.path.join(BRAND, "wordmark-path.js"),
              "// generated by tools/brand/brand.py: the MUTAGEN wordmark and the fork mark as SVG path data\n"
              f'window.MUTAGEN = {{ wordmark: {{ w: {len(rows[0])}, h: {len(rows)}, d: "{cells_to_path(bitmap_cells(rows))}" }},\n'
              f'  mark: {{ w: {MARK_W}, h: {MARK_H}, upper: "{cells_to_path(MARK["upper"])}", lower: "{cells_to_path(MARK["lower"])}" }} }};\n')
        write(os.path.join(THEME, "favicon.svg"), favicon_svg())
        save(os.path.join(THEME, "favicon.png"), icon(32))
        save(os.path.join(BRAND, "icon-192.png"), icon(192))
        save(os.path.join(BRAND, "icon-512.png"), icon(512))
        save(os.path.join(BRAND, "apple-touch-icon.png"), icon(180))
        save(os.path.join(BRAND, "cover.png"), COVERS[variant]((1280, 640)))


if __name__ == "__main__":
    main()
