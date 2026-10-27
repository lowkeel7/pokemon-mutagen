#!/usr/bin/env python3
"""Warp to every map of a dev build and report the ones that don't load cleanly.

Uses the gDebugWarpRequest hook in src/debug.c, so it needs a `make hns` ROM (debug menus on) with
its .elf next to it, and a save that continues into the overworld; smoke.txt leaves one in its
session folder:

    tools/playtest/playtest.py --rom pokehns.gba --session /tmp/pt --fresh @tools/playtest/smoke.txt
    tools/playtest/mapsweep.py --rom pokehns.gba --save /tmp/pt/save.sav --out /tmp/sweep

For each map it posts a warp to the map's first warp (its centre if it has none), taps B through
any on-load script, and waits for the overworld to settle there. Results go to <out>/results.tsv,
with a screenshot of every map that didn't: battle (a battle started on arrival), wrong-map,
timeout (stuck in another callback) or locked (the warp was never taken: controls stayed locked).
Every warp starts from the state the save continued into, so maps can't affect each other.
"""
import argparse
import os
import re
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import playtest  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MAP_LINE = re.compile(r"^\s+(MAP_\w+)\s*=\s*\((\d+) \| \((\d+) << 8\)\)")


def load_maps(path):
    maps = []
    for line in open(path):
        m = MAP_LINE.match(line)
        if m:
            maps.append((m.group(1), int(m.group(3)), int(m.group(2))))
    return maps


class Sweep:
    def __init__(self, args):
        self.args = args
        self.core = playtest.Core(args.core, args.out)
        self.core.load(args.rom)
        self.core.put_sram(open(args.save, "rb").read())
        self.core.run(1)
        self.by_name, self.by_addr = playtest.load_symbols(os.path.splitext(args.rom)[0] + ".elf", args.out)
        self.request = self.by_name["gDebugWarpRequest"]
        self.main = self.by_name["gMain"]
        self.sb1 = self.by_name["gSaveBlock1Ptr"]

    def cb2(self):
        ptr = struct.unpack("<I", self.core.read(self.main + 4, 4))[0]
        return self.by_addr.get(ptr & ~1, f"0x{ptr:08x}")

    def location(self):
        # gSaveBlock1Ptr->location. HnS puts a u16 saveVersion (and padding) before pos, so it is
        # at +8, not the +4 that global.h's offset comments say.
        sb1 = struct.unpack("<I", self.core.read(self.sb1, 4))[0]
        group, num = struct.unpack("<bb", self.core.read(sb1 + 8, 2))
        return group, num

    def pending(self):
        return struct.unpack("<H", self.core.read(self.request, 2))[0] != 0

    def run_until(self, name, limit, button=None):
        for _ in range(limit // 10):
            if self.cb2() == name:
                return True
            self.core.run(4, [button] if button else [])
            self.core.run(6)
        return False

    def boot(self):
        if not self.run_until("CB2_MainMenu", 3000, "START"):
            sys.exit(f"mapsweep: no main menu (at {self.cb2()})")
        self.core.run(90)
        self.core.run(6, ["A"])
        if not self.run_until("CB2_Overworld", 1200):
            sys.exit(f"mapsweep: the save didn't continue into the overworld (at {self.cb2()})")
        self.core.run(120)

    def shot(self, name):
        img = self.core.screen_rgb()
        if img:
            playtest.write_png(os.path.join(self.args.out, name + ".png"), *img, 1)

    def visit(self, group, num, pos=None):
        """'ok' or the problem, and the callback and location it ended on. pos=(x, y) lands there
        instead of on the map's first warp."""
        if pos:
            self.core.write(self.by_name["gDebugWarpRequestPos"], struct.pack("<H", ((pos[1] << 8) | pos[0]) + 1))
        self.core.write(self.request, struct.pack("<H", ((group << 8) | num) + 1))
        settled = 0
        for frame in range(0, self.args.timeout, 10):
            cb2 = self.cb2()
            if "Battle" in cb2:
                return "battle", cb2
            if not self.pending() and cb2 == "CB2_Overworld" and self.location() == (group, num):
                settled += 10
                if settled >= self.args.settle:
                    return "ok", cb2
            else:
                settled = 0
            # B clears on-load messages and says NO to questions; in the free overworld it does nothing.
            self.core.run(4, ["B"] if frame % 40 == 20 else [])
            self.core.run(6)
        cb2 = self.cb2()
        if self.pending():
            return "locked", cb2
        if cb2 == "CB2_Overworld":
            return "wrong-map", cb2
        return "timeout", cb2


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--save", required=True, help="a save that continues into the overworld")
    ap.add_argument("--out", required=True)
    ap.add_argument("--core", default=next((os.path.expanduser(p) for p in playtest.DEFAULT_CORES
                                            if os.path.exists(os.path.expanduser(p))), None))
    ap.add_argument("--maps", default=os.path.join(ROOT, "include", "constants", "map_groups.h"))
    ap.add_argument("--only", help="regex on the map constant, e.g. 'ROUTE3[0-9]'")
    ap.add_argument("--timeout", type=int, default=1200, help="frames per map")
    ap.add_argument("--settle", type=int, default=60, help="frames the overworld must hold on the map")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    maps = load_maps(args.maps)
    if args.only:
        maps = [m for m in maps if re.search(args.only, m[0])]
    sweep = Sweep(args)
    sweep.boot()
    base = sweep.core.get_state()
    start, counts = time.time(), {}
    with open(os.path.join(args.out, "results.tsv"), "w") as out:
        out.write("result\tmap\tgroup\tnum\tended_on\tlocation\n")
        for i, (name, group, num) in enumerate(maps):
            # Every visit starts from the same state, so a map whose script runs on (a Battle Tent
            # corridor walks you into its rental screen) can't leave the next warp locked.
            sweep.core.put_state(base)
            sweep.core.run(1)
            result, cb2 = sweep.visit(group, num)
            counts[result] = counts.get(result, 0) + 1
            loc = sweep.location() if result != "timeout" else ("?", "?")
            out.write(f"{result}\t{name}\t{group}\t{num}\t{cb2}\t{loc[0]}.{loc[1]}\n")
            out.flush()
            if result != "ok":
                sweep.shot(f"{result}-{name}")
            if i == 4 and counts.get("wrong-map") == 5:
                sys.exit("mapsweep: the first 5 maps all read as wrong-map; did SaveBlock1's layout change?")
            if (i + 1) % 100 == 0:
                print(f"mapsweep: {i + 1}/{len(maps)} {counts} ({time.time() - start:.0f}s)", flush=True)
    print(f"mapsweep: {len(maps)} maps {counts} in {time.time() - start:.0f}s; {args.out}/results.tsv")
    return 0 if counts.get("ok", 0) == len(maps) else 1


if __name__ == "__main__":
    sys.exit(main())
