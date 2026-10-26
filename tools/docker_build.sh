#!/usr/bin/env bash
# Build the hns ROM of a committed ref inside a Linux container, with the same packages CI uses.
# Needs only Docker: no devkitPro, no sudo. The working tree is never written to except the
# output folder, so Linux tool binaries can't end up in it.
#
#   tools/docker_build.sh [ref] [make args...]     defaults: HEAD, then "hns"
#   tools/docker_build.sh feat/qw-01-type-icons
#   tools/docker_build.sh pokerom/dev release BUILD=hns
#
# Output: build/docker/<ref>/pokehns*.gba plus build.log; the ROM fill is printed at the end.
set -euo pipefail

root=$(git rev-parse --show-toplevel)
ref=${1:-HEAD}; shift || true
args=("${@:-hns}")
sha=$(git -C "$root" rev-parse --short "$ref")
out="$root/build/docker/${ref//\//_}"
mkdir -p "$out"

docker run --rm \
    -v "$root:/src:ro" -v "$out:/out" \
    -e REF="$sha" \
    ubuntu:24.04 bash -euo pipefail -c "
        apt-get update -qq >/dev/null
        DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
            git make g++ python3 libpng-dev binutils-arm-none-eabi gcc-arm-none-eabi \
            libnewlib-arm-none-eabi ca-certificates >/dev/null
        git config --global --add safe.directory '*'
        git clone -q /src /build && cd /build && git checkout -q \$REF
        make ${args[*]} -j\$(nproc) UNUSED_ERROR=0 >/out/build.log 2>&1 || { tail -30 /out/build.log; exit 1; }
        cp pokehns*.gba /out/
        python3 - /out/pokehns*.gba <<'PY'
import sys
for p in sys.argv[1:]:
    d = open(p, 'rb').read()
    used = len(d.rstrip(b'\xff'))
    print(f'{p}: {used} of {len(d)} bytes used ({100 * used / len(d):.2f}%), {len(d) - used} free')
PY
    "
echo "ROM in $out (built from $ref @ $sha)"
