#!/usr/bin/env python3
"""Stitch GBA footage into one video in the brand: a title card, then each clip with its caption.

    tools/video/stitch.py build/gameplay/seg --subtitle "gameplay from the dev build" \\
        --out build/gameplay/mutagen-gameplay.mp4

The folder holds NN.mp4 clips as tools/playtest/playtest.py's `record NAME` writes them (960x640,
60 fps, AAC sound) and NN.txt captions, one line each; they are stitched in name order and a clip
without a .txt gets no caption. The title card comes from tools/brand/brand.py at the clips' own
size and plays for 2.5 s in silence. Captions sit in a lower-third band of ink across the frame, in
Space Grotesk with the strain's bar at their left (the band also hides a caption an older cut burnt
into a clip); with --footer, "Pokémon Mutagen · <subtitle>" stays top-left in ash too
(docs/pokerom/design/brand.md).
Segments are re-encoded to one format into <out>/_stitch/ and joined without a second encode. Needs
ffmpeg and ffprobe on PATH (brew install ffmpeg).
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "brand"))
import brand  # noqa: E402

ROOT = brand.ROOT
CARD_SECONDS = 2.5
ENCODE = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
          "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"]


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", path], check=True,
                         capture_output=True, text=True).stdout
    streams = json.loads(out)["streams"]
    video = next(s for s in streams if s["codec_type"] == "video")
    num, den = video["r_frame_rate"].split("/")
    return {"width": int(video["width"]), "height": int(video["height"]), "fps": int(num) / int(den),
            "audio": any(s["codec_type"] == "audio" for s in streams)}


def run(command, log):
    with open(log, "a") as f:
        f.write(" ".join(command) + "\n")
        result = subprocess.run(command, stdout=f, stderr=f)
    if result.returncode != 0:
        sys.exit(f"stitch: ffmpeg exited {result.returncode}, see {log}")


def caption_filters(work, index, caption, footer, width, height):
    """drawtext filters for one clip; the texts go through files so nothing needs escaping."""
    bone, ash, ink, strain = (brand.C[k].lstrip("#") for k in ("bone", "ash", "ink", "strain"))
    bold = os.path.join(brand.FONTS, "SpaceGrotesk-Bold.ttf")
    medium = os.path.join(brand.FONTS, "SpaceGrotesk-Medium.ttf")
    margin = height // 20
    filters = []
    if footer:
        path = os.path.join(work, "footer.txt")
        with open(path, "w") as f:
            f.write(footer)
        size = max(14, height // 32)
        filters.append(f"drawtext=fontfile={medium}:textfile={path}:fontsize={size}:fontcolor=0x{ash}"
                       f":box=1:boxcolor=0x{ink}@0.55:boxborderw=8:x={margin}:y={margin}")
    if caption:
        path = os.path.join(work, f"caption-{index}.txt")
        with open(path, "w") as f:
            f.write(caption)
        size = max(18, height // 22)
        border = size // 3
        band = size + border * 2 + size // 5           # a lower-third band across the frame
        y = height - band
        bar = max(4, size // 5)
        filters.append(f"drawbox=x=0:y={y}:w={width}:h={band}:color=0x{ink}@0.94:t=fill")
        filters.append(f"drawbox=x={margin}:y={y + border}:w={bar}:h={band - border * 2}:color=0x{strain}:t=fill")
        filters.append(f"drawtext=fontfile={bold}:textfile={path}:fontsize={size}:fontcolor=0x{bone}"
                       f":x={margin + bar + border}:y={y + (band - size) // 2 - size // 10}")
    return filters


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("folder", help="the clips: NN.mp4 with NN.txt captions")
    ap.add_argument("--subtitle", default="", help='the title card\'s line and the footer, e.g. "gameplay from the dev build"')
    ap.add_argument("--out", required=True, help="the stitched .mp4")
    ap.add_argument("--no-card", action="store_true", help="skip the title card")
    ap.add_argument("--footer", action="store_true",
                    help='also keep "Pokémon Mutagen · <subtitle>" top-left over the clips (off: it sits on the game\'s own header)')
    args = ap.parse_args()

    clips = sorted(p for p in glob.glob(os.path.join(args.folder, "*.mp4"))
                   if re.match(r"^\d", os.path.basename(p)) and not os.path.basename(p).startswith("00-title"))
    if not clips:
        sys.exit(f"stitch: no NN.mp4 clips in {args.folder}")
    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    work = os.path.join(out_dir, "_stitch")
    os.makedirs(work, exist_ok=True)
    log = os.path.join(work, "ffmpeg.log")
    open(log, "w").close()
    info = probe(clips[0])
    width, height, fps = info["width"], info["height"], info["fps"]
    footer = (f"Pokémon Mutagen · {args.subtitle}" if args.subtitle else "Pokémon Mutagen") if args.footer else ""
    segments = []

    if not args.no_card:
        card = os.path.join(work, "card.png")
        brand.titlecard((width, height), args.subtitle).convert("RGB").save(card)
        segment = os.path.join(work, "seg-00-card.mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-framerate", f"{fps:g}", "-t", str(CARD_SECONDS), "-i", card,
             "-f", "lavfi", "-t", str(CARD_SECONDS), "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
             "-r", f"{fps:g}", "-shortest"] + ENCODE + [segment], log)
        segments.append(segment)

    for i, clip in enumerate(clips, 1):
        name = os.path.splitext(os.path.basename(clip))[0]
        text_path = os.path.join(args.folder, name + ".txt")
        caption = open(text_path).read().strip() if os.path.exists(text_path) else ""
        filters = caption_filters(work, i, caption, footer, width, height)
        segment = os.path.join(work, f"seg-{i:02d}.mp4")
        command = ["ffmpeg", "-y", "-loglevel", "error", "-i", clip]
        if not probe(clip)["audio"]:
            command += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000", "-shortest"]
        if filters:
            command += ["-vf", ",".join(filters)]
        command += ["-r", f"{fps:g}"] + ENCODE + [segment]
        run(command, log)
        segments.append(segment)
        print(f"stitch: {name}: {caption or '(no caption)'}", flush=True)

    manifest = os.path.join(work, "list.txt")
    with open(manifest, "w") as f:
        for segment in segments:
            f.write(f"file '{os.path.abspath(segment)}'\n")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", manifest, "-c", "copy",
         "-movflags", "+faststart", args.out], log)
    duration = sum(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", s],
                                        check=True, capture_output=True, text=True).stdout.strip() or 0) for s in segments)
    print(f"stitch: wrote {args.out} ({os.path.getsize(args.out) / 1e6:.1f} MB, {duration:.1f} s, {len(clips)} clips)")


if __name__ == "__main__":
    main()
