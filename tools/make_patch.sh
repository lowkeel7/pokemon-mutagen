#!/usr/bin/env bash
# Build a BPS patch that turns clean Pokemon Emerald (USA) into pokehns.gba.
#
#   tools/make_patch.sh [rom] [patch]        defaults: pokehns.gba pokehns.bps
#
# Nobody has to supply the base ROM: pret's decompilation rebuilds it bit for
# bit, and the result is checked against the SHA-1 pret and No-Intro publish
# before anything is created from it. The patch is then applied back to that
# base and compared with the ROM, so a patch that would not reproduce the
# build is never written out.
#
# BPS, not IPS: IPS offsets are 24-bit and stop at 16 MiB, the ROM is 32 MiB.
#
# Needs the same toolchain as `make hns` plus g++. Everything it fetches is
# pinned below and cached in $PATCH_CACHE, so later runs only rebuild Flips
# when it is missing and never rebuild Emerald.
set -euo pipefail

ROM=${1:-pokehns.gba}
OUT=${2:-pokehns.bps}
CACHE=${PATCH_CACHE:-$HOME/.cache/pokerom-patch}

# Pinned so the base build cannot drift. The SHA-1 check is what actually
# guarantees the base; the pins only keep it reproducible.
AGBCC_SHA=da598c1d918402c42c0c0d7128ba14567f3175e9
POKEEMERALD_SHA=731ad5bfd6e6f265508d0efcca0ba42f9dcf5881
FLIPS_SHA=ff216a75df0987047a67d7923567dc4482ce07ac
EMERALD_SHA1=f3ae088181bf583e55daf962a92bb46f4f1d07b7

BASE=$CACHE/emerald.gba
FLIPS=$CACHE/flips

log() { printf '[make_patch] %s\n' "$*" >&2; }
die() { log "error: $*"; exit 1; }

fetch_pinned() {  # url sha dir
    rm -rf "$3"
    git init -q "$3"
    git -C "$3" fetch -q --depth 1 "$1" "$2"
    git -C "$3" checkout -q FETCH_HEAD
}

# Portable across Linux and macOS (no sha1sum, nproc or GNU stat on a stock Mac).
sha1() { shasum -a 1 "$1" | cut -d' ' -f1; }
ncpu() { getconf _NPROCESSORS_ONLN; }
bytes() { wc -c <"$1" | tr -d ' '; }

build_base() {
    if [[ -f $BASE && $(sha1 "$BASE") == "$EMERALD_SHA1" ]]; then
        return
    fi
    log "building clean Emerald from pret/pokeemerald (about a minute)"
    local work=$CACHE/src
    mkdir -p "$work"
    fetch_pinned https://github.com/pret/agbcc "$AGBCC_SHA" "$work/agbcc"
    fetch_pinned https://github.com/pret/pokeemerald "$POKEEMERALD_SHA" "$work/pokeemerald"
    local blog=$CACHE/emerald-build.log
    { (cd "$work/agbcc" && ./build.sh && ./install.sh ../pokeemerald) &&
      make -C "$work/pokeemerald" -j"$(ncpu)"; } >"$blog" 2>&1 ||
        { tail -20 "$blog" >&2; die "Emerald build failed, full log in $blog"; }
    local got
    got=$(sha1 "$work/pokeemerald/pokeemerald.gba")
    [[ $got == "$EMERALD_SHA1" ]] || die "rebuilt Emerald has SHA-1 $got, expected $EMERALD_SHA1"
    cp "$work/pokeemerald/pokeemerald.gba" "$BASE"
    rm -rf "$work"
}

build_flips() {
    [[ -x $FLIPS ]] && return
    log "building Flips"
    local work=$CACHE/flips-src
    fetch_pinned https://github.com/Alcaro/Flips "$FLIPS_SHA" "$work"
    # Its Makefile asks git for a version string and complains on a detached
    # checkout; harmless, so only its failure is reported.
    make -C "$work" TARGET=cli >/dev/null 2>&1 || die "Flips build failed"
    cp "$work/flips" "$FLIPS"
    rm -rf "$work"
}

[[ -f $ROM ]] || die "$ROM not found: run 'make hns' first"
mkdir -p "$CACHE"
build_base
build_flips

log "creating $OUT"
"$FLIPS" --create --bps-delta --exact "$BASE" "$ROM" "$OUT" >/dev/null

check=$(mktemp)
trap 'rm -f "$check"' EXIT
"$FLIPS" --apply --exact "$OUT" "$BASE" "$check" >/dev/null
cmp -s "$check" "$ROM" || { rm -f "$OUT"; die "patch does not reproduce $ROM, removed"; }

log "ok: $OUT ($(bytes "$OUT") bytes), base SHA-1 $EMERALD_SHA1, target SHA-1 $(sha1 "$ROM")"
