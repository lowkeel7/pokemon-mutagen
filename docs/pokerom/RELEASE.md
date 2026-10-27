# Releasing Pokémon Mutagen

A release is a BPS patch, its checksums and its notes. Never a ROM, and never a link to one.

## 1. Before: the desk checks

On the commit to release, with the toolchain on PATH (CLAUDE.md §1):

| Check | Command | Pass |
|---|---|---|
| Battle tests | `tools/testgate/testgate.py` | "no new failures" |
| Every map (dev build) | `make hns`, then `tools/playtest/mapsweep.py --rom pokehns.gba --save <save> --out <dir>` | no new problem since the last release's results (BACKLOG TS-03) |
| Every trainer (dev build) | `tools/playtest/battlesweep.py --rom pokehns.gba --save <save> --out <dir>` | no new problem since the last release's results (BACKLOG TS-05) |
| Sprites | `tools/spritecheck/spritecheck.py --strict` | no finding outside `known.txt` |
| Old saves | `tools/playtest/savecheck.py --out <dir> pokehns.gba pokehns-release.gba` | every save in `tools/playtest/saves/` continues, saves and reloads on both ROMs, read the same on both |

`<save>` is any save that continues into the overworld; `tools/playtest/smoke.txt` makes one in its
`--session` folder. After a release, add a save the release wrote to `tools/playtest/saves/`, so the
next one is checked against it.

The release link prints a few warnings that aren't ours to fix: newlib's `_close`, `_lseek`, `_read`
and `_write` stubs (ARM's toolchain; devkitARM supplies them), a LOAD segment with RWX permissions
(binutils 2.39 and later), and `mystery_gift_client.c` copying 1,024 bytes from a 16-byte script
(pret's and RHH's code too; it only reads ROM). Anything else is new and needs a look.

## 2. Build the release

1. Set `VERSION`. If the title screen's version changes, redraw it in
   `graphics/title_screen/hns/press_start.png` (PROVENANCE has how 0.1.0's was made).
2. Write the version's section in `docs/pokerom/CHANGELOG.md`.
3. `tools/release.sh`: builds `make release BUILD=hns`, runs the smoke test on it in RetroArch's mGBA
   core, makes `release/<version>/pokemon-mutagen-<version>.bps` with `tools/make_patch.sh` (which
   rebuilds clean Emerald, checks its SHA-1, and applies the patch back to compare), and writes
   `SHA1SUMS` and `NOTES.md`.

## 3. The hardware gate (by hand, every release)

Patch a ROM from the `.bps` the way a player would, then on (1) RetroArch's mGBA core on a phone and
(2) a flash cart: boot, start a new game, save, reload, play 10 minutes. Note any save-type or clock
prompt and any slowdown. Fill in the table in `NOTES.md`. A failure here stops the release.

## 4. Publish

Only from the project's own pseudonymous account, after the steps in the clean-room checklist
(`.clean-room/ANONYMITY.md`, private): the placeholder identity rewritten with `git filter-repo
--mailmap`, `git log --format='%an %ae'` checked. Tag `v<version>`, push, and attach the `.bps`,
`SHA1SUMS` and `NOTES.md` to a release. The README's "Play" section tells players the rest.
