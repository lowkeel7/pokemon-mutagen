#!/usr/bin/env python3
"""Voxel view of one map (BACKLOG DP-21, first slice): a self-contained HTML page.

Reads the decomp's own map data, nothing from a ROM or an emulator: the layout's `map.bin`, its
two tilesets' `metatiles.bin`, `metatile_attributes.bin`, `tiles.png` and `palettes/NN.pal`
(the Heart & Soul tileset layout: 640 primary tiles and metatiles, 7 primary palettes, 13 in all).
Every metatile becomes a textured block whose height follows the map: passable ground is a thin
slab, an impassable block stands one level, and one whose over-the-player layer has pixels (trees,
roof edges, fences) stands two. The page draws the blocks with three.js (MIT, loaded from cdnjs)
under a tilted camera with shadows, and the mouse orbits it.

    tools/voxel/export_map.py LAYOUT_NEW_BARK_TOWN_HNS out/new-bark-town.html
    tools/voxel/export_map.py --list | grep -i cherry

The live sync with mGBA (map, player position, facing) is the next slice; this one proves the look.
"""
import argparse
import base64
import io
import json
import os
import re
import struct
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NUM_TILES_IN_PRIMARY = 640
NUM_METATILES_IN_PRIMARY = 640
NUM_PALS_IN_PRIMARY = 7
NUM_PALS_TOTAL = 13
TILE = 8
METATILE = 16
ATLAS_COLUMNS = 32

# map.bin and metatile_attributes.bin bit layout (include/global.fieldmap.h)
METATILE_ID_MASK = 0x03FF
COLLISION_MASK = 0x0C00
ATTR_LAYER_SHIFT = 12
LAYER_NORMAL, LAYER_COVERED, LAYER_SPLIT = 0, 1, 2  # top layer over the player: NORMAL and SPLIT


def read_layouts():
    with open(os.path.join(ROOT, "data/layouts/layouts.json")) as f:
        return {layout["id"]: layout for layout in json.load(f)["layouts"]}


def tileset_dir(symbol):
    """gTileset_NewBarkTown_Hns -> data/tilesets/secondary/new_bark_town_hns, from graphics.h."""
    suffix = symbol[len("gTileset_"):]
    needle = f"gTilesetTiles_{suffix}[]"
    with open(os.path.join(ROOT, "src/data/tilesets/graphics.h")) as f:
        for line in f:
            if needle in line:
                match = re.search(r'INCBIN_U32\("([^"]+)"\)', line)
                if match:
                    return os.path.join(ROOT, os.path.dirname(match.group(1)))
    sys.exit(f"export_map: no INCBIN for {needle} in src/data/tilesets/graphics.h")


def read_palette(path):
    with open(path) as f:
        lines = [line.strip() for line in f]
    if lines[0] != "JASC-PAL":
        sys.exit(f"export_map: {path} is not a JASC palette")
    count = int(lines[2])
    return [tuple(int(v) for v in lines[3 + i].split()) for i in range(count)]


class Tileset:
    def __init__(self, directory):
        self.directory = directory
        self.tiles = Image.open(os.path.join(directory, "tiles.png")).convert("P")
        with open(os.path.join(directory, "metatiles.bin"), "rb") as f:
            data = f.read()
        self.metatiles = [struct.unpack_from("<8H", data, i) for i in range(0, len(data), 16)]
        with open(os.path.join(directory, "metatile_attributes.bin"), "rb") as f:
            data = f.read()
        self.attributes = list(struct.unpack(f"<{len(data) // 2}H", data))

    def tile_indices(self, tile):
        """The 8x8 colour indices of one tile of this tileset's sheet."""
        x = (tile % (self.tiles.width // TILE)) * TILE
        y = (tile // (self.tiles.width // TILE)) * TILE
        return self.tiles.crop((x, y, x + TILE, y + TILE))


def load_palettes(primary, secondary):
    palettes = []
    for n in range(NUM_PALS_TOTAL):
        source = primary if n < NUM_PALS_IN_PRIMARY else secondary
        palettes.append(read_palette(os.path.join(source.directory, "palettes", f"{n:02}.pal")))
    return palettes


def draw_tile(canvas, tileset_for, palettes, entry, x, y):
    """Blit one 8x8 tile entry of a metatile; colour 0 stays transparent."""
    tile = entry & 0x3FF
    hflip = (entry >> 10) & 1
    vflip = (entry >> 11) & 1
    palette = palettes[(entry >> 12) & 0xF]
    tileset, local = tileset_for(tile)
    indices = tileset.tile_indices(local)
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
    """-> (16x16 RGBA image, top layer has pixels, layer type)."""
    if metatile_id < NUM_METATILES_IN_PRIMARY:
        tileset, local = primary, metatile_id
    else:
        tileset, local = secondary, metatile_id - NUM_METATILES_IN_PRIMARY
    if local >= len(tileset.metatiles):
        return Image.new("RGBA", (METATILE, METATILE), (0, 0, 0, 0)), False, LAYER_NORMAL
    entries = tileset.metatiles[local]
    layer_type = (tileset.attributes[local] >> ATTR_LAYER_SHIFT) & 0x3

    def tileset_for(tile):
        if tile < NUM_TILES_IN_PRIMARY:
            return primary, tile
        return secondary, tile - NUM_TILES_IN_PRIMARY

    canvas = Image.new("RGBA", (METATILE, METATILE), (0, 0, 0, 0))
    positions = [(0, 0), (TILE, 0), (0, TILE), (TILE, TILE)]
    for i, (x, y) in enumerate(positions):
        draw_tile(canvas, tileset_for, palettes, entries[i], x, y)
    top_opaque = 0
    for i, (x, y) in enumerate(positions):
        top_opaque += draw_tile(canvas, tileset_for, palettes, entries[4 + i], x, y)
    return canvas, top_opaque > 0, layer_type


def export(layout_id, out_path):
    layouts = read_layouts()
    if layout_id not in layouts:
        sys.exit(f"export_map: no layout {layout_id} (try --list)")
    layout = layouts[layout_id]
    width, height = layout["width"], layout["height"]
    primary = Tileset(tileset_dir(layout["primary_tileset"]))
    secondary = Tileset(tileset_dir(layout["secondary_tileset"]))
    palettes = load_palettes(primary, secondary)
    with open(os.path.join(ROOT, layout["blockdata_filepath"]), "rb") as f:
        grid = struct.unpack(f"<{width * height}H", f.read(width * height * 2))

    # One atlas cell per distinct metatile, in first-seen order
    cells = {}
    images = []
    blocks = []
    for value in grid:
        metatile_id = value & METATILE_ID_MASK
        if metatile_id not in cells:
            image, top_opaque, layer_type = compose_metatile(primary, secondary, palettes, metatile_id)
            cells[metatile_id] = (len(images), top_opaque, layer_type)
            images.append(image)
        cell, top_opaque, layer_type = cells[metatile_id]
        impassable = (value & COLLISION_MASK) != 0
        levels = (1 if impassable else 0) + (1 if top_opaque and layer_type != LAYER_COVERED else 0)
        blocks.append((cell, levels))

    rows = (len(images) + ATLAS_COLUMNS - 1) // ATLAS_COLUMNS
    atlas = Image.new("RGBA", (ATLAS_COLUMNS * METATILE, rows * METATILE), (0, 0, 0, 0))
    for i, image in enumerate(images):
        atlas.paste(image, ((i % ATLAS_COLUMNS) * METATILE, (i // ATLAS_COLUMNS) * METATILE))
    buffer = io.BytesIO()
    atlas.save(buffer, format="PNG")
    atlas_b64 = base64.b64encode(buffer.getvalue()).decode("ascii")

    scene = {
        "layout": layout_id,
        "width": width,
        "height": height,
        "atlasColumns": ATLAS_COLUMNS,
        "atlasRows": rows,
        "blocks": blocks,
    }
    page = TEMPLATE.replace("__TITLE__", layout["name"].replace("_Layout", "")) \
                   .replace("__SCENE__", json.dumps(scene, separators=(",", ":"))) \
                   .replace("__ATLAS__", atlas_b64)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page)
    print(f"export_map: {layout_id} {width}x{height}, {len(images)} metatiles drawn, "
          f"{sum(1 for _, l in blocks if l)} raised blocks -> {out_path}")
    return images, blocks, width, height


SLAB_PX = 3    # a passable block's thickness, in pixels of the 16-pixel grid
LEVEL_PX = 16  # one level of height


def shade(image, factor):
    r, g, b, a = image.split()
    table = [min(255, int(v * factor)) for v in range(256)]
    return Image.merge("RGBA", (r.point(table), g.point(table), b.point(table), a))


def render_png(images, blocks, width, height, path, scale=2):
    """The same scene as a 2:1 isometric picture, no browser needed: back to front, each block's
    top face and its two faces towards the viewer (south and east), the sides darker."""
    max_h = SLAB_PX + 2 * LEVEL_PX
    canvas = Image.new("RGBA", ((width + height) * 16, (width + height) * 8 + max_h + 16), (11, 15, 26, 255))
    top_faces = {}
    for i, image in enumerate(images):
        # top: (u, v) -> X = u - v + 16, Y = (u + v) / 2; AFFINE takes the inverse
        top_faces[i] = image.transform((32, 16), Image.AFFINE, (0.5, 1, -8, -0.5, 1, 8), Image.NEAREST)
    for s in range(width + height - 1):
        for x in range(max(0, s - height + 1), min(width, s + 1)):
            y = s - x
            cell, levels = blocks[y * width + x]
            h = SLAB_PX + levels * LEVEL_PX
            rx = (x - y) * 16 + (height - 1) * 16
            ry = (x + y) * 8 + max_h - h
            image = images[cell]
            column = image.resize((16, h), Image.NEAREST) if h != 16 else image
            # south face: X in 0..16, texture (s, t) = (X, Y - X/2)
            south = column.transform((16, h + 8), Image.AFFINE, (1, 0, 0, -0.5, 1, 0), Image.NEAREST)
            canvas.alpha_composite(shade(south, 0.78), (rx, ry + 8))
            # east face: X in 0..16 (screen 16..32), texture (s, t) = (16 - X, Y - 8 + X/2)
            east = column.transform((16, h + 8), Image.AFFINE, (-1, 0, 16, 0.5, 1, -8), Image.NEAREST)
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
  html, body { margin: 0; height: 100%; background: #0b0f1a; color: #dfe6f3; font: 14px system-ui, sans-serif; }
  canvas { display: block; }
  #hud { position: fixed; left: 12px; top: 10px; background: rgba(11,15,26,.72); padding: 8px 10px; border-radius: 8px; }
  #hud b { color: #fff; }
</style>
</head>
<body>
<div id="hud"><b>__TITLE__</b> · drag to orbit, wheel to zoom, right-drag to pan</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const SCENE = __SCENE__;
const ATLAS = "data:image/png;base64,__ATLAS__";
const SIZE = 16, LEVEL = 16, SLAB = 3;

const heights = SCENE.blocks.map(b => SLAB + b[1] * LEVEL);
function heightAt(x, y) {
  if (x < 0 || y < 0 || x >= SCENE.width || y >= SCENE.height) return 0;
  return heights[y * SCENE.width + x];
}

// One merged mesh: for every block the top face and the side faces a lower neighbour leaves open.
const positions = [], normals = [], uvs = [], indices = [];
const cw = 1 / SCENE.atlasColumns, ch = 1 / SCENE.atlasRows;
function quad(p, n, cell, uvMode) {
  const base = positions.length / 3;
  const u0 = (cell % SCENE.atlasColumns) * cw, v0 = 1 - Math.floor(cell / SCENE.atlasColumns) * ch;
  for (let i = 0; i < 4; i++) { positions.push(...p[i]); normals.push(...n); }
  const uv = uvMode === "top"
    ? [[u0, v0], [u0 + cw, v0], [u0 + cw, v0 - ch], [u0, v0 - ch]]
    : [[u0, v0], [u0 + cw, v0], [u0 + cw, v0 - ch], [u0, v0 - ch]];
  for (const [u, v] of uv) uvs.push(u, v);
  indices.push(base, base + 2, base + 1, base, base + 3, base + 2);
}
for (let y = 0; y < SCENE.height; y++) for (let x = 0; x < SCENE.width; x++) {
  const [cell, levels] = SCENE.blocks[y * SCENE.width + x];
  const h = heights[y * SCENE.width + x];
  const x0 = x * SIZE, x1 = x0 + SIZE, z0 = y * SIZE, z1 = z0 + SIZE;
  quad([[x0, h, z0], [x1, h, z0], [x1, h, z1], [x0, h, z1]], [0, 1, 0], cell, "top");
  const sides = [
    [heightAt(x, y + 1), [[x0, h, z1], [x1, h, z1], [x1, 0, z1], [x0, 0, z1]], [0, 0, 1]],   // south
    [heightAt(x, y - 1), [[x1, h, z0], [x0, h, z0], [x0, 0, z0], [x1, 0, z0]], [0, 0, -1]],  // north
    [heightAt(x + 1, y), [[x1, h, z1], [x1, h, z0], [x1, 0, z0], [x1, 0, z1]], [1, 0, 0]],   // east
    [heightAt(x - 1, y), [[x0, h, z0], [x0, h, z1], [x0, 0, z1], [x0, 0, z0]], [-1, 0, 0]],  // west
  ];
  for (const [nh, p, n] of sides) if (nh < h) {
    // the side shows the same metatile, stretched over the open height
    quad(p, n, cell, "side");
  }
}
const geometry = new THREE.BufferGeometry();
geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
geometry.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
geometry.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
geometry.setIndex(indices);

const texture = new THREE.TextureLoader().load(ATLAS);
texture.magFilter = THREE.NearestFilter;
texture.minFilter = THREE.NearestFilter;
const material = new THREE.MeshLambertMaterial({ map: texture });
const mesh = new THREE.Mesh(geometry, material);
mesh.castShadow = mesh.receiveShadow = true;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0f1a);
scene.add(mesh);
scene.add(new THREE.HemisphereLight(0xcfe3ff, 0x30261a, 0.75));
const sun = new THREE.DirectionalLight(0xfff1d6, 1.1);
const W = SCENE.width * SIZE, D = SCENE.height * SIZE;
sun.position.set(W * 0.2, 420, D * 0.9);
sun.target.position.set(W / 2, 0, D / 2);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
const cam = sun.shadow.camera; cam.left = -W; cam.right = W; cam.top = D; cam.bottom = -D; cam.near = 10; cam.far = 1500;
scene.add(sun, sun.target);

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

const camera = new THREE.PerspectiveCamera(42, innerWidth / innerHeight, 1, 6000);
camera.position.set(W / 2, Math.max(W, D) * 0.9, D * 1.35);
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.target.set(W / 2, 0, D / 2);
controls.maxPolarAngle = Math.PI / 2 - 0.05;
controls.update();

addEventListener("resize", () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});
(function frame() { controls.update(); renderer.render(scene, camera); requestAnimationFrame(frame); })();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("layout", nargs="?", help="a LAYOUT_* id from data/layouts/layouts.json")
    ap.add_argument("out", nargs="?", help="the .html to write")
    ap.add_argument("--list", action="store_true", help="print every layout id")
    ap.add_argument("--png", help="also draw the scene as an isometric PNG at this path")
    args = ap.parse_args()
    if args.list:
        for layout_id in read_layouts():
            print(layout_id)
        return
    if not args.layout or not args.out:
        ap.error("layout and out are required (or --list)")
    images, blocks, width, height = export(args.layout, args.out)
    if args.png:
        render_png(images, blocks, width, height, args.png)


if __name__ == "__main__":
    main()
