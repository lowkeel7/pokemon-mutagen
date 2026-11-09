#!/usr/bin/env python3
"""The voxel view's demo walk (BACKLOG DP-21): out of the player's house in New Bark Town, past
Elm's lab, west along Route 29 into Cherrygrove City and through the Pokémon Center's door, as one
frame of "map group, map number, x, y, facing" per video frame.

    tools/voxel/demo.py           # print the route
    tools/voxel/demo.py --json    # what serve.py sends the page at /demo

The route is found on the maps' own collision data (map.bin), so it walks where the game lets the
player walk, and the maps join where their map.json connections say they do. serve.py serves it at
/demo; the page opened with ?record renders every frame and hands it back for the video.
"""
import argparse
import json
import os
import re
import struct
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import export_map  # noqa: E402

FPS = 30
WALK = 8            # video frames per tile: the game's 16 of 60
RUN = 4             # running shoes: the game's 8 of 60
SOUTH, NORTH, WEST, EAST = 1, 2, 3, 4
STEPS = {SOUTH: (0, 1), NORTH: (0, -1), WEST: (-1, 0), EAST: (1, 0)}
ELEVATION_SHIFT = 12
BLOCKED = r"DOOR|WARP|LADDER|ESCALATOR|HOLE|WATER|CURRENT|WATERFALL|DIVE|JUMP|IMPASSABLE"

# The walk: (map, waypoints) in order; a waypoint is a tile, "west" (leave by the west edge, where
# the next map is passable too) or ("door", x, y) (step onto that door, then the next map starts
# at its warp).
ROUTE = [
    ("MAP_NEW_BARK_TOWN_HNS", [(20, 12), (10, 10), "west"], WALK),
    ("MAP_ROUTE29_HNS", ["west"], RUN),
    ("MAP_CHERRYGROVE_CITY_HNS", [(47, 8), ("door", 47, 7)], WALK),
    ("MAP_CHERRYGROVE_CITY_POKEMON_CENTER_HNS", [(7, 8), (7, 6)], WALK),
]
HOLD_START, HOLD_DOOR, HOLD_END = 1.5, 0.6, 2.5     # seconds


def pretty(name):
    """NewBarkTown_hns -> New Bark Town."""
    name = re.sub(r"_[Hh]ns$", "", name)
    return re.sub(r"(?<=[a-z])(?=[A-Z0-9])|(?<=[0-9])(?=[A-Z])|_", " ", name).strip()


class Map:
    """One map's grid, read as the game reads it: collision and elevation from map.bin, the
    behaviour from the metatile's attributes, the connections from map.json."""

    def __init__(self, map_id):
        index = export_map.map_index()
        self.key, entry = next((k, v) for k, v in index.items() if v["id"] == map_id)
        self.id = map_id
        self.name = pretty(entry["name"])
        with open(os.path.join(export_map.ROOT, "data/maps", entry["name"], "map.json")) as f:
            self.json = json.load(f)
        layout = export_map.read_layouts()[entry["layout"]]
        self.width, self.height = layout["width"], layout["height"]
        self.primary = export_map.tileset(layout["primary_tileset"])
        self.secondary = export_map.tileset(layout["secondary_tileset"])
        with open(os.path.join(export_map.ROOT, layout["blockdata_filepath"]), "rb") as f:
            data = f.read(self.width * self.height * 2)
        self.grid = struct.unpack(f"<{len(data) // 2}H", data)
        self.blocked = export_map.behavior_set(BLOCKED)

    def value(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height and y * self.width + x < len(self.grid):
            return self.grid[y * self.width + x]
        return None

    def behavior(self, value):
        metatile = value & export_map.METATILE_ID_MASK
        source, local = (self.primary, metatile) if metatile < export_map.NUM_METATILES_IN_PRIMARY \
            else (self.secondary, metatile - export_map.NUM_METATILES_IN_PRIMARY)
        return source.attributes[local] & export_map.ATTR_BEHAVIOR_MASK if local < len(source.attributes) else 0

    def passable(self, x, y):
        value = self.value(x, y)
        return value is not None and (value & export_map.COLLISION_MASK) == 0 and self.behavior(value) not in self.blocked

    def elevation(self, x, y):
        value = self.value(x, y)
        return (value >> ELEVATION_SHIFT) & 0xF if value is not None else 0

    def can_step(self, a, b):
        if not self.passable(*b):
            return False
        ea, eb = self.elevation(*a), self.elevation(*b)
        return ea == eb or ea in (0, 15) or eb in (0, 15)

    def path(self, start, goal):
        """Shortest walk from start to a tile goal or to any tile goal(x, y) accepts."""
        accept = goal if callable(goal) else (lambda x, y: (x, y) == goal)
        if accept(*start):
            return [start]
        previous = {start: None}
        queue = deque([start])
        while queue:
            at = queue.popleft()
            for dx, dy in STEPS.values():
                nxt = (at[0] + dx, at[1] + dy)
                if nxt in previous or not self.can_step(at, nxt):
                    continue
                previous[nxt] = at
                if accept(*nxt):
                    out = [nxt]
                    while previous[out[-1]] is not None:
                        out.append(previous[out[-1]])
                    return out[::-1]
                queue.append(nxt)
        raise ValueError(f"{self.id}: no walk from {start} to {goal if not callable(goal) else 'the goal'}")

    def connection(self, direction):
        for c in self.json.get("connections") or []:
            if c["direction"] == direction:
                return c
        raise ValueError(f"{self.id} has no {direction} connection")


def west_crossing(here, there):
    """Tiles (x=0, y) of `here` from which a step west lands on a passable tile of `there`, and
    that tile: the game puts the player at (there.width - 1, y - offset) (fieldmap.c
    SetPositionFromConnection)."""
    offset = here.connection("left")["offset"]
    crossings = {}
    for y in range(here.height):
        landing = (there.width - 1, y - offset)
        if here.passable(0, y) and there.passable(*landing):
            crossings[(0, y)] = landing
    return crossings


def direction(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    return {(0, 1): SOUTH, (0, -1): NORTH, (-1, 0): WEST, (1, 0): EAST}[(dx, dy)]


class Timeline:
    def __init__(self):
        self.frames = []        # [group, num, x, y, facing], x and y fractional between tiles
        self.segments = []      # {"start", "end", "map"} in frames
        self.steps = []         # for --print

    def hold(self, m, tile, facing, seconds):
        for _ in range(round(seconds * FPS)):
            self.frames.append([m.key[0], m.key[1], tile[0], tile[1], facing])

    def walk(self, m, path, per_tile, entering_from=None):
        """path tiles in order; entering_from: an off-map tile the first step starts from."""
        start = len(self.frames)
        tiles = ([entering_from] if entering_from else []) + list(path)
        facing = SOUTH
        for a, b in zip(tiles, tiles[1:]):
            facing = direction(a, b)
            for k in range(1, per_tile + 1):
                t = k / per_tile
                self.frames.append([m.key[0], m.key[1], a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, facing])
        self.steps.append((m.name, tiles[0], tiles[-1], len(tiles) - 1, len(self.frames) - start))
        return facing

    def segment(self, m, start):
        if self.segments and self.segments[-1]["map"] == m.name:
            self.segments[-1]["end"] = len(self.frames)
        else:
            self.segments.append({"start": start, "end": len(self.frames), "map": m.name})


def timeline():
    tl = Timeline()
    maps = [Map(map_id) for map_id, _, _ in ROUTE]
    at = None               # the player's tile in the current map
    entering_from = None    # off-map tile the first step comes from (a map crossing)
    facing = SOUTH
    next_start = None       # a map entered by a door starts with its hold, already added
    for i, ((_, waypoints, per_tile), m) in enumerate(zip(ROUTE, maps)):
        start = len(tl.frames) if next_start is None else next_start
        next_start = None
        if at is None:
            at = waypoints[0]
            if not m.passable(*at):
                raise ValueError(f"{m.id}: the start {at} is not passable")
            tl.hold(m, at, facing, HOLD_START)
            waypoints = waypoints[1:]
        for waypoint in waypoints:
            if waypoint == "west":
                crossings = west_crossing(m, maps[i + 1])
                path = m.path(at, lambda x, y: (x, y) in crossings)
                facing = tl.walk(m, path, per_tile, entering_from)
                landing = crossings[path[-1]]
                # the step off the edge: the next map draws it, from one tile past its east edge
                entering_from = (landing[0] + 1, landing[1])
                at = None
                tl.segment(m, start)
                break
            if isinstance(waypoint, tuple) and waypoint[0] == "door":
                door = waypoint[1:]
                path = m.path(at, lambda x, y: (x, y) == door or (abs(x - door[0]) + abs(y - door[1]) == 1 and m.passable(x, y)))
                if path[-1] != door:
                    path.append(door)
                facing = tl.walk(m, path, per_tile, entering_from)
                entering_from = None
                tl.hold(m, door, facing, HOLD_DOOR)
                at = None
                tl.segment(m, start)
                break
            path = m.path(at, tuple(waypoint))
            facing = tl.walk(m, path, per_tile, entering_from)
            entering_from = None
            at = path[-1]
        else:
            tl.segment(m, start)
            if at is not None and i + 1 < len(ROUTE):
                raise ValueError(f"{m.id}: the route does not leave the map")
        if at is None and i + 1 < len(ROUTE) and entering_from is None:
            # arrived by a door: the next map starts at its first waypoint, facing north
            nxt = maps[i + 1]
            at = ROUTE[i + 1][1][0]
            next_start = len(tl.frames)
            tl.hold(nxt, at, NORTH, HOLD_DOOR)
            facing = NORTH
            ROUTE[i + 1] = (ROUTE[i + 1][0], ROUTE[i + 1][1][1:], ROUTE[i + 1][2])
        elif at is None and entering_from is not None:
            # the next map's first step starts from entering_from and lands on `at`
            at = (entering_from[0] - 1, entering_from[1])
    last = tl.frames[-1]
    tl.hold(maps[-1], (last[2], last[3]), last[4], HOLD_END)
    tl.segment(maps[-1], tl.segments[-1]["end"] if tl.segments else 0)
    return {"fps": FPS, "frames": tl.frames, "segments": tl.segments, "steps": tl.steps}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--json", action="store_true", help="print the frames as JSON")
    args = ap.parse_args()
    tl = timeline()
    if args.json:
        json.dump({k: v for k, v in tl.items() if k != "steps"}, sys.stdout)
        return
    for name, a, b, tiles, frames in tl["steps"]:
        print(f"{name:20s} {a} -> {b}: {tiles} tiles, {frames} frames")
    for s in tl["segments"]:
        print(f"segment {s['map']:20s} frames {s['start']}-{s['end']}")
    print(f"{len(tl['frames'])} frames, {len(tl['frames']) / FPS:.1f} s at {FPS} fps")


if __name__ == "__main__":
    main()
