#!/usr/bin/env python3
"""Voxel view of the overworld (BACKLOG DP-21): one layout as textured blocks.

Reads the decomp's own map data, nothing from a ROM: the layout's `map.bin`, its two tilesets'
`metatiles.bin`, `metatile_attributes.bin`, `tiles.png` and `palettes/NN.pal` (the Heart & Soul
tileset layout: 640 primary tiles and metatiles, 7 primary palettes, 13 in all), and the metatile
behaviours for water and doors.

Every metatile becomes a block. Passable ground is a thin slab (water too). An impassable block
joins the impassable blocks above and below it in its column into one run. Trees and bushes (the
solid blocks drawn in the ground's own palette, which buildings, cliffs and signs never are) are
not boxes: their canopy pixels stand as columns, higher the further from the canopy's edge, so
they are stepped domes with their own leaves on every face. Any other run stands as one box: a run of one
repeated metatile (a hedge, a fence, a cliff line) one level; anything else (a building: roof rows
over a wall row, the door counted in) up to three. The box's front face shows the run's own rows
stacked, bottom row at the bottom, which is the 2D art standing up, and its top faces keep each
row's own art: the look of the voxel mods for the 2D games.

    tools/voxel/export_map.py LAYOUT_NEW_BARK_TOWN_HNS out/new-bark-town.html [--png out/new-bark-town.png]
    tools/voxel/export_map.py --list | grep -i cherry
    tools/voxel/export_map.py --sweep            # every layout, to catch data this script can't read

The page draws the blocks with three.js (MIT, loaded from cdnjs) under a tilted camera with
shadows; the mouse orbits it. `serve.py` serves the same page live, following the player in mGBA.
"""
import argparse
import base64
import io
import json
import os
import re
import struct
import sys
import time

from PIL import Image, ImageChops, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NUM_TILES_IN_PRIMARY = 640
NUM_METATILES_IN_PRIMARY = 640
NUM_PALS_IN_PRIMARY = 7
NUM_PALS_TOTAL = 13
TILE = 8
METATILE = 16
ATLAS_COLUMNS = 32
MAX_LEVELS = 3        # a building's box
TREE_LEVELS = 2       # a tree's height, in blocks
SLAB_HEIGHT, LEVEL_HEIGHT = 3, 16   # the page's SLAB and LEVEL, in pixels of the map
DOME_RADIUS = 6       # pixels from the canopy's edge over which a tree rises to its full height
DOME_EDGE = 0.5       # the canopy's edge stands at this share of the tree's height
# The palette that draws the trees and bushes of a tileset: for the outdoor primary tilesets the
# one most of their over-the-player solid blocks use; for a town's own tileset, its trees' (looked
# up by hand: `metatile_palettes`). Indoor tilesets are left out, so nothing indoors is a tree.
TREE_PALETTES = {
    "gTileset_Johto_General_Hns": 0, "gTileset_Johto_NorthEast_Hns": 0, "gTileset_Johto_NorthWest_Hns": 0,
    "gTileset_Johto_South_Hns": 0, "gTileset_Kanto_General_Hns": 0, "gTileset_MtSilver_Exp_Hns": 0,
    "gTileset_AlolaIsland": 0,
    "gTileset_CherrygroveCity_Hns": 12,     # the pink flowering trees
}

# map.bin and metatile_attributes.bin bit layout (include/global.fieldmap.h)
METATILE_ID_MASK = 0x03FF
COLLISION_MASK = 0x0C00
ATTR_BEHAVIOR_MASK = 0x00FF
ATTR_LAYER_SHIFT = 12
LAYER_NORMAL, LAYER_COVERED, LAYER_SPLIT = 0, 1, 2  # top layer over the player: NORMAL and SPLIT

DIRECTIONS = {1: "south", 2: "north", 3: "west", 4: "east"}


def read_layouts():
    with open(os.path.join(ROOT, "data/layouts/layouts.json")) as f:
        return {layout["id"]: layout for layout in json.load(f)["layouts"]}


_map_index = None


def map_index():
    """(map group, map number) -> {"id", "name", "layout"} from data/maps."""
    global _map_index
    if _map_index is None:
        with open(os.path.join(ROOT, "data/maps/map_groups.json")) as f:
            groups = json.load(f)
        _map_index = {}
        for gi, gname in enumerate(groups["group_order"]):
            for mi, name in enumerate(groups[gname]):
                path = os.path.join(ROOT, "data/maps", name, "map.json")
                if not os.path.exists(path):
                    continue
                with open(path) as f:
                    m = json.load(f)
                _map_index[(gi, mi)] = {"id": m["id"], "name": name, "layout": m["layout"]}
    return _map_index


_behaviors = None


def behaviors():
    """Metatile behaviour name -> value, from the enum in include/constants/metatile_behaviors.h."""
    global _behaviors
    if _behaviors is None:
        _behaviors = {}
        value = 0
        inside = False
        with open(os.path.join(ROOT, "include/constants/metatile_behaviors.h")) as f:
            for line in f:
                line = line.split("//")[0].strip()
                if line.startswith("enum"):
                    inside = True
                    continue
                if not inside or not line or line.startswith("}"):
                    continue
                name = line.rstrip(",").strip()
                if "=" in name:
                    name, rhs = (p.strip() for p in name.split("=", 1))
                    value = int(rhs, 0)
                _behaviors[name] = value
                value += 1
    return _behaviors


def behavior_set(pattern):
    return {v for k, v in behaviors().items() if re.search(pattern, k)}


TILESET_SOURCES = ("src/data/tilesets/graphics.h", "src/graphics.c")  # Heart & Soul's, then Emerald's


_tiles_symbols = None


def tiles_symbol(symbol):
    """gTileset_X -> the symbol its header's .tiles names (gTilesetTiles_Building_Frlg for
    gTileset_BuildingFrlg, say), from src/data/tilesets/headers.h."""
    global _tiles_symbols
    if _tiles_symbols is None:
        with open(os.path.join(ROOT, "src/data/tilesets/headers.h")) as f:
            text = f.read()
        _tiles_symbols = {
            m.group(1): m.group(2)
            for m in re.finditer(r"struct Tileset (gTileset_\w+)\s*=\s*\{[^}]*?\.tiles\s*=\s*(\w+)", text)
        }
    return _tiles_symbols.get(symbol, "gTilesetTiles_" + symbol[len("gTileset_"):])


def tileset_dir(symbol):
    """gTileset_NewBarkTown_Hns -> (data/tilesets/secondary/new_bark_town_hns, the same), from the
    INCBIN of its tiles. The secret-base tilesets keep only their tiles in their own folder and
    share the metatiles of the folder above, so the folders come back as (metatiles, tiles)."""
    needle = f"{tiles_symbol(symbol)}[]"
    for source in TILESET_SOURCES:
        with open(os.path.join(ROOT, source)) as f:
            for line in f:
                if needle in line:
                    match = re.search(r'INCBIN_U32\("([^"]+)"\)', line)
                    if match:
                        directory = os.path.join(ROOT, os.path.dirname(match.group(1)))
                        if not os.path.exists(os.path.join(directory, "metatiles.bin")):
                            return os.path.dirname(directory), directory
                        return directory, directory
    raise ValueError(f"no INCBIN for {needle} in {' or '.join(TILESET_SOURCES)}")


def read_palette(path):
    with open(path) as f:
        lines = [line.strip() for line in f]
    if lines[0] != "JASC-PAL":
        raise ValueError(f"{path} is not a JASC palette")
    count = int(lines[2])
    return [tuple(int(v) for v in lines[3 + i].split()[:3]) for i in range(count)]


class Tileset:
    def __init__(self, directory, tiles_dir=None):
        self.directory = directory
        self.tiles = Image.open(os.path.join(tiles_dir or directory, "tiles.png")).convert("P")
        with open(os.path.join(directory, "metatiles.bin"), "rb") as f:
            data = f.read()
        self.metatiles = [struct.unpack_from("<8H", data, i) for i in range(0, len(data) - 15, 16)]
        with open(os.path.join(directory, "metatile_attributes.bin"), "rb") as f:
            data = f.read()
        self.attributes = list(struct.unpack(f"<{len(data) // 2}H", data[: len(data) // 2 * 2]))
        self._tile_cache = {}

    def tile_indices(self, tile):
        """The 8x8 colour indices of one tile of this tileset's sheet (blank past the sheet)."""
        if tile in self._tile_cache:
            return self._tile_cache[tile]
        per_row = self.tiles.width // TILE
        x = (tile % per_row) * TILE
        y = (tile // per_row) * TILE
        if y + TILE > self.tiles.height:
            image = Image.new("P", (TILE, TILE), 0)
        else:
            image = self.tiles.crop((x, y, x + TILE, y + TILE))
        self._tile_cache[tile] = image
        return image


_tileset_cache = {}


def tileset(symbol):
    if symbol not in _tileset_cache:
        directory, tiles_dir = tileset_dir(symbol)
        _tileset_cache[symbol] = Tileset(directory, tiles_dir)
    return _tileset_cache[symbol]


def load_palettes(primary, secondary):
    palettes = []
    for n in range(NUM_PALS_TOTAL):
        source = primary if n < NUM_PALS_IN_PRIMARY else secondary
        path = os.path.join(source.directory, "palettes", f"{n:02}.pal")
        palettes.append(read_palette(path) if os.path.exists(path) else [(0, 0, 0)] * 16)
    while len(palettes) < 16:
        palettes.append([(0, 0, 0)] * 16)
    return palettes


def draw_tile(canvas, tileset_for, palettes, entry, x, y):
    """Blit one 8x8 tile entry of a metatile; colour 0 stays transparent. -> opaque pixel count."""
    tile = entry & 0x3FF
    hflip = (entry >> 10) & 1
    vflip = (entry >> 11) & 1
    palette = palettes[(entry >> 12) & 0xF]
    source, local = tileset_for(tile)
    indices = source.tile_indices(local)
    if hflip:
        indices = indices.transpose(Image.FLIP_LEFT_RIGHT)
    if vflip:
        indices = indices.transpose(Image.FLIP_TOP_BOTTOM)
    pixels = indices.load()
    opaque = 0
    for ty in range(TILE):
        for tx in range(TILE):
            index = pixels[tx, ty]
            if index:
                canvas.putpixel((x + tx, y + ty), palette[index] + (255,))
                opaque += 1
    return opaque


def compose_metatile(primary, secondary, palettes, metatile_id):
    """-> (16x16 RGBA image, the top layer's mask (an L image, 255 where it has pixels), layer type,
    behaviour)."""
    if metatile_id < NUM_METATILES_IN_PRIMARY:
        source, local = primary, metatile_id
    else:
        source, local = secondary, metatile_id - NUM_METATILES_IN_PRIMARY
    blank = Image.new("RGBA", (METATILE, METATILE), (0, 0, 0, 0))
    if local >= len(source.metatiles):
        return blank, Image.new("L", (METATILE, METATILE), 0), LAYER_NORMAL, 0
    entries = source.metatiles[local]
    attributes = source.attributes[local] if local < len(source.attributes) else 0
    layer_type = (attributes >> ATTR_LAYER_SHIFT) & 0x3
    behavior = attributes & ATTR_BEHAVIOR_MASK

    def tileset_for(tile):
        if tile < NUM_TILES_IN_PRIMARY:
            return primary, tile
        return secondary, tile - NUM_TILES_IN_PRIMARY

    canvas = blank
    top = Image.new("RGBA", (METATILE, METATILE), (0, 0, 0, 0))
    positions = [(0, 0), (TILE, 0), (0, TILE), (TILE, TILE)]
    for i, (x, y) in enumerate(positions):
        draw_tile(canvas, tileset_for, palettes, entries[i], x, y)
        draw_tile(top, tileset_for, palettes, entries[4 + i], x, y)
    canvas.alpha_composite(top)
    return canvas, top.getchannel("A").point(lambda a: 255 if a else 0), layer_type, behavior


def metatile_palettes(primary, secondary, metatile_id):
    """-> (palettes of the bottom layer's tiles, of the top layer's), blank tiles left out."""
    if metatile_id < NUM_METATILES_IN_PRIMARY:
        source, local = primary, metatile_id
    else:
        source, local = secondary, metatile_id - NUM_METATILES_IN_PRIMARY
    if local >= len(source.metatiles):
        return set(), set()
    entries = source.metatiles[local]
    return ({(e >> 12) & 0xF for e in entries[:4] if e & 0x3FF},
            {(e >> 12) & 0xF for e in entries[4:] if e & 0x3FF})


def tree_relief(width, height, tree_blocks, ids, masks):
    """Per-pixel heights for the tree blocks: the canopy's own pixels (the top layer's, or the whole
    block where the canopy sits in the bottom layer) stand as columns, higher the further they are
    from the canopy's edge, so trees come out as stepped domes instead of boxes.
    -> [[block index, base64 of 256 height bytes (0 = no column)], ...]"""
    if not tree_blocks:
        return []
    mask = Image.new("L", (width * METATILE, height * METATILE), 0)
    full = Image.new("L", (METATILE, METATILE), 255)
    for i in tree_blocks:
        m = masks[ids[i]]
        mask.paste(m if m.getbbox() else full, ((i % width) * METATILE, (i // width) * METATILE))
    inside = mask.point(lambda v: 1 if v else 0)
    distance = inside
    eroded = mask
    for _ in range(DOME_RADIUS - 1):
        eroded = eroded.filter(ImageFilter.MinFilter(3))
        distance = ImageChops.add(distance, eroded.point(lambda v: 1 if v else 0))
    span = LEVEL_HEIGHT * TREE_LEVELS
    table = [0] + [SLAB_HEIGHT + round(span * (DOME_EDGE + (1 - DOME_EDGE) * (d - 1) / (DOME_RADIUS - 1)))
                   for d in range(1, DOME_RADIUS + 1)]
    heights = distance.point(lambda d: table[min(d, DOME_RADIUS)])
    out = []
    for i in sorted(tree_blocks):
        x, y = (i % width) * METATILE, (i // width) * METATILE
        out.append([i, base64.b64encode(heights.crop((x, y, x + METATILE, y + METATILE)).tobytes()).decode("ascii")])
    return out


def build_scene(layout_id):
    """-> (scene dict for the page, atlas PNG bytes, metatile images, blocks).

    blocks[i] = (atlas cell, levels, stack): stack is the list of atlas cells the block's front
    face shows from the bottom up when it is the bottom of a run, else None."""
    layouts = read_layouts()
    if layout_id not in layouts:
        raise KeyError(f"no layout {layout_id} (try --list)")
    layout = layouts[layout_id]
    width, height = layout["width"], layout["height"]
    primary = tileset(layout["primary_tileset"])
    secondary = tileset(layout["secondary_tileset"])
    palettes = load_palettes(primary, secondary)
    with open(os.path.join(ROOT, layout["blockdata_filepath"]), "rb") as f:
        data = f.read(width * height * 2)
    grid = struct.unpack(f"<{len(data) // 2}H", data)
    grid = grid + (0,) * (width * height - len(grid))
    flat = behavior_set(r"WATER|CURRENT|WATERFALL|PUDDLE|DIVE")
    doors = behavior_set(r"DOOR")

    cells = {}      # metatile id -> (atlas cell, flat, door, pixels over the player)
    masks = {}      # metatile id -> the top layer's mask
    pals = {}       # metatile id -> (bottom layer's palettes, top layer's)
    images = []
    solid = []      # per block: impassable (or a door)
    ids = []
    for value in grid:
        metatile_id = value & METATILE_ID_MASK
        if metatile_id not in cells:
            image, top_mask, layer_type, behavior = compose_metatile(primary, secondary, palettes, metatile_id)
            cells[metatile_id] = (len(images), behavior in flat, behavior in doors,
                                  top_mask.getbbox() is not None and layer_type != LAYER_COVERED)
            masks[metatile_id] = top_mask
            pals[metatile_id] = metatile_palettes(primary, secondary, metatile_id)
            images.append(image)
        cell, is_flat, is_door, _ = cells[metatile_id]
        solid.append(((value & COLLISION_MASK) != 0 and not is_flat) or is_door)
        ids.append(metatile_id)

    # Trees and bushes are drawn in one palette of their tileset (TREE_PALETTES), which buildings,
    # cliffs, signs and poles never use alone: a solid block whose drawn layer uses that palette
    # alone is vegetation, and stands as a dome of its pixels (tree_relief).
    tree_palettes = (TREE_PALETTES.get(layout["primary_tileset"]), TREE_PALETTES.get(layout["secondary_tileset"]))

    def is_tree(metatile_id):
        bottom, top = pals[metatile_id]
        palette = tree_palettes[0 if metatile_id < NUM_METATILES_IN_PRIMARY else 1]
        return palette is not None and (top or bottom) == {palette}

    tree_blocks = {i for i in range(width * height) if solid[i] and is_tree(ids[i])}

    runs = []       # each a column's run of solid, non-tree blocks, north to south
    for x in range(width):
        y = 0
        while y < height:
            i = y * width + x
            if not solid[i] or i in tree_blocks:
                y += 1
                continue
            start = y
            while y < height and solid[y * width + x] and (y * width + x) not in tree_blocks:
                y += 1
            runs.append([row * width + x for row in range(start, y)])

    levels = [0] * (width * height)
    stacks = [None] * (width * height)
    for i in tree_blocks:
        levels[i] = TREE_LEVELS
    for run in runs:
        run_ids = {ids[i] for i in run}
        if any(cells[ids[i]][3] for i in run):
            lv = TREE_LEVELS                # over-the-player pixels (a roof): a tall box
        elif len(run_ids) == 1:
            lv = 1                          # a hedge, a fence, a cliff line
        else:
            lv = min(len(run), MAX_LEVELS)  # a building: roof rows over a wall row
        stack = [cells[ids[i]][0] for i in reversed(run)][:lv]   # the run's rows, bottom row first
        for i in run:
            levels[i] = lv
            stacks[i] = stack                                     # every side of the box shows them

    blocks = []
    for i, metatile_id in enumerate(ids):
        blocks.append((cells[metatile_id][0], levels[i], stacks[i]))

    rows = (len(images) + ATLAS_COLUMNS - 1) // ATLAS_COLUMNS
    atlas = Image.new("RGBA", (ATLAS_COLUMNS * METATILE, max(rows, 1) * METATILE), (0, 0, 0, 0))
    for i, image in enumerate(images):
        atlas.paste(image, ((i % ATLAS_COLUMNS) * METATILE, (i // ATLAS_COLUMNS) * METATILE))
    buffer = io.BytesIO()
    atlas.save(buffer, format="PNG")

    scene = {
        "layout": layout_id,
        "name": layout["name"].replace("_Layout", ""),
        "width": width,
        "height": height,
        "atlasColumns": ATLAS_COLUMNS,
        "atlasRows": max(rows, 1),
        "blocks": [[c, l, s] for c, l, s in blocks],
        "relief": tree_relief(width, height, tree_blocks, ids, masks),
    }
    return scene, buffer.getvalue(), images, blocks


def render_page(title, scene=None, atlas_png=None, live=False):
    scene_json = json.dumps(scene, separators=(",", ":")) if scene else "null"
    atlas = "data:image/png;base64," + base64.b64encode(atlas_png).decode("ascii") if atlas_png else ""
    return (TEMPLATE.replace("__TITLE__", title)
            .replace("__LIVE__", "true" if live else "false")
            .replace("__SCENE__", scene_json)
            .replace("__ATLAS__", atlas))


def export(layout_id, out_path):
    scene, atlas_png, images, blocks = build_scene(layout_id)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(render_page(scene["name"], scene, atlas_png))
    raised = sum(1 for _, l, _ in blocks if l)
    print(f"export_map: {layout_id} {scene['width']}x{scene['height']}, {len(images)} metatiles drawn, "
          f"{raised} raised blocks -> {out_path}")
    return images, blocks, scene["width"], scene["height"]


def sweep():
    """Build every layout once; print the ones this script can't read."""
    ok, failed = 0, []
    started = time.time()
    for layout_id in read_layouts():
        try:
            build_scene(layout_id)
            ok += 1
        except Exception as e:  # noqa: BLE001 - a sweep reports, it doesn't stop
            failed.append((layout_id, f"{type(e).__name__}: {e}"))
    print(f"export_map: {ok} layouts built, {len(failed)} failed, {time.time() - started:.0f} s")
    for layout_id, why in failed:
        print(f"  {layout_id}: {why}")
    return 1 if failed else 0


SLAB_PX = 3    # a passable block's thickness, in pixels of the 16-pixel grid
LEVEL_PX = 16  # one level of height


def shade(image, factor):
    r, g, b, a = image.split()
    table = [min(255, int(v * factor)) for v in range(256)]
    return Image.merge("RGBA", (r.point(table), g.point(table), b.point(table), a))


def column_image(images, cell, stack, h):
    """The 16 x h texture of a block's side: the run's rows stacked when it has a stack, else the
    block's own art stretched."""
    if not stack:
        return images[cell].resize((16, h), Image.NEAREST)
    column = Image.new("RGBA", (16, h), (0, 0, 0, 0))
    for i, c in enumerate(stack):
        column.paste(images[c], (0, h - SLAB_PX - (i + 1) * LEVEL_PX))
    column.paste(images[stack[0]].crop((0, 16 - SLAB_PX, 16, 16)), (0, h - SLAB_PX))
    return column


def render_png(images, blocks, width, height, path, scale=2):
    """The same scene as a 2:1 isometric picture, no browser needed: back to front, each block's
    top face and its two faces towards the viewer (south and east), the sides darker."""
    max_h = SLAB_PX + MAX_LEVELS * LEVEL_PX
    canvas = Image.new("RGBA", ((width + height) * 16, (width + height) * 8 + max_h + 16), (11, 15, 26, 255))
    top_faces = {}
    for i, image in enumerate(images):
        # top: (u, v) -> X = u - v + 16, Y = (u + v) / 2; AFFINE takes the inverse
        top_faces[i] = image.transform((32, 16), Image.AFFINE, (0.5, 1, -8, -0.5, 1, 8), Image.NEAREST)
    for s in range(width + height - 1):
        for x in range(max(0, s - height + 1), min(width, s + 1)):
            y = s - x
            cell, levels, stack = blocks[y * width + x]
            h = SLAB_PX + levels * LEVEL_PX
            rx = (x - y) * 16 + (height - 1) * 16
            ry = (x + y) * 8 + max_h - h
            # south face: X in 0..16, texture (s, t) = (X, Y - X/2)
            south = column_image(images, cell, stack, h).transform((16, h + 8), Image.AFFINE, (1, 0, 0, -0.5, 1, 0), Image.NEAREST)
            canvas.alpha_composite(shade(south, 0.78), (rx, ry + 8))
            # east face: X in 0..16 (screen 16..32), texture (s, t) = (16 - X, Y - 8 + X/2)
            east = images[cell].resize((16, h), Image.NEAREST).transform((16, h + 8), Image.AFFINE, (-1, 0, 16, 0.5, 1, -8), Image.NEAREST)
            canvas.alpha_composite(shade(east, 0.6), (rx + 16, ry + 8))
            canvas.alpha_composite(top_faces[cell], (rx, ry))
    if scale != 1:
        canvas = canvas.resize((canvas.width * scale, canvas.height * scale), Image.NEAREST)
    canvas.convert("RGB").save(path)
    print(f"export_map: isometric picture {canvas.width}x{canvas.height} -> {path}")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ · voxel view</title>
<style>
  html, body { margin: 0; height: 100%; background: #0b0f1a; color: #dfe6f3; font: 14px system-ui, sans-serif; overflow: hidden; }
  canvas { display: block; }
  #hud { position: fixed; left: 12px; top: 10px; background: rgba(11,15,26,.72); padding: 8px 10px; border-radius: 8px; line-height: 1.5; }
  #hud b { color: #fff; }
  #hud .dim { color: #9aa7bd; }
</style>
</head>
<body>
<div id="hud"><b id="title">__TITLE__</b><span id="status"></span><br><span class="dim">drag to orbit · wheel to zoom · right-drag to pan · F follows the player</span></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const LIVE = __LIVE__;
const RECORD = LIVE && new URLSearchParams(location.search).has("record");  // ?record: render the demo walk for the video
const SIZE = 16, LEVEL = 16, SLAB = 3;
const VIDEO_WIDTH = 1920, VIDEO_HEIGHT = 1080;
const FOLLOW_OFFSET = [130, 220, 280];   // the camera from the player when a map opens in the video
let scene3, renderer, camera, controls, sun, mapMesh = null, mapTexture = null, current = null, heights = null;
let follow = LIVE, marker = null, lastState = null, lastSeen = 0, textureReady = Promise.resolve();

function heightAt(sc, x, y) {
  x = Math.round(x); y = Math.round(y);   // the demo walk puts the player between tiles
  if (x < 0 || y < 0 || x >= sc.width || y >= sc.height) return 0;
  return heights[y * sc.width + x];
}

// One merged mesh: for every block the top face and the side faces a lower neighbour leaves open;
// a tree block is a slab under per-pixel columns (sc.relief: 256 heights a block, 0 = no column).
function buildGeometry(sc) {
  const relief = new Map();
  for (const [i, b64] of sc.relief || []) relief.set(i, Uint8Array.from(atob(b64), c => c.charCodeAt(0)));
  heights = sc.blocks.map((b, i) => relief.has(i) ? SLAB : SLAB + b[1] * LEVEL);
  const positions = [], normals = [], uvs = [], indices = [];
  const cw = 1 / sc.atlasColumns, ch = 1 / sc.atlasRows, pw = cw / SIZE, ph = ch / SIZE;
  function cellUV(cell) {
    return [(cell % sc.atlasColumns) * cw, 1 - Math.floor(cell / sc.atlasColumns) * ch];
  }
  // p: top-left, top-right, bottom-right, bottom-left as seen from outside; uv: that corner order
  function face(p, n, uv) {
    const base = positions.length / 3;
    for (let i = 0; i < 4; i++) { positions.push(...p[i]); normals.push(...n); }
    uvs.push(...uv);
    indices.push(base, base + 2, base + 1, base, base + 3, base + 2);
  }
  // a block face showing the cell's art; v0..v1: the cell's v span to show
  function quad(p, n, cell, vTop = 1, vBottom = 0) {
    const [u0, v0] = cellUV(cell);
    const top = v0 - ch * (1 - vTop), bottom = v0 - ch * (1 - vBottom);
    face(p, n, [u0, top, u0 + cw, top, u0 + cw, bottom, u0, bottom]);
  }
  // the height of the map at one of its pixels: a tree's column, else its block's top
  function pixelHeight(gx, gy) {
    if (gx < 0 || gy < 0 || gx >= sc.width * SIZE || gy >= sc.height * SIZE) return 0;
    const i = (gy >> 4) * sc.width + (gx >> 4), r = relief.get(i);
    if (r) return r[(gy & 15) * SIZE + (gx & 15)] || SLAB;
    return heights[i];
  }
  for (const [i, r] of relief) {
    const bx = (i % sc.width) * SIZE, by = Math.floor(i / sc.width) * SIZE;
    const [u0, v0] = cellUV(sc.blocks[i][0]);
    for (let py = 0; py < SIZE; py++) {
      const z0 = by + py, z1 = z0 + 1, va = v0 - py * ph, vb = va - ph;
      for (let px = 0; px < SIZE;) {
        const h = r[py * SIZE + px];
        if (!h) { px++; continue; }
        let end = px + 1;
        while (end < SIZE && r[py * SIZE + end] === h) end++;
        const x0 = bx + px, x1 = bx + end, ua = u0 + px * pw, ub = u0 + end * pw;
        face([[x0, h, z0], [x1, h, z0], [x1, h, z1], [x0, h, z1]], [0, 1, 0], [ua, va, ub, va, ub, vb, ua, vb]);
        for (let k = px; k < end; k++) {   // the walls down to each lower neighbour, in the pixel's own colour
          const gx = bx + k, uc = u0 + (k + 0.5) * pw, vc = va - ph / 2, flat = [uc, vc, uc, vc, uc, vc, uc, vc];
          const s = pixelHeight(gx, z1), n = pixelHeight(gx, z0 - 1);
          if (s < h) face([[gx, h, z1], [gx + 1, h, z1], [gx + 1, s, z1], [gx, s, z1]], [0, 0, 1], flat);
          if (n < h) face([[gx + 1, h, z0], [gx, h, z0], [gx, n, z0], [gx + 1, n, z0]], [0, 0, -1], flat);
          if (k === end - 1) { const e = pixelHeight(gx + 1, z0); if (e < h) face([[gx + 1, h, z1], [gx + 1, h, z0], [gx + 1, e, z0], [gx + 1, e, z1]], [1, 0, 0], flat); }
          if (k === px) { const w = pixelHeight(gx - 1, z0); if (w < h) face([[gx, h, z0], [gx, h, z1], [gx, w, z1], [gx, w, z0]], [-1, 0, 0], flat); }
        }
        px = end;
      }
    }
  }
  for (let y = 0; y < sc.height; y++) for (let x = 0; x < sc.width; x++) {
    const [cell, levels, stack] = sc.blocks[y * sc.width + x];
    const h = heights[y * sc.width + x];
    const x0 = x * SIZE, x1 = x0 + SIZE, z0 = y * SIZE, z1 = z0 + SIZE;
    quad([[x0, h, z0], [x1, h, z0], [x1, h, z1], [x0, h, z1]], [0, 1, 0], cell);
    // a side of the box, from the ground to h, between its outside-left and outside-right corners: the
    // run's rows standing up (bottom row at the bottom, the slab under it), so the 2D art is the wall
    const boxed = stack && stack.length && !relief.has(y * sc.width + x);
    function wall(l, r, n) {
      if (!boxed) { quad([[l[0], h, l[1]], [r[0], h, r[1]], [r[0], 0, r[1]], [l[0], 0, l[1]]], n, cell); return; }
      quad([[l[0], SLAB, l[1]], [r[0], SLAB, r[1]], [r[0], 0, r[1]], [l[0], 0, l[1]]], n, stack[0], SLAB / 16, 0);
      for (let i = 0; i < stack.length; i++) {
        const a = SLAB + i * LEVEL, b = a + LEVEL;
        quad([[l[0], b, l[1]], [r[0], b, r[1]], [r[0], a, r[1]], [l[0], a, l[1]]], n, stack[i]);
      }
    }
    if (heightAt(sc, x, y + 1) < h) wall([x0, z1], [x1, z1], [0, 0, 1]);    // south: the front
    if (heightAt(sc, x, y - 1) < h) wall([x1, z0], [x0, z0], [0, 0, -1]);   // north
    if (heightAt(sc, x + 1, y) < h) wall([x1, z1], [x1, z0], [1, 0, 0]);    // east
    if (heightAt(sc, x - 1, y) < h) wall([x0, z0], [x0, z1], [-1, 0, 0]);   // west
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  geometry.setIndex(indices);
  return geometry;
}

function setScene(sc, atlasUrl, recenter) {
  if (mapMesh) { scene3.remove(mapMesh); mapMesh.geometry.dispose(); mapMesh.material.dispose(); }
  if (mapTexture) mapTexture.dispose();
  current = sc;
  textureReady = new Promise(resolve => { mapTexture = new THREE.TextureLoader().load(atlasUrl, resolve, undefined, resolve); });
  mapTexture.magFilter = THREE.NearestFilter;
  mapTexture.minFilter = THREE.NearestFilter;
  mapMesh = new THREE.Mesh(buildGeometry(sc), new THREE.MeshLambertMaterial({ map: mapTexture }));
  mapMesh.castShadow = mapMesh.receiveShadow = true;
  scene3.add(mapMesh);
  const W = sc.width * SIZE, D = sc.height * SIZE;
  sun.position.set(W * 0.2, 420, D * 0.9);
  sun.target.position.set(W / 2, 0, D / 2);
  const c = sun.shadow.camera; c.left = -W; c.right = W; c.top = D; c.bottom = -D; c.updateProjectionMatrix();
  document.getElementById("title").textContent = sc.name;
  if (recenter) {
    camera.position.set(W / 2, Math.max(W, D) * 0.9, D * 1.35);
    controls.target.set(W / 2, 0, D / 2);
    controls.update();
  }
}

function makeMarker() {
  const group = new THREE.Group();
  const body = new THREE.Mesh(new THREE.BoxGeometry(10, 14, 10), new THREE.MeshLambertMaterial({ color: 0xff5c5c }));
  body.position.y = 7; body.castShadow = true;
  const nose = new THREE.Mesh(new THREE.ConeGeometry(4, 8, 4), new THREE.MeshLambertMaterial({ color: 0xffe08a }));
  nose.rotation.x = Math.PI / 2; nose.position.set(0, 7, 9);
  group.add(body, nose);
  return group;
}

function placeMarker(st) {
  if (!current || !marker) return;
  const h = heightAt(current, st.x, st.y);
  marker.position.set(st.x * SIZE + 8, h, st.y * SIZE + 8);
  marker.rotation.y = { 1: 0, 2: Math.PI, 3: -Math.PI / 2, 4: Math.PI / 2 }[st.dir] || 0;   // the nose starts south (+z); +y turns it toward +x (east)
  marker.visible = true;
}

async function poll() {
  try {
    const st = await (await fetch("/state", { cache: "no-store" })).json();
    lastSeen = Date.now();
    if (!st.layout) { document.getElementById("status").textContent = " · waiting for mGBA"; return; }
    if (!current || current.layout !== st.layout) {
      const sc = await (await fetch(`/scene/${st.group}/${st.num}`, { cache: "no-store" })).json();
      setScene(sc, sc.atlas, true);
    }
    lastState = st;
    placeMarker(st);
    document.getElementById("status").textContent = ` · ${st.map} (${st.x}, ${st.y}) ${st.facing}${follow ? " · following" : ""}`;
  } catch (e) {
    document.getElementById("status").textContent = " · server away";
  }
}

function init() {
  scene3 = new THREE.Scene();
  scene3.background = new THREE.Color(0x0b0f1a);
  scene3.add(new THREE.HemisphereLight(0xcfe3ff, 0x30261a, 0.6));
  sun = new THREE.DirectionalLight(0xfff1d6, 0.95);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.near = 10; sun.shadow.camera.far = 1500;
  scene3.add(sun, sun.target);
  renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(innerWidth, innerHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  document.body.appendChild(renderer.domElement);
  camera = new THREE.PerspectiveCamera(42, innerWidth / innerHeight, 1, 6000);
  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.maxPolarAngle = Math.PI / 2 - 0.05;
  marker = makeMarker(); marker.visible = false; scene3.add(marker);
  addEventListener("resize", () => {
    if (RECORD) return;
    camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight);
  });
  addEventListener("keydown", e => { if (e.key === "f" || e.key === "F") follow = !follow; });
  const SCENE = __SCENE__;
  if (SCENE) setScene(SCENE, "__ATLAS__", true);
  if (RECORD) { record(); return; }
  if (LIVE) { poll(); setInterval(poll, 100); }
  (function frame() {
    followStep();
    controls.update();
    renderer.render(scene3, camera);
    requestAnimationFrame(frame);
  })();
}

function followStep() {
  if (follow && lastState && marker.visible) {
    const offset = new THREE.Vector3().subVectors(camera.position, controls.target);
    controls.target.lerp(marker.position, 0.12);
    camera.position.copy(controls.target).add(offset);
  }
}

// The demo video (tools/voxel/record.py): the page draws the server's /demo walk one frame at a time
// at the video's size, each time record.py calls demoStep(k) over DevTools and takes a screenshot.
async function record() {
  const demo = await (await fetch("/demo", { cache: "no-store" })).json();
  document.getElementById("hud").hidden = true;   // the map's name goes on in ffmpeg
  renderer.setPixelRatio(1);
  renderer.setSize(VIDEO_WIDTH, VIDEO_HEIGHT);
  camera.aspect = VIDEO_WIDTH / VIDEO_HEIGHT; camera.updateProjectionMatrix();
  controls.autoRotate = true; controls.autoRotateSpeed = 1.5;   // a slow turn around the player
  follow = true;
  let map = null;
  window.demoFrames = demo.frames.length;
  window.demoStep = async k => {
    const [group, num, x, y, dir] = demo.frames[k];
    const st = { group, num, x, y, dir };
    if (map !== `${group}/${num}`) {
      const sc = await (await fetch(`/scene/${group}/${num}`, { cache: "no-store" })).json();
      setScene(sc, sc.atlas, false);
      await textureReady;
      lastState = st; placeMarker(st);
      // the camera keeps its angle from the last map and opens on the player
      const offset = map === null ? new THREE.Vector3(...FOLLOW_OFFSET) : new THREE.Vector3().subVectors(camera.position, controls.target);
      controls.target.copy(marker.position);
      camera.position.copy(marker.position).add(offset);
      map = `${group}/${num}`;
    }
    lastState = st; placeMarker(st);
    followStep();
    controls.update();
    renderer.render(scene3, camera);
    return k;
  };
  document.title = "ready";
}
init();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("layout", nargs="?", help="a LAYOUT_* id from data/layouts/layouts.json")
    ap.add_argument("out", nargs="?", help="the .html to write")
    ap.add_argument("--list", action="store_true", help="print every layout id")
    ap.add_argument("--sweep", action="store_true", help="build every layout, report the ones that fail")
    ap.add_argument("--png", help="also draw the scene as an isometric PNG at this path")
    args = ap.parse_args()
    if args.list:
        for layout_id in read_layouts():
            print(layout_id)
        return 0
    if args.sweep:
        return sweep()
    if not args.layout or not args.out:
        ap.error("layout and out are required (or --list / --sweep)")
    try:
        images, blocks, width, height = export(args.layout, args.out)
    except (KeyError, ValueError) as e:
        sys.exit(f"export_map: {e}")
    if args.png:
        render_png(images, blocks, width, height, args.png)
    return 0


if __name__ == "__main__":
    sys.exit(main())
