#!/usr/bin/env python3
"""The brand's web fonts (docs/pokerom/design/brand.md): fetch, verify, subset.

    tools/brand/fonts.py            # -> docs/pokerom/brand/fonts/ (woff2 for the site, ttf for PIL and ffmpeg)

Both families are SIL Open Font License 1.1 (their OFL.txt is written next to the files):
  Space Grotesk (Florian Karsten and the project's authors), the text and heading face;
  Silkscreen (Jason Kottke and the project's authors), the small pixel labels.
The files come from google/fonts at a pinned commit and are checked against the hashes below before
anything is written, then cut down to the Latin ranges the site uses. Space Grotesk's variable file
keeps its weight axis for the web; static Regular / Medium / Bold instances are made for the tools
that cannot pick a weight on a variable font (PIL, ffmpeg's drawtext).
"""
import hashlib
import io
import os
import sys
import urllib.request

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs/pokerom/brand/fonts")
COMMIT = "5bb28733cec313b63fbd415b574b5ae35c8aa8b8"   # google/fonts main, 2026-11-08
BASE = f"https://raw.githubusercontent.com/google/fonts/{COMMIT}/ofl"
FILES = {
    # path in google/fonts: sha256
    "spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf": "acad6de1fc93436f5c0f1f4137751ef04f1aea3063e7036535970ffcfbd79f72",
    "silkscreen/Silkscreen-Regular.ttf": "c845473330b94c2079ce9af01c51ac8ba2d99c24f4d14c039843bbb8e642ebd8",
    "silkscreen/Silkscreen-Bold.ttf": "768476aa712d4f5c3e18d3bce80f980a8bd3f72b7094d22ec5e768df3acfed61",
    "spacegrotesk/OFL.txt": None,
    "silkscreen/OFL.txt": None,
}
# Basic Latin, Latin-1, Latin Extended-A, general punctuation (dashes, quotes, bullet, ellipsis),
# euro, trademark, the four arrows, multiplication sign.
UNICODES = "U+0000-00FF,U+0100-017F,U+2000-206F,U+20AC,U+2122,U+2190-2193,U+00D7"


def fetch(path, sha256):
    data = urllib.request.urlopen(BASE + "/" + path, timeout=60).read()
    if sha256 is not None:
        got = hashlib.sha256(data).hexdigest()
        if got != sha256:
            sys.exit(f"{path}: sha256 {got}, expected {sha256}; not written")
    return data


def subset_font(data, flavor=None, keep_axes=True):
    font = TTFont(io.BytesIO(data))
    options = subset.Options()
    options.layout_features = ["*"]
    options.name_IDs = ["*"]
    options.notdef_outline = True
    options.recalc_bounds = True
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=subset.parse_unicodes(UNICODES))
    subsetter.subset(font)
    font.flavor = flavor          # None keeps a TrueType file, "woff2" compresses it for the web
    out = io.BytesIO()
    font.save(out)
    return out.getvalue()


def instance(data, weight):
    font = TTFont(io.BytesIO(data))
    static = instancer.instantiateVariableFont(font, {"wght": weight}, inplace=False, updateFontNames=True)
    out = io.BytesIO()
    static.save(out)
    return out.getvalue()


def write(name, data):
    path = os.path.join(OUT, name)
    with open(path, "wb") as f:
        f.write(data)
    print(f"{os.path.relpath(path, ROOT)}  {len(data):,} B")


def main():
    os.makedirs(OUT, exist_ok=True)
    raw = {path: fetch(path, sha) for path, sha in FILES.items()}
    write("OFL-SpaceGrotesk.txt", raw["spacegrotesk/OFL.txt"])
    write("OFL-Silkscreen.txt", raw["silkscreen/OFL.txt"])
    grotesk = raw["spacegrotesk/SpaceGrotesk%5Bwght%5D.ttf"]
    write("SpaceGrotesk-Variable.woff2", subset_font(grotesk, flavor="woff2"))
    for weight, name in ((400, "Regular"), (500, "Medium"), (700, "Bold")):
        write(f"SpaceGrotesk-{name}.ttf", subset_font(instance(grotesk, weight)))
    for name in ("Regular", "Bold"):
        data = raw[f"silkscreen/Silkscreen-{name}.ttf"]
        write(f"Silkscreen-{name}.woff2", subset_font(data, flavor="woff2"))
        write(f"Silkscreen-{name}.ttf", subset_font(data))


if __name__ == "__main__":
    main()
