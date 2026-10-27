#!/usr/bin/env python3
"""Check that saves keep loading: continue a save, save in-game, power-cycle, continue again.

    tools/playtest/savecheck.py --out /tmp/saves pokehns.gba pokehns-release.gba

Takes every tools/playtest/saves/*.sav unless --save is given. For each ROM and save it continues
into the overworld and reads what the save holds (map, position, player name, gender and ID, the
party's levels and HP, SaveBlock3 with the challenge options), saves from the start menu, power-
cycles, continues and reads it again. It fails when a step doesn't finish, when the second read
differs from the first, or when a ROM reads a save differently from the first ROM. Any build works
(dev or release) as long as its .elf is next to it. Screenshots and the re-saved .sav go to <out>.
"""
import argparse
import glob
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import playtest  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
MENU_ACTION_SAVE = 5        # src/start_menu.c
SAVEBLOCK3_SIZE = 52        # test/save.c
MON_SIZE, MON_LEVEL, MON_HP = 100, 84, 86  # struct Pokemon: level, then hp and maxHP


class Game:
    def __init__(self, core, rom, sram, out):
        self.rom, self.out = rom, out
        self.core = playtest.Core(core, out)
        self.by_name, self.by_addr = playtest.load_symbols(os.path.splitext(rom)[0] + ".elf", out)
        self.power_on(sram)

    def power_on(self, sram):
        self.core.load(self.rom)
        self.core.put_sram(sram)
        self.core.run(1)

    def power_cycle(self):
        sram = self.core.get_sram()
        self.core.unload()
        self.power_on(sram)

    def u32(self, addr):
        return struct.unpack("<I", self.core.read(addr, 4))[0]

    def byte(self, sym):
        return self.core.read(self.by_name[sym], 1)[0]

    def cb2(self):
        ptr = self.u32(self.by_name["gMain"] + 4)
        return self.by_addr.get(ptr & ~1, f"0x{ptr:08x}")

    def run_until(self, name, limit, button=None):
        for _ in range(limit // 10):
            if self.cb2() == name:
                return True
            self.core.run(4, [button] if button else [])
            self.core.run(6)
        return False

    def shot(self, name):
        img = self.core.screen_rgb()
        if img:
            playtest.write_png(os.path.join(self.out, name + ".png"), *img, 1)

    def free(self):
        return self.cb2() == "CB2_Overworld" and self.byte("sLockFieldControls") == 0

    def continue_game(self):
        if not self.run_until("CB2_MainMenu", 3000, "START"):
            return f"no main menu (at {self.cb2()})"
        self.core.run(90)
        self.core.run(6, ["A"])
        if not self.run_until("CB2_Overworld", 1200):
            return f"didn't continue into the overworld (at {self.cb2()})"
        self.core.run(180)
        return "ok"

    def read(self):
        sb1, sb2, sb3 = (self.u32(self.by_name[f"gSaveBlock{n}Ptr"]) for n in (1, 2, 3))
        party = []
        for i in range(self.byte("gPlayerPartyCount")):
            mon = self.by_name["gPlayerParty"] + MON_SIZE * i
            party.append([self.core.read(mon + MON_LEVEL, 1)[0], *struct.unpack("<HH", self.core.read(mon + MON_HP, 4))])
        return {
            # HnS puts a u16 saveVersion first in SaveBlock1, so pos is at +4 and location at +8.
            "location": list(struct.unpack("<bb", self.core.read(sb1 + 8, 2))),
            "pos": list(struct.unpack("<hh", self.core.read(sb1 + 4, 4))),
            "name": self.core.read(sb2, 8).hex(),
            "gender": self.core.read(sb2 + 8, 1)[0],
            "trainer_id": self.core.read(sb2 + 0xA, 4).hex(),
            "party": party,
            "saveblock3": self.core.read(sb3, SAVEBLOCK3_SIZE).hex(),
        }

    def save_game(self):
        self.core.run(4, ["START"])
        self.core.run(40)
        actions = list(self.core.read(self.by_name["sCurrentStartMenuActions"], self.byte("sNumStartMenuActions")))
        if MENU_ACTION_SAVE not in actions:
            return f"no SAVE in the start menu {actions}"
        move = actions.index(MENU_ACTION_SAVE) - self.byte("sStartMenuCursorPos")
        for _ in range(abs(move)):
            self.core.run(4, ["DOWN" if move > 0 else "UP"])
            self.core.run(12)
        self.core.run(4, ["A"])
        self.core.run(90)
        self.shot("save-prompt")
        # A says YES to "save the game?" and to "overwrite?", then closes "saved the game".
        for i in range(40):
            if i > 10 and self.free():
                return "ok"
            self.core.run(4, ["A"])
            self.core.run(56)
        return f"the save didn't finish (at {self.cb2()})"


def check(core, rom, save, out):
    """('ok' or the problem, what the save held when first continued)."""
    game = Game(core, rom, open(save, "rb").read(), out)
    result = game.continue_game()
    if result != "ok":
        return result, None
    held = game.read()
    result = game.save_game()
    if result != "ok":
        return result, held
    open(os.path.join(out, "after.sav"), "wb").write(game.core.get_sram())
    game.power_cycle()
    result = game.continue_game()
    game.shot("continued")
    if result != "ok":
        return f"after saving, {result}", held
    again = game.read()
    changed = [k for k in held if held[k] != again[k]]
    return ("ok" if not changed else f"saving changed {', '.join(changed)}"), held


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("roms", nargs="+")
    ap.add_argument("--save", action="append", help="a .sav to check (repeatable); default saves/*.sav")
    ap.add_argument("--out", required=True)
    ap.add_argument("--core", default=next((os.path.expanduser(p) for p in playtest.DEFAULT_CORES
                                            if os.path.exists(os.path.expanduser(p))), None))
    args = ap.parse_args()
    saves = args.save or sorted(glob.glob(os.path.join(HERE, "saves", "*.sav")))
    failed = 0
    for save in saves:
        reference = None
        for i, rom in enumerate(args.roms):
            # Numbered: two builds are often both pokehns.gba.
            name = f"{i + 1}-{os.path.splitext(os.path.basename(rom))[0]}-{os.path.splitext(os.path.basename(save))[0]}"
            out = os.path.join(args.out, name)
            os.makedirs(out, exist_ok=True)
            result, held = check(args.core, rom, save, out)
            if result == "ok" and reference and held != reference[1]:
                diff = [k for k in held if held[k] != reference[1][k]]
                result = f"reads {', '.join(diff)} differently from {reference[0]}"
            reference = reference or (held and (f"ROM {i + 1}", held))
            failed += result != "ok"
            print(f"{result}\t{name}\t{json.dumps(held)}", flush=True)
    print(f"savecheck: {len(saves) * len(args.roms) - failed} of {len(saves) * len(args.roms)} ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
