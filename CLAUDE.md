# Pokerom — notes for Claude

Fork of Pokémon Heart & Soul 2.0.6 (pokeemerald-expansion 1.15.x). Only what every session needs
is here; each area's detail is in `.claude/rules/<area>.md`, which loads when you open a matching
file. `grep` doesn't trigger a rule, so if you work in an area without opening its files, read the
rule by hand (index in §6).

## 0. Targets (hard requirement)

The product is one `.gba` file that runs on **real GBA hardware (flash cart)** and on **RetroArch's
mGBA core on a phone**. Desktop mGBA is the dev tool, not the target. So:

- Nothing may depend on emulator-only behaviour: no Lua, no mGBA-only debug registers in release
  builds, no reliance on emulator-forgiving timing or open-bus reads.
- 32 MiB ROM cap, FLASH1M save (keep the `FLASH1M_V103` string, `src/agb_flash_1m.c:4`, so carts and
  cores auto-detect the save type). RTC is unreliable on some carts: the HnS `FAKE RTC` option
  (`src/challenge_menu.c:540`) must keep working.
- 60 fps on hardware. Battle/overworld speed-ups, overworld wild Pokémon and new UI must hold frame
  rate on a real ARM7 at 16.78 MHz; the IWRAM audio mixer is a known risk (HnS PR #32).
- Release builds use `make release BUILD=hns` with `DEBUG_OVERWORLD_MENU` FALSE; player cheats go
  through the Pokerom cheat menu only.
- Release gate: boot, save and reload, and play 10 minutes on (1) RetroArch mGBA core on a phone and
  (2) a flash cart, with no save-type or RTC prompt and no slowdown. Record the results in the release notes.

## 1. Build and run

```sh
make hns -j$(sysctl -n hw.ncpu)        # → pokehns.gba. Plain `make` builds Emerald, not HnS.
make hns SANDBOX=1 -j$(sysctl -n hw.ncpu)  # → pokehns-sandbox.gba: a dev build to play with. New games
                                       #   start with Mutagen's options on, every item but key items, full PC boxes
make release BUILD=hns                 # → pokehns-release.gba. `make hns release` silently builds Emerald.
tools/testgate/testgate.py                # battle tests; exit 1 on a failure not in its baseline
tools/spritecheck/spritecheck.py --strict # sprites vs their data; exit 1 on a finding not in known.txt
tools/make_patch.sh pokehns-release.gba   # → BPS against clean Emerald, rebuilt from pret and SHA-1 checked
tools/playtest/playtest.py --rom pokehns.gba --session /tmp/pt --fresh @tools/playtest/smoke.txt
tools/playtest/savecheck.py --out /tmp/saves pokehns.gba pokehns-release.gba  # old saves still load
```

- **The toolchain goes on `PATH`.** Naming it only through `DEVKITARM` or `TOOLCHAIN=` fails on
  macOS, whose make is GNU Make 3.81: its `$(shell)` calls don't see the Makefile's `export PATH`
  and it has no `.SHELLSTATUS`, so `make generated` fails silently and the build dies later on
  `data/battle_partners.h: No such file or directory`. No-sudo route: unpack ARM's
  `arm-gnu-toolchain-13.2.rel1-darwin-arm64-arm-none-eabi.tar.xz` (the GCC that CI's Ubuntu
  packages are built from) anywhere and put its `bin/` on `PATH`. No toolchain at all?
  `tools/docker_build.sh <ref> [make args]` builds a committed ref in an Ubuntu container.
- **Battle tests go through `tools/testgate/testgate.py`.** It runs `make check BUILD=hns` with
  `TEST_SKIP_MESSAGES=1` (HnS prints classic battle text, so `MESSAGE()` checks are skipped; HP,
  animations, abilities and `EXPECT_*` still run) and exits 1 on any failure not listed in
  `tools/testgate/baseline.txt`. Run it before merging engine, battle or item code; `--tests "X"`
  for one area. Use `--update` only when a listed test now passes or a change is meant to alter
  one, and say which in the commit. `--strict` keeps the message checks, report only. On macOS
  `make check` needs coreutils' `stdbuf` (`brew install coreutils`); the script finds it.
- The variant is `$(or $(BUILD),$(MAKECMDGOALS))` (Makefile:21-27). Combine goals only with `BUILD=hns`.
- **Play it headless.** `tools/playtest/playtest.py` runs the ROM in RetroArch's mGBA libretro core
  (the core the phone target uses): scripted buttons, screenshots, `gMain.callback2` by name, and
  save RAM that survives a power cycle. `smoke.txt` is boot → new game → save → power cycle →
  continue; `mapsweep.py` warps to every map and files the ones that don't load (rerun after map
  or script changes; 931 Emerald maps never load here, BACKLOG TS-03). Look at the screen after
  every menu step, and verify the feature you touched with a case that fails without your change.
  Desktop mGBA (`mgba -g` for gdb) works too.
- An unbalanced `#if`/`#endif` shows up as "used but never defined" on unrelated functions.

## 2. The rule: every Pokerom mechanic is a toggle, and zero means HnS

- New behaviour goes behind an in-game option (`.claude/rules/options.md`) or a build flag. The
  vanilla HnS behaviour stays reachable, so RHH's battle tests keep passing and upstream merges
  stay possible.
- **Polarity**: an old save reads zero, so zero must be the old behaviour. Put the zero value's
  label first in the choice list, even when the field name reads awkwardly.
- `IS_HNS` (include/constants/global.h:73-76) is how HnS gates its own code. Config headers load
  before it exists and test `#ifdef POKEMON_HNS`. An `#if IS_HNS / #else` is often where a feature
  is switched off with no flag saying so: check it before writing a feature that may exist.

## 3. Before building anything: does it exist?

In order: `docs/pokerom/BACKLOG.md` (the prior-art column) → the codebase (DexNav, type icons and
the relearner shipped switched off) → `hnsplus/master` (`git log hnsplus/master -- <path>`) → RHH
`master`/`upcoming`. Porting from HnS+ uses the `hnsplus-pick` skill.

## 4. Budgets (measure, don't estimate)

- ROM: 32 MiB cap; HnS uses about 30.2 MiB. Every sprite set, Mega or song is paid from about
  1.8 MiB. Record the before/after bytes in the commit message of anything with art or audio.
- Save: see `.claude/rules/save.md` (spare BoxPokemon bits, SaveBlock limits, free flags/vars).
- `make hns` isn't a release build: a failing `assertf` shows the player a blue screen. Assert only
  on programmer errors, never on reachable states (VRAM full, object table full).

## 5. Content and commits

- No AI-generated art, music or story text in the game. Code may be AI-assisted; the README discloses it.
- Every asset not made here gets a line in `docs/pokerom/PROVENANCE.md` (source, author, terms).
  Never use leaked Game Freak material.
- Commits: English, say what was broken or added, why, and how it was verified. Commit with
  `TZ=UTC git commit`. Update the feature's BACKLOG row in the same commit.
- Work on a branch, never `main` (`main` is untouched HnS 2.0.6).

## 6. Rule index (`.claude/rules/`)

| Rule | Area |
|---|---|
| `options.md` | challenge menu, option menu, ChallengeSettings, adding a toggle |
| `save.md` | Pokémon struct spare bits, SaveBlocks, free flags and vars, save breaks |
| `battle.md` | types and the third slot, speed/priority, type chart, held-item and move-flag hooks, tests |
| `items-moves-abilities.md` | recipes: new item, hold effect, move, ability, species form |
| `debug-cheats.md` | debug menu, cheat entries, release gating |
| `scripts.md` | map scripts, NPCs, trainers, marts, Elite Four, legendaries, trains |
| `sprites.md` | the SPRITES option (GBA/DS), reading battle art, regenerating the DS table, sprite checks |

Repo skills (`.claude/skills/`): `feature` (backlog row → shipped toggle), `hnsplus-pick` (port
one HnS+ feature), `rhh-upgrade` (the P2 engine merge).
