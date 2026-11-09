#!/usr/bin/env python3
"""Record the voxel view's demo video (BACKLOG DP-21).

    tools/voxel/serve.py                 # in another terminal, or already running
    tools/voxel/record.py [--out build/voxel/demo.mp4]

Drives a headless Chrome over its DevTools protocol: opens the page with ?record, asks it for one
frame of the demo walk (/demo, see demo.py) at a time, takes a screenshot of each, and feeds them to
ffmpeg (`brew install ffmpeg`), which writes an H.264 .mp4 with the brand's title card first and the
map's name drawn on in the brand's type (tools/brand/brand.py, docs/pokerom/design/brand.md). A second
Chrome with its own profile is started beside the one in use (and closed at the end) unless one
already answers on the DevTools port. Chrome is needed: Mullvad Browser and Tor Browser refuse WebGL
readback. About two minutes for the 30-second walk.
"""
import argparse
import base64
import io
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "brand"))
import export_map  # noqa: E402
import brand  # noqa: E402

ROOT = export_map.ROOT
WIDTH, HEIGHT = 1920, 1080
CARD_SECONDS = 2.5                      # the title card before the walk
TITLE_FONT = os.path.join(brand.FONTS, "SpaceGrotesk-Bold.ttf")
FOOTER_FONT = os.path.join(brand.FONTS, "SpaceGrotesk-Medium.ttf")


# --- a small DevTools client (stdlib only) --------------------------------------------------------

class DevTools:
    def __init__(self, ws_url):
        u = urllib.parse.urlparse(ws_url)
        self.sock = socket.create_connection((u.hostname, u.port), timeout=120)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET {u.path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\nUpgrade: websocket\r\n"
                           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise RuntimeError("DevTools closed the connection during the handshake")
            response += chunk
        if b" 101 " not in response.split(b"\r\n")[0]:
            raise RuntimeError("DevTools refused the websocket: " + response[:120].decode(errors="replace"))
        self.next_id = 0

    def _send(self, text):
        data = text.encode()
        n = len(data)
        header = bytearray([0x81])
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        mask = os.urandom(4)
        header += mask
        self.sock.sendall(bytes(header) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _exact(self, n):
        chunks = []
        while n:
            chunk = self.sock.recv(min(n, 1 << 20))
            if not chunk:
                raise RuntimeError("DevTools closed the connection")
            chunks.append(chunk)
            n -= len(chunk)
        return b"".join(chunks)

    def _recv(self):
        b1, b2 = self._exact(2)
        n = b2 & 0x7F
        if n == 126:
            n = struct.unpack(">H", self._exact(2))[0]
        elif n == 127:
            n = struct.unpack(">Q", self._exact(8))[0]
        if b2 & 0x80:
            self._exact(4)
        return b1 & 0x0F, self._exact(n)

    def call(self, method, **params):
        self.next_id += 1
        self._send(json.dumps({"id": self.next_id, "method": method, "params": params}))
        while True:
            opcode, payload = self._recv()
            if opcode == 8:
                raise RuntimeError("DevTools closed the connection")
            if opcode != 1:
                continue
            message = json.loads(payload)
            if message.get("method") == "Runtime.exceptionThrown":
                details = message["params"]["exceptionDetails"]
                text = details.get("exception", {}).get("description") or details.get("text")
                print(f"record: the page threw: {text}", flush=True)
            if message.get("id") == self.next_id:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message["result"]

    def evaluate(self, expression):
        result = self.call("Runtime.evaluate", expression=expression, returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in result:
            details = result["exceptionDetails"]
            raise RuntimeError("the page threw: " + (details.get("exception", {}).get("description") or details.get("text", "?")))
        return result.get("result", {}).get("value")


def devtools_json(port, path, method="GET"):
    """DevTools' HTTP side; /json/close answers with plain text, which comes back as a string."""
    request = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method=method)
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read()
    try:
        return json.loads(body)
    except ValueError:
        return body.decode("utf-8", "replace")


def chrome_running(port):
    try:
        return devtools_json(port, "/json/version")
    except (urllib.error.URLError, OSError, ValueError):
        return None


def launch_chrome(port, profile):
    """A second Chrome, headless, with its own profile, in the background: `open -n` starts a new
    instance beside the one in use and `-g` keeps the focus where it is."""
    os.makedirs(profile, exist_ok=True)
    subprocess.run(["/usr/bin/open", "-n", "-g", "-a", "Google Chrome", "--args", "--headless=new",
                    f"--remote-debugging-port={port}", f"--user-data-dir={profile}", "--no-first-run",
                    f"--window-size={WIDTH},{HEIGHT}", "about:blank"], check=True)
    for _ in range(60):
        time.sleep(0.5)
        if chrome_running(port):
            return
    sys.exit("record: Chrome did not answer on its DevTools port; is Google Chrome installed?")


# --- the video ------------------------------------------------------------------------------------

def caption_filters(out_dir, segments, offset):
    """drawtext filters in the brand's type: the map's name (with the strain's bar at its left) while
    the walk is on it, the footer line throughout; both after the title card's `offset` frames. The
    texts go through files, so no character needs escaping for the filter graph."""
    if not (os.path.exists(TITLE_FONT) and os.path.exists(FOOTER_FONT)):
        return []
    bone, ash, ink, strain = (brand.C[k].lstrip("#") for k in ("bone", "ash", "ink", "strain"))
    filters = []
    footer = os.path.join(out_dir, "caption-footer.txt")
    with open(footer, "w") as f:
        f.write("Pokémon Mutagen · voxel view")
    filters.append(f"drawtext=fontfile={FOOTER_FONT}:textfile={footer}:fontsize=30:fontcolor=0x{ash}"
                   f":box=1:boxcolor=0x{ink}@0.55:boxborderw=10:x=58:y={HEIGHT - 86}:enable='gte(n,{offset})'")
    for i, segment in enumerate(segments):
        path = os.path.join(out_dir, f"caption-{i}.txt")
        with open(path, "w") as f:
            f.write(segment["map"])
        enable = f"enable='between(n,{segment['start'] + offset},{segment['end'] + offset - 1})'"
        filters.append(f"drawbox=x=48:y=44:w=8:h=80:color=0x{strain}:t=fill:{enable}")
        filters.append(f"drawtext=fontfile={TITLE_FONT}:textfile={path}:fontsize=56:fontcolor=0x{bone}"
                       f":box=1:boxcolor=0x{ink}@0.55:boxborderw=12:x=72:y=56:{enable}")
    return filters


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--http", type=int, default=8765, help="serve.py's port (default 8765)")
    ap.add_argument("--devtools", type=int, default=9222, help="Chrome's DevTools port (default 9222)")
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "voxel", "demo.mp4"))
    ap.add_argument("--profile", default=os.path.join(ROOT, "build", "voxel", "chrome-profile"),
                    help="the headless Chrome's own profile folder")
    args = ap.parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        sys.exit("record: ffmpeg not found (brew install ffmpeg)")
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{args.http}/demo", timeout=120) as response:
            demo = json.load(response)
    except (urllib.error.URLError, OSError) as e:
        sys.exit(f"record: serve.py is not answering on port {args.http} ({e}); start it first")
    frames, fps = len(demo["frames"]), demo["fps"]

    launched = chrome_running(args.devtools) is None
    if launched:
        launch_chrome(args.devtools, args.profile)
    page = devtools_json(args.devtools, f"/json/new?http://127.0.0.1:{args.http}/?record=1", method="PUT")
    tab = DevTools(page["webSocketDebuggerUrl"])
    tab.call("Runtime.enable")
    tab.call("Emulation.setDeviceMetricsOverride", width=WIDTH, height=HEIGHT, deviceScaleFactor=1, mobile=False)
    for _ in range(120):
        if tab.evaluate("document.title") == "ready":
            break
        time.sleep(0.5)
    else:
        sys.exit("record: the page did not get ready (three.js comes from cdnjs: is the Mac online?)")

    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)
    card_frames = int(CARD_SECONDS * fps)
    card = io.BytesIO()
    brand.titlecard((WIDTH, HEIGHT), "voxel view").convert("RGB").save(card, "PNG")
    filters = caption_filters(out_dir, demo["segments"], card_frames)
    command = [ffmpeg, "-y", "-loglevel", "error", "-f", "image2pipe", "-vcodec", "png", "-framerate", str(fps),
               "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", args.out]
    if filters:
        command[-9:-9] = ["-vf", ",".join(filters)]
    log = open(os.path.join(out_dir, "ffmpeg.log"), "w")
    encoder = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=log, stdout=log)
    started = time.time()
    print(f"record: {frames} frames at {fps} fps, {WIDTH}x{HEIGHT} → {args.out}", flush=True)
    for _ in range(card_frames):
        encoder.stdin.write(card.getvalue())
    for k in range(frames):
        tab.evaluate(f"demoStep({k})")
        shot = tab.call("Page.captureScreenshot", format="png", fromSurface=True)
        encoder.stdin.write(base64.b64decode(shot["data"]))
        if (k + 1) % 60 == 0 or k + 1 == frames:
            rate = (k + 1) / (time.time() - started)
            print(f"record: frame {k + 1}/{frames} ({rate:.1f} a second)", flush=True)
    encoder.stdin.close()
    code = encoder.wait()
    log.close()
    devtools_json(args.devtools, f"/json/close/{page['id']}")
    if launched:
        browser = DevTools(chrome_running(args.devtools)["webSocketDebuggerUrl"])
        browser.call("Browser.close")
    if code != 0:
        sys.exit(f"record: ffmpeg exited {code}, see {os.path.join(out_dir, 'ffmpeg.log')}")
    size = os.path.getsize(args.out)
    print(f"record: wrote {args.out} ({size / 1e6:.1f} MB, {(frames + card_frames) / fps:.1f} s) in {time.time() - started:.0f} s")


if __name__ == "__main__":
    main()
