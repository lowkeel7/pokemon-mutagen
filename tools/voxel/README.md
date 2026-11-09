# Voxel view (BACKLOG DP-21)

The overworld as a voxel diorama, drawn from the decomp's own map data, beside the game: a
desktop extra. Nothing of it is in the ROM, so it never reaches the phone or a flash cart.

## Still pictures and pages

    tools/voxel/export_map.py LAYOUT_NEW_BARK_TOWN_HNS out/new-bark-town.html --png out/new-bark-town.png
    tools/voxel/export_map.py --list          # every layout id
    tools/voxel/export_map.py --sweep         # build every layout, report the ones that fail

The page needs an internet connection the first time (three.js comes from cdnjs); the PNG needs
nothing but Pillow.

## Live, following the player

1. Build the game (`make hns`): the view reads addresses from `pokehns.elf`, so the ROM open in
   mGBA must be that build.
2. `tools/voxel/serve.py` (page on http://127.0.0.1:8765/, the script's port 8776; `--http` and
   `--sync` change them). It writes `build/voxel/mgba-sync.lua`.
3. Desktop mGBA 0.10 or later (`brew install --cask mgba`): open `pokehns.gba`, then
   Tools → Scripting… → File → Load script → `build/voxel/mgba-sync.lua`. The scripting console
   says "voxel: connected".
4. Open http://127.0.0.1:8765/ in a browser. It follows the player (F toggles that), rebuilds when
   the map changes, and the mouse orbits, zooms and pans.

## The demo video

`tools/voxel/demo.py` is a scripted walk (out of the player's house in New Bark Town, past the lab,
west along Route 29 into Cherrygrove City and through the Pokémon Center's door), found on the
maps' own collision data at the game's walking and running pace. With `serve.py` running:

    tools/voxel/record.py

starts a second, headless Chrome beside the one in use (Mullvad Browser and Tor Browser refuse WebGL
readback), has the page draw the walk one frame at a time at 1920x1080, screenshots each over
DevTools and feeds them to ffmpeg (`brew install ffmpeg`), which writes `build/voxel/demo.mp4`
with the map's name drawn on. About two minutes. `demo.py` alone prints the route.

## How the heights come out

Every metatile is a block. Passable ground (water too) is a thin slab. Trees and bushes are the
solid blocks drawn in their tileset's vegetation palette (`TREE_PALETTES`: palette 0 of the Johto
and Kanto general tilesets, Cherrygrove's pink trees; buildings, cliffs and signs use others):
their canopy pixels stand as columns, higher the further from the canopy's edge (`DOME_RADIUS`,
`DOME_EDGE`), so a tree is a stepped dome with its own leaves on every face and a forest a bumpy
canopy. Every other column's run of impassable blocks stands as one box: a run with over-the-player
pixels (a roof) two levels, a repeated metatile (hedge, fence, cliff line) one, anything else (a
building: roof rows over a wall row, the door counted in) up to three, with the run's rows standing
up as the box's front face, so the 2D art becomes the facade. Tune `MAX_LEVELS`, `TREE_LEVELS` and
the behaviour sets in `export_map.py`; add a town's tileset and its trees' palette to
`TREE_PALETTES` to round its own trees too. The `--png` picture still draws trees as boxes.
