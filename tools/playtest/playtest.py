#!/usr/bin/env python3
"""Headless playtest harness: runs a GBA ROM in a libretro core (RetroArch's mGBA core by default,
the core the phone target uses), drives it with a small script and writes screenshots.

State carries over between runs through a save state and a save-RAM file, so a session can be
driven one command at a time:

    tools/playtest/playtest.py --rom pokehns.gba --session /tmp/pt "wait 600; shot title"
    tools/playtest/playtest.py --rom pokehns.gba --session /tmp/pt "press START; wait 120; shot menu"

--fresh starts from power-on with blank save RAM. Names need arm-none-eabi-nm on PATH and the .elf
next to the ROM. Scripts may be given as @file; '#' starts a comment. Commands, separated by ';'
or newlines (a FAIL line makes the run exit 1):
    wait N                   run N frames with no input
    press BTN[+BTN] [N] [G]  hold the buttons N frames (default 6), then release for G (default 20)
    hold BTN[+BTN] N         hold the buttons N frames
    chord HELD BTN [G]       hold HELD, then press BTN with it (R then START opens the debug menu)
    mash BTN N               tap BTN every 12 frames for N frames
    shot NAME                write NAME.png into the session folder
    cb2                      print gMain.callback2 by name (needs the ELF next to the ROM)
    until CB2NAME [N]        run until gMain.callback2 is CB2NAME, at most N frames (default 3600)
    mashuntil BTN CB2NAME [N]  as until, tapping BTN meanwhile
    read SYM [OFFSET] [LEN]  hex dump LEN bytes (default 16) at SYM+OFFSET; SYM may be an address
    deref SYM [OFFSET] [LEN] read the pointer at SYM, then dump LEN bytes at pointer+OFFSET
    reboot                   power cycle: keep save RAM, drop everything else, as on a cart
    still N                  fail unless the screen changed during the next N frames (hang check)
Buttons: A B L R START SELECT UP DOWN LEFT RIGHT.
"""
import argparse
import ctypes as C
import os
import struct
import subprocess
import sys
import zlib

DEFAULT_CORES = [
    "~/Library/Application Support/RetroArch/cores/mgba_libretro.dylib",
    "~/.config/retroarch/cores/mgba_libretro.so",
]

BUTTONS = {"B": 0, "SELECT": 2, "START": 3, "UP": 4, "DOWN": 5, "LEFT": 6, "RIGHT": 7, "A": 8, "L": 10, "R": 11}

ENV_GET_CAN_DUPE = 3
ENV_GET_SYSTEM_DIRECTORY = 9
ENV_SET_PIXEL_FORMAT = 10
ENV_GET_VARIABLE = 15
ENV_GET_VARIABLE_UPDATE = 17
ENV_GET_CORE_ASSETS_DIRECTORY = 30
ENV_GET_SAVE_DIRECTORY = 31
ENV_SET_MEMORY_MAPS = 36 | 0x10000
ENV_ACCEPTED = {1, 6, 8, 11, 16, 32, 33, 34, 35, 37, 44, 53, 54, 55, 65, 67, 68, 69, 42 | 0x10000}

MEMORY_SAVE_RAM = 0

ENVIRONMENT = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VIDEO_REFRESH = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUDIO_SAMPLE = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUDIO_SAMPLE_BATCH = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
INPUT_POLL = C.CFUNCTYPE(None)
INPUT_STATE = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)


class GameInfo(C.Structure):
    _fields_ = [("path", C.c_char_p), ("data", C.c_void_p), ("size", C.c_size_t), ("meta", C.c_char_p)]


class SystemInfo(C.Structure):
    _fields_ = [("library_name", C.c_char_p), ("library_version", C.c_char_p),
                ("valid_extensions", C.c_char_p), ("need_fullpath", C.c_bool), ("block_extract", C.c_bool)]


class Variable(C.Structure):
    _fields_ = [("key", C.c_char_p), ("value", C.c_char_p)]


class MemoryDescriptor(C.Structure):
    _fields_ = [("flags", C.c_uint64), ("ptr", C.c_void_p), ("offset", C.c_size_t), ("start", C.c_size_t),
                ("select", C.c_size_t), ("disconnect", C.c_size_t), ("len", C.c_size_t), ("addrspace", C.c_char_p)]


class MemoryMap(C.Structure):
    _fields_ = [("descriptors", C.POINTER(MemoryDescriptor)), ("num_descriptors", C.c_uint)]


class Core:
    def __init__(self, core_path, workdir, options=None):
        self.lib = C.CDLL(core_path)
        self.workdir = workdir.encode()
        self.options = {k.encode(): v.encode() for k, v in (options or {}).items()}
        self.pixel_format = 0
        self.frame = None  # (pointer, width, height, pitch) of the last frame drawn
        self.pressed = set()
        self.regions = []  # (start, length, pointer) from the core's memory map
        self.frames = 0
        self._keep = [ENVIRONMENT(self._environment), VIDEO_REFRESH(self._video), AUDIO_SAMPLE(lambda l, r: None),
                      AUDIO_SAMPLE_BATCH(lambda d, n: n), INPUT_POLL(lambda: None), INPUT_STATE(self._input)]
        lib = self.lib
        lib.retro_set_environment(self._keep[0])
        lib.retro_set_video_refresh(self._keep[1])
        lib.retro_set_audio_sample(self._keep[2])
        lib.retro_set_audio_sample_batch(self._keep[3])
        lib.retro_set_input_poll(self._keep[4])
        lib.retro_set_input_state(self._keep[5])
        lib.retro_get_memory_data.restype = C.c_void_p
        lib.retro_get_memory_size.restype = C.c_size_t
        lib.retro_serialize_size.restype = C.c_size_t
        lib.retro_serialize.restype = C.c_bool
        lib.retro_unserialize.restype = C.c_bool
        lib.retro_load_game.restype = C.c_bool
        lib.retro_init()

    def _environment(self, cmd, data):
        if cmd == ENV_GET_CAN_DUPE:
            C.cast(data, C.POINTER(C.c_bool))[0] = True
            return True
        if cmd in (ENV_GET_SYSTEM_DIRECTORY, ENV_GET_SAVE_DIRECTORY, ENV_GET_CORE_ASSETS_DIRECTORY):
            C.cast(data, C.POINTER(C.c_char_p))[0] = self.workdir
            return True
        if cmd == ENV_SET_PIXEL_FORMAT:
            self.pixel_format = C.cast(data, C.POINTER(C.c_int))[0]
            return self.pixel_format in (0, 1, 2)
        if cmd == ENV_GET_VARIABLE:
            var = C.cast(data, C.POINTER(Variable))[0]
            if var.key in self.options:
                var.value = self.options[var.key]
                return True
            return False
        if cmd == ENV_GET_VARIABLE_UPDATE:
            C.cast(data, C.POINTER(C.c_bool))[0] = False
            return True
        if cmd == ENV_SET_MEMORY_MAPS:
            mmap = C.cast(data, C.POINTER(MemoryMap))[0]
            self.regions = [(d.start, d.len, d.ptr) for d in mmap.descriptors[:mmap.num_descriptors] if d.ptr and d.len]
            return True
        return cmd in ENV_ACCEPTED

    def _video(self, data, width, height, pitch):
        if data:
            self.frame = (data, width, height, pitch)

    def _input(self, port, device, index, button):
        return 1 if port == 0 and device == 1 and button in self.pressed else 0

    def load(self, rom_path):
        self.rom = open(rom_path, "rb").read()
        self.rom_buf = C.create_string_buffer(self.rom, len(self.rom))
        info = GameInfo(rom_path.encode(), C.cast(self.rom_buf, C.c_void_p), len(self.rom), None)
        if not self.lib.retro_load_game(C.byref(info)):
            sys.exit(f"the core refused {rom_path}")

    def unload(self):
        self.lib.retro_unload_game()
        self.regions = []
        self.frame = None

    def run(self, frames, buttons=()):
        self.pressed = {BUTTONS[b] for b in buttons}
        for _ in range(frames):
            self.lib.retro_run()
            self.frames += 1
        self.pressed = set()

    def sram(self):
        size = self.lib.retro_get_memory_size(MEMORY_SAVE_RAM)
        ptr = self.lib.retro_get_memory_data(MEMORY_SAVE_RAM)
        return (ptr, size)

    def get_sram(self):
        ptr, size = self.sram()
        return C.string_at(ptr, size) if ptr and size else b""

    def put_sram(self, data):
        ptr, size = self.sram()
        if ptr and size:
            C.memmove(ptr, data, min(size, len(data)))

    def get_state(self):
        size = self.lib.retro_serialize_size()
        buf = C.create_string_buffer(size)
        if not self.lib.retro_serialize(buf, size):
            sys.exit("retro_serialize failed")
        return buf.raw

    def put_state(self, data):
        buf = C.create_string_buffer(data, len(data))
        if not self.lib.retro_unserialize(buf, len(data)):
            sys.exit("retro_unserialize failed: was the state made from another build of the ROM?")

    def read(self, address, length):
        for start, size, ptr in self.regions:
            if start <= address and address + length <= start + size:
                return C.string_at(ptr + address - start, length)
        raise ValueError(f"0x{address:08x} is not in a mapped RAM region")

    def screen_rgb(self):
        if not self.frame:
            return None
        ptr, width, height, pitch = self.frame
        raw = C.string_at(ptr, pitch * height)
        rows = []
        for y in range(height):
            line = raw[y * pitch:y * pitch + width * (4 if self.pixel_format == 1 else 2)]
            if self.pixel_format == 1:
                rgb = bytearray(width * 3)
                rgb[0::3], rgb[1::3], rgb[2::3] = line[2::4], line[1::4], line[0::4]
            else:
                px = struct.unpack(f"<{width}H", line)
                rgb = bytearray(width * 3)
                for i, p in enumerate(px):
                    if self.pixel_format == 2:
                        r, g, b = p >> 11, (p >> 5) & 0x3F, p & 0x1F
                        rgb[i * 3:i * 3 + 3] = bytes(((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)))
                    else:
                        r, g, b = (p >> 10) & 0x1F, (p >> 5) & 0x1F, p & 0x1F
                        rgb[i * 3:i * 3 + 3] = bytes(((r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2)))
            rows.append(bytes(rgb))
        return width, height, rows


def write_png(path, width, height, rows, scale):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = bytearray()
    for row in rows:
        wide = b"".join(row[i:i + 3] * scale for i in range(0, len(row), 3))
        raw += (b"\x00" + wide) * scale
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width * scale, height * scale, 8, 2, 0, 0, 0)))
        f.write(chunk(b"IDAT", zlib.compress(bytes(raw), 6)))
        f.write(chunk(b"IEND", b""))


def load_symbols(elf, cache_dir):
    """Symbol name → address, and text address → name, from `arm-none-eabi-nm` (cached in the session)."""
    cache = os.path.join(cache_dir, "symbols.nm")
    stamp = f"# {os.path.abspath(elf)} {os.path.getmtime(elf)}\n"
    if not os.path.exists(cache) or open(cache).readline() != stamp:
        try:
            out = subprocess.run(["arm-none-eabi-nm", "-n", elf], check=True, capture_output=True, text=True).stdout
        except (OSError, subprocess.CalledProcessError) as e:
            sys.exit(f"can't read symbols from {elf} ({e}); put arm-none-eabi-nm on PATH")
        with open(cache, "w") as f:
            f.write(stamp + out)
    by_name, by_addr = {}, {}
    for line in open(cache):
        parts = line.split()
        if len(parts) == 3 and not line.startswith("#"):
            addr = int(parts[0], 16)
            name = parts[2].split(".")[0]  # LTO and IPA clones: MainCB2.lto_priv.0, Foo.constprop.0
            by_name.setdefault(name, addr)
            if parts[1] in "tT":
                by_addr.setdefault(addr & ~1, name)
    return by_name, by_addr


class Session:
    def __init__(self, args):
        self.args = args
        self.dir = args.session
        os.makedirs(self.dir, exist_ok=True)
        self.core = Core(args.core, self.dir)
        self.core.load(args.rom)
        self.state_path = os.path.join(self.dir, "state.bin")
        self.sram_path = os.path.join(self.dir, "save.sav")
        elf = os.path.splitext(args.rom)[0] + ".elf"
        self.syms = load_symbols(elf, self.dir) if os.path.exists(elf) else None
        if args.fresh:
            for p in (self.state_path, self.sram_path):
                if os.path.exists(p):
                    os.remove(p)
        if os.path.exists(self.sram_path):
            self.core.put_sram(open(self.sram_path, "rb").read())
        # mGBA reads the save RAM buffer and sends its memory map on the first frame, not at load.
        self.core.run(1)
        if os.path.exists(self.state_path):
            self.core.put_state(open(self.state_path, "rb").read())

    def close(self):
        open(self.sram_path, "wb").write(self.core.get_sram())
        open(self.state_path, "wb").write(self.core.get_state())

    def addr(self, sym):
        if sym.startswith("0x"):
            return int(sym, 16)
        if not self.syms:
            sys.exit("symbol lookup needs the .elf next to the ROM")
        if sym not in self.syms[0]:
            sys.exit(f"unknown symbol {sym}")
        return self.syms[0][sym]

    def cb2(self):
        main = self.addr("gMain")
        ptr = struct.unpack("<I", self.core.read(main + 4, 4))[0]
        return self.syms[1].get(ptr & ~1, f"0x{ptr:08x}")

    def shot(self, name):
        img = self.core.screen_rgb()
        if not img:
            print("shot: no frame drawn yet")
            return
        path = os.path.join(self.dir, name + ".png")
        write_png(path, *img, self.args.scale)
        print(f"shot {path}")

    def reboot(self):
        sram = self.core.get_sram()
        self.core.unload()
        self.core.load(self.args.rom)
        self.core.put_sram(sram)
        self.core.run(1)

    def execute(self, line):
        words = line.split()
        if not words:
            return
        op, rest = words[0], words[1:]
        num = lambda i, d: int(rest[i], 0) if len(rest) > i else d
        if op == "wait":
            self.core.run(num(0, 60))
        elif op == "press":
            self.core.run(num(1, 6), rest[0].upper().split("+"))
            self.core.run(num(2, 20))
        elif op == "hold":
            self.core.run(num(1, 60), rest[0].upper().split("+"))
        elif op == "chord":
            held, button = rest[0].upper(), rest[1].upper()
            self.core.run(4, [held])
            self.core.run(6, [held, button])
            self.core.run(num(2, 20))
        elif op == "mash":
            for _ in range(max(1, num(1, 120) // 12)):
                self.core.run(4, [rest[0].upper()])
                self.core.run(8)
        elif op == "shot":
            self.shot(rest[0])
        elif op == "cb2":
            print(f"cb2 {self.cb2()}")
        elif op in ("until", "mashuntil"):
            button = rest.pop(0).upper() if op == "mashuntil" else None
            target, limit = rest[0], num(1, 3600)
            start = self.core.frames
            while self.cb2() != target:
                if self.core.frames - start >= limit:
                    print(f"FAIL {op} {target}: still {self.cb2()} after {limit} frames")
                    return False
                if button:
                    self.core.run(4, [button])
                    self.core.run(8)
                else:
                    self.core.run(10)
            print(f"ok {target} after {self.core.frames - start} frames")
        elif op in ("read", "deref"):
            address = self.addr(rest[0])
            if op == "deref":
                address = struct.unpack("<I", self.core.read(address, 4))[0]
            address += num(1, 0)
            data = self.core.read(address, num(2, 16))
            print(f"{rest[0]} 0x{address:08x}: {data.hex(' ')}")
        elif op == "reboot":
            self.reboot()
        elif op == "still":
            before = self.core.screen_rgb()
            self.core.run(num(0, 120))
            if before and before == self.core.screen_rgb():
                print(f"FAIL still: the screen didn't change for {num(0, 120)} frames")
                return False
        else:
            sys.exit(f"unknown command {op}")
        return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", help="commands, separated by ';' or newlines; '@file' reads them from a file")
    ap.add_argument("--rom", required=True)
    ap.add_argument("--session", required=True, help="folder for the state, save RAM and screenshots")
    ap.add_argument("--core", default=next((os.path.expanduser(p) for p in DEFAULT_CORES
                                            if os.path.exists(os.path.expanduser(p))), None))
    ap.add_argument("--fresh", action="store_true", help="start from power-on with blank save RAM")
    ap.add_argument("--scale", type=int, default=2)
    args = ap.parse_args()
    if not args.core:
        sys.exit("no libretro core found; pass --core")
    script = open(args.script[1:]).read() if args.script.startswith("@") else args.script
    session = Session(args)
    ok = True
    try:
        commands = [c.strip() for line in script.splitlines() for c in line.split("#", 1)[0].split(";")]
        for command in commands:
            if command and session.execute(command) is False:
                ok = False
                break
    finally:
        session.close()
    print(f"frames {session.core.frames}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
