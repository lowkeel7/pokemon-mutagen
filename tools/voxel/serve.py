#!/usr/bin/env python3
"""Live voxel view (BACKLOG DP-21): the page follows the player in desktop mGBA.

    tools/voxel/serve.py [--rom pokehns.gba] [--http 8765] [--sync 8766] [--out build/voxel]

Then, in mGBA (0.10 or later) with the same build's ROM open: Tools → Scripting… → File → Load
script → `build/voxel/mgba-sync.lua`, and open http://127.0.0.1:8765/ in a browser.

How it works: the Lua script reads the save block's map and the player's object event every
frame (addresses from the build's .elf, so the ROM and the .elf must match) and sends one line,
"group num x y facing", over TCP whenever it changes. This server keeps the last line, serves the
page, and builds a layout's scene (export_map.build_scene) the first time the player enters it.
Nothing of it runs on the GBA or the phone: the ROM is untouched.
"""
import argparse
import base64
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import demo  # noqa: E402
import export_map  # noqa: E402

ROOT = export_map.ROOT
SYMBOLS = ("gSaveBlock1Ptr", "gObjectEvents", "gPlayerAvatar")
MAP_OFFSET = 7           # include/fieldmap.h: object event coordinates carry it
OE_CURRENT_X, OE_CURRENT_Y, OE_FACING = 0x10, 0x12, 0x18   # struct ObjectEvent (include/global.fieldmap.h)
PA_OBJECT_EVENT_ID = 0x05                                   # struct PlayerAvatar


def find_nm():
    nm = shutil.which("arm-none-eabi-nm")
    if nm:
        return nm
    candidate = os.path.expanduser("~/.local/opt/arm-gnu-13.2/bin/arm-none-eabi-nm")
    if os.path.exists(candidate):
        return candidate
    sys.exit("serve: arm-none-eabi-nm not found; put the toolchain's bin on PATH (CLAUDE.md section 1)")


def read_symbols(elf):
    """Addresses and sizes of the symbols the Lua script reads."""
    out = subprocess.run([find_nm(), "-S", elf], capture_output=True, text=True, check=True).stdout
    found = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[3] in SYMBOLS:
            found[parts[3]] = (int(parts[0], 16), int(parts[1], 16))
    missing = [s for s in SYMBOLS if s not in found]
    if missing:
        sys.exit(f"serve: {elf} lacks {', '.join(missing)}")
    return found


def object_events_count():
    with open(os.path.join(ROOT, "include/constants/global.h")) as f:
        match = re.search(r"#define OBJECT_EVENTS_COUNT\s+(\d+)", f.read())
    return int(match.group(1)) if match else 16


def save_block1_location_offset():
    """Offset of SaveBlock1.location (mapGroup, then mapNum): after pos, and after a saveVersion
    when the struct starts with one (Heart & Soul's does)."""
    with open(os.path.join(ROOT, "include/global.h")) as f:
        text = f.read()
    start = text.index("struct SaveBlock1\n")
    body = text[start:text.index("};", start)]
    offset = 0
    if re.search(r"u16 saveVersion;", body) and body.index("saveVersion") < body.index("struct Coords16 pos;"):
        offset += 2
    return offset + 4  # pos is two s16


LUA = """-- mgba-sync.lua, written by tools/voxel/serve.py for {elf}
-- Sends "mapGroup mapNum x y facing" to the voxel view whenever it changes. mGBA 0.10 or later:
-- Tools -> Scripting... -> File -> Load script. The ROM open in mGBA must be the build this .elf is from.
local HOST, PORT = "127.0.0.1", {port}
local SAVE_BLOCK1_PTR = {sb1_ptr}
local LOCATION = {location}
local OBJECT_EVENTS, OBJECT_EVENT_SIZE = {object_events}, {object_event_size}
local PLAYER_AVATAR = {player_avatar}
local sock, last, frames = nil, "", 0

local function connect()
    local s = socket.connect(HOST, PORT)
    if s then
        sock = s
        console:log("voxel: connected to " .. HOST .. ":" .. PORT)
    end
end

local function s16(v)
    if v >= 0x8000 then return v - 0x10000 end
    return v
end

callbacks:add("frame", function()
    frames = frames + 1
    if not sock then
        if frames % 120 == 1 then connect() end
        return
    end
    local sb1 = emu:read32(SAVE_BLOCK1_PTR)
    if sb1 < 0x02000000 or sb1 >= 0x02040000 then return end
    local group = emu:read8(sb1 + LOCATION)
    local num = emu:read8(sb1 + LOCATION + 1)
    local id = emu:read8(PLAYER_AVATAR + {pa_object_event_id})
    if id >= {object_events_count} then return end
    local obj = OBJECT_EVENTS + id * OBJECT_EVENT_SIZE
    local x = s16(emu:read16(obj + {oe_x})) - {map_offset}
    local y = s16(emu:read16(obj + {oe_y})) - {map_offset}
    local facing = emu:read16(obj + {oe_facing}) % 16
    local line = string.format("%d %d %d %d %d\\n", group, num, x, y, facing)
    if line ~= last then
        local ok = pcall(function() sock:send(line) end)
        if ok then
            last = line
        else
            console:log("voxel: connection lost, retrying")
            sock = nil
            last = ""
        end
    end
end)
console:log("voxel: script loaded, connecting to the view at " .. HOST .. ":" .. PORT)
"""


def write_lua(elf, out_dir, sync_port):
    symbols = read_symbols(elf)
    count = object_events_count()
    size = symbols["gObjectEvents"][1] // count
    text = LUA.format(
        elf=os.path.relpath(elf, ROOT),
        port=sync_port,
        sb1_ptr=f"0x{symbols['gSaveBlock1Ptr'][0]:08X}",
        location=save_block1_location_offset(),
        object_events=f"0x{symbols['gObjectEvents'][0]:08X}",
        object_event_size=size,
        object_events_count=count,
        player_avatar=f"0x{symbols['gPlayerAvatar'][0]:08X}",
        pa_object_event_id=PA_OBJECT_EVENT_ID,
        oe_x=OE_CURRENT_X, oe_y=OE_CURRENT_Y, oe_facing=OE_FACING,
        map_offset=MAP_OFFSET,
    )
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "mgba-sync.lua")
    with open(path, "w") as f:
        f.write(text)
    return path, symbols, size


class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.line = None
        self.at = 0.0
        self.scenes = {}

    def update(self, line):
        parts = line.split()
        if len(parts) != 5:
            return
        try:
            group, num, x, y, facing = (int(p) for p in parts)
        except ValueError:
            return
        with self.lock:
            self.line = (group, num, x, y, facing)
            self.at = time.time()

    def snapshot(self):
        with self.lock:
            line, at = self.line, self.at
        if line is None:
            return {"layout": None}
        group, num, x, y, facing = line
        entry = export_map.map_index().get((group, num))
        return {
            "group": group, "num": num, "x": x, "y": y, "dir": facing,
            "facing": export_map.DIRECTIONS.get(facing, "?"),
            "map": entry["name"] if entry else f"map {group}.{num}",
            "layout": entry["layout"] if entry else None,
            "age": round(time.time() - at, 1),
        }

    def scene(self, group, num):
        entry = export_map.map_index().get((group, num))
        if entry is None:
            return None
        layout_id = entry["layout"]
        with self.lock:
            cached = self.scenes.get(layout_id)
        if cached is None:
            started = time.time()
            scene, atlas_png, _, _ = export_map.build_scene(layout_id)
            scene["atlas"] = "data:image/png;base64," + base64.b64encode(atlas_png).decode("ascii")
            cached = json.dumps(scene, separators=(",", ":")).encode()
            with self.lock:
                self.scenes[layout_id] = cached
            print(f"serve: built {layout_id} ({scene['width']}x{scene['height']}) in {time.time() - started:.1f} s", flush=True)
        return cached


STATE = State()

_demo = None


def demo_timeline():
    global _demo
    if _demo is None:
        _demo = demo.timeline()
    return _demo


def bind_sync(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("127.0.0.1", port))
    except OSError as e:
        sys.exit(f"serve: port {port} for the mGBA script is taken ({e.strerror}); pass --sync with a free one")
    server.listen(4)
    return server


def sync_listener(server):
    while True:
        conn, _ = server.accept()
        threading.Thread(target=sync_connection, args=(conn,), daemon=True).start()


def sync_connection(conn):
    print("serve: mGBA connected", flush=True)
    buffer = b""
    with conn:
        while True:
            try:
                data = conn.recv(4096)
            except OSError:
                break
            if not data:
                break
            buffer += data
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                STATE.update(line.decode("ascii", "replace"))
    print("serve: mGBA disconnected", flush=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # quiet
        pass

    def send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]     # /?record=1 is the page too
        if path in ("/", "/index.html"):
            page = export_map.render_page("Pokémon Mutagen", live=True).encode()
            return self.send(200, page, "text/html; charset=utf-8")
        if path == "/state":
            return self.send(200, json.dumps(STATE.snapshot()).encode(), "application/json")
        if path == "/demo":
            timeline = {k: v for k, v in demo_timeline().items() if k != "steps"}
            return self.send(200, json.dumps(timeline, separators=(",", ":")).encode(), "application/json")
        match = re.match(r"^/scene/(\d+)/(\d+)$", path)
        if match:
            body = STATE.scene(int(match.group(1)), int(match.group(2)))
            if body is None:
                return self.send(404, b'{"error":"no such map"}', "application/json")
            return self.send(200, body, "application/json")
        self.send(404, b"not found", "text/plain")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--rom", default=os.path.join(ROOT, "pokehns.gba"), help="the build's ROM; its .elf sits next to it")
    ap.add_argument("--http", type=int, default=8765, help="port of the page (default 8765)")
    ap.add_argument("--sync", type=int, default=8776, help="port the mGBA script connects to (default 8776)")
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "voxel"), help="where mgba-sync.lua is written")
    args = ap.parse_args()
    elf = os.path.splitext(args.rom)[0] + ".elf"
    if not os.path.exists(elf):
        sys.exit(f"serve: {elf} not found next to the ROM (make hns writes it)")
    sync = bind_sync(args.sync)
    lua, symbols, size = write_lua(elf, args.out, args.sync)
    print(f"serve: {lua} (gSaveBlock1Ptr 0x{symbols['gSaveBlock1Ptr'][0]:08X}, object events at "
          f"0x{symbols['gObjectEvents'][0]:08X}, {size} bytes each)")
    threading.Thread(target=sync_listener, args=(sync,), daemon=True).start()
    print(f"serve: 1. open {os.path.relpath(args.rom, ROOT)} in mGBA, Tools → Scripting… → File → Load script → {lua}")
    print(f"serve: 2. open http://127.0.0.1:{args.http}/  (F toggles following the player)")
    print("serve: demo video: tools/voxel/record.py (tools/voxel/README.md)", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.http), Handler).serve_forever()


if __name__ == "__main__":
    main()
