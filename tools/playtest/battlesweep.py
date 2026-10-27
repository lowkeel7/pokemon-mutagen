#!/usr/bin/env python3
"""Fight every trainer of a dev build, with the AI playing both sides, and report the battles that
don't start or don't end.

Uses the gDebugBattleRequest hook in src/debug.c (dev builds only): the player gets the debug
party (src/data/debug_trainers.party), the trainer keeps its own party and single/double format,
and gDebugAiVsAi hands the player's side to the battle AI, so no input is needed beyond advancing
text. Same save as mapsweep.py:

    tools/playtest/battlesweep.py --rom pokehns.gba --save /tmp/pt/save.sav --out /tmp/battles

Results in <out>/results.tsv: ok (back in the overworld, won or lost), no-start, hang (the screen
stopped changing), long (still fighting at --timeout) or stuck (left the battle for somewhere
other than the overworld). Every problem gets a screenshot.
"""
import argparse
import ctypes as C
import os
import re
import struct
import sys
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapsweep  # noqa: E402
import playtest  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TRAINER_LINE = re.compile(r"^#define (TRAINER_\w+)\s+(\d+)\s*$")


def load_trainers(path):
    count, trainers = None, []
    for line in open(path):
        m = TRAINER_LINE.match(line)
        if m and m.group(1) != "TRAINER_NONE":
            trainers.append((m.group(1), int(m.group(2))))
        m = re.match(r"^#define TRAINERS_COUNT_HNS\s+(\d+)", line)
        if m:
            count = int(m.group(1))
    return [t for t in trainers if count is None or t[1] < count]


def frame_crc(core):
    if not core.frame:
        return 0
    ptr, width, height, pitch = core.frame
    return zlib.crc32(C.string_at(ptr, pitch * height))


def fight(sweep, trainer_id, timeout):
    core = sweep.core
    core.write(sweep.by_name["gDebugBattleRequest"], struct.pack("<H", trainer_id + 1))
    for _ in range(60):
        core.run(10)
        if "Battle" in sweep.cb2():
            break
    else:
        return "no-start", sweep.cb2(), 0
    start, last_crc, still = core.frames, None, 0
    while core.frames - start < timeout:
        core.run(4, ["A"])   # the AI picks the moves; A only moves battle text along
        core.run(26)
        cb2 = sweep.cb2()
        if cb2 == "CB2_Overworld":
            return "ok", cb2, core.frames - start
        if "Battle" not in cb2 and core.frames - start > 600:
            # On the way back to the field a few callbacks pass by; one that stays is stuck.
            settled = 0
            for _ in range(40):
                core.run(30)
                if sweep.cb2() == "CB2_Overworld":
                    return "ok", "CB2_Overworld", core.frames - start
                settled += 30
            return "stuck", sweep.cb2(), core.frames - start
        crc = frame_crc(core)
        still = still + 30 if crc == last_crc else 0
        last_crc = crc
        if still >= 3000:
            return "hang", cb2, core.frames - start
    return "long", sweep.cb2(), core.frames - start


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--save", required=True, help="a save that continues into the overworld")
    ap.add_argument("--out", required=True)
    ap.add_argument("--core", default=next((os.path.expanduser(p) for p in playtest.DEFAULT_CORES
                                            if os.path.exists(os.path.expanduser(p))), None))
    ap.add_argument("--trainers", default=os.path.join(ROOT, "include", "constants", "opponents_hns.h"))
    ap.add_argument("--only", help="regex on the trainer constant, e.g. 'FALKNER|RED'")
    ap.add_argument("--timeout", type=int, default=60000, help="frames per battle")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    trainers = load_trainers(args.trainers)
    if args.only:
        trainers = [t for t in trainers if re.search(args.only, t[0])]
    args.settle = 60  # mapsweep.Sweep reads it; unused here
    sweep = mapsweep.Sweep(args)
    sweep.boot()
    base = sweep.core.get_state()
    started, counts = time.time(), {}
    with open(os.path.join(args.out, "results.tsv"), "w") as out:
        out.write("result\ttrainer\tid\tended_on\tframes\n")
        for i, (name, tid) in enumerate(trainers):
            sweep.core.put_state(base)
            sweep.core.run(1)
            result, cb2, frames = fight(sweep, tid, args.timeout)
            counts[result] = counts.get(result, 0) + 1
            out.write(f"{result}\t{name}\t{tid}\t{cb2}\t{frames}\n")
            out.flush()
            if result != "ok":
                sweep.shot(f"{result}-{name}")
            if (i + 1) % 50 == 0:
                print(f"battlesweep: {i + 1}/{len(trainers)} {counts} ({time.time() - started:.0f}s)", flush=True)
    print(f"battlesweep: {len(trainers)} trainers {counts} in {time.time() - started:.0f}s; {args.out}/results.tsv")
    return 0 if counts.get("ok", 0) == len(trainers) else 1


if __name__ == "__main__":
    sys.exit(main())
