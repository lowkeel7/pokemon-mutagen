#!/usr/bin/env bash
# Build a Pokemon Mutagen release: the release ROM, its checks, and the BPS patch players apply.
#
#   tools/release.sh            version from VERSION; writes release/<version>/
#   tools/release.sh --dirty    allow uncommitted changes (the notes say so)
#
# Writes release/<version>/pokemon-mutagen-<version>.bps, SHA1SUMS and NOTES.md (gitignored).
# Never a ROM: only the patch is published (docs/pokerom/RELEASE.md). The checks it runs are the
# desk half of the release gate; the phone and flash-cart half (BACKLOG HW-01) is done by hand and
# recorded in NOTES.md before publishing.
set -euo pipefail

root=$(git rev-parse --show-toplevel)
cd "$root"
version=$(tr -d ' \n' < VERSION)
out="release/$version"
bps="$out/pokemon-mutagen-$version.bps"
dirty=0
[[ ${1:-} == --dirty ]] && dirty=1

log() { printf '[release] %s\n' "$*" >&2; }
die() { log "error: $*"; exit 1; }
sha1() { shasum -a 1 "$1" | cut -d' ' -f1; }

command -v arm-none-eabi-gcc >/dev/null || die "arm-none-eabi-gcc is not on PATH (CLAUDE.md section 1)"
if ! git diff --quiet || ! git diff --cached --quiet; then
    ((dirty)) || die "uncommitted changes; commit them or pass --dirty"
fi
commit=$(git rev-parse --short HEAD)
mkdir -p "$out"

log "building make release BUILD=hns at $commit"
make release BUILD=hns -j"$(getconf _NPROCESSORS_ONLN)" > "$out/build.log" 2>&1 ||
    { tail -20 "$out/build.log" >&2; die "release build failed, log in $out/build.log"; }
rom=pokehns-release.gba
used=$(python3 -c "import sys; d=open(sys.argv[1],'rb').read(); print(f'{len(d.rstrip(bytes([255]))):,}')" "$rom")
header=$(python3 -c "import sys; d=open(sys.argv[1],'rb').read(); print(d[0xA0:0xAC].rstrip(b'\0').decode(), d[0xAC:0xB0].decode())" "$rom")

smoke="not run (no libretro mGBA core found)"
if python3 -c "import sys; sys.path.insert(0, 'tools/playtest'); import playtest, os; sys.exit(0 if any(os.path.exists(os.path.expanduser(p)) for p in playtest.DEFAULT_CORES) else 1)"; then
    session=$(mktemp -d)
    if python3 tools/playtest/playtest.py --rom "$rom" --session "$session" --fresh @tools/playtest/smoke.txt > "$out/smoke.log" 2>&1; then
        smoke="passed (boot, new game, save, power cycle, continue; mGBA libretro core)"
    else
        tail -5 "$out/smoke.log" >&2
        die "smoke test failed on the release ROM, log in $out/smoke.log"
    fi
    rm -rf "$session"
fi

log "making the patch"
tools/make_patch.sh "$rom" "$bps"

base=f3ae088181bf583e55daf962a92bb46f4f1d07b7
{
    echo "$base  Pokemon - Emerald Version (USA, Europe).gba  (the base ROM to patch)"
    echo "$(sha1 "$rom")  pokemon-mutagen-$version.gba  (what the patch produces)"
    echo "$(sha1 "$bps")  pokemon-mutagen-$version.bps"
} > "$out/SHA1SUMS"

cat > "$out/NOTES.md" <<EOF
# Pokémon Mutagen $version

Built from \`$commit\`$( ((dirty)) && echo ' with uncommitted changes' ) by \`tools/release.sh\`.

| | |
|---|---|
| Patch | \`pokemon-mutagen-$version.bps\` |
| Base ROM | Pokémon Emerald (USA), SHA-1 \`$base\` |
| Patched ROM SHA-1 | \`$(sha1 "$rom")\` |
| ROM header | $header |
| ROM used | $used of 33,554,432 bytes |
| Smoke test | $smoke |
| Patch round trip | passed (make_patch.sh applies it back to the base and compares) |

## Release gate (CLAUDE.md §0), fill in before publishing

| Target | Boot | New game | Save + reload | 10 min play | Save/RTC prompt | Slowdown | Who, when |
|---|---|---|---|---|---|---|---|
| RetroArch mGBA core, phone | | | | | | | |
| Flash cart (model: ) | | | | | | | |

## Changes

See docs/pokerom/CHANGELOG.md, section $version.
EOF

log "done: $out (patch $(wc -c < "$bps" | tr -d ' ') bytes, ROM $used bytes used)"
