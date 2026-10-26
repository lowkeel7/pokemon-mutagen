---
name: rhh-upgrade
description: The P2 engine upgrade, merging rh-hideout pokeemerald-expansion releases into Pokerom one tag at a time with migration scripts. Use for "upgrade the engine", "merge RHH", "pull expansion 1.16/1.17/1.18", or a migration-script error.
---

# rhh-upgrade: 1.15.x → latest, one tag at a time

Do this once, before any P3 system. HnS sits on the 1.15 line (forked from RHH master on
2026-04-29) and is missing two 1.15.2 migration scripts.

```sh
git fetch rhh --tags
git switch -c upgrade/<tag> pokerom/dev
git merge <tag>                       # expansion/1.15.2 → 1.15.3 → 1.16.0 … 1.16.4 → 1.17.0 → 1.17.1; never skip one
python3 migration_scripts/<minor>/<script>.py   # every script the tag added (see migration_scripts/README.md)
make hns -j$(sysctl -n hw.ncpu) && make check BUILD=hns
```

## Per tag
1. Read that tag's changelog, `docs/changelogs/<minor>.x/` on the RHH side, for breaking changes and migration scripts.
2. Merge, resolve conflicts, keeping HnS behaviour (resolution rules below), then run its scripts.
3. Build, run the tests, boot a new game, and load a save from the previous step.
4. Commit the merge with the tag in the message. Tag it locally `pokerom-upgrade/<tag>` as a rollback point.

## Known breakers on the way
| Tag | Breaker |
|---|---|
| 1.15.2 | graphics includes move to INCGFX (`migrate_incgfx.py`); `delete_implicit_waitstates.py` |
| 1.16 | `loadspritegfx` removed from animations; decorations and trainer pics refactored; `gEnemyParty` → `gParties`; wild-encounter config moved |
| 1.17 | Pokédex consolidation: edits in `pokedex_plus_hgss.c` "must be copied manually" (HnS uses the HGSS dex); `MapHeader` struct change; money/coin commands; `givemon` gains an egg argument |

## Conflict rules
- HnS content files (maps, tilesets, music, `*_hns*`) almost never conflict; if one does, HnS wins.
- Engine files: take RHH's structure and re-apply the HnS change on top. Find it with
  `git diff $(git merge-base main rhh/master) main -- <file>`.
- `#if IS_HNS` blocks must survive. After each tag, `grep -c IS_HNS` over src/ and include/ should
  not drop unexplained (536 at 2.0.6).
- Configs in `include/config/*.h`: keep HnS values, add RHH's new switches with RHH defaults, then
  review each new switch against BACKLOG.

## Exit
RHH's tests pass in vanilla mode, the game completes start to Red with the Pokerom toggles off, and
the save break is written up for the release notes. Then set BACKLOG UP-01 to `done`.
