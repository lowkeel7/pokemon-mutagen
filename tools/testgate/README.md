# Test gate

`testgate.py` runs RHH's battle and engine tests (`make check BUILD=hns`) with their `MESSAGE()`
checks skipped (`TEST_SKIP_MESSAGES=1`): Heart & Soul prints classic battle text ("restored HP using
its Rain Dish!") where the tests expect Gen 5+ lines, and 1,738 of the 1,924 tests that failed at 2.0.6
failed on that alone. HP bars, animations, ability pop-ups, status icons and `EXPECT_*` still run.

Every failure left is listed in `baseline.txt` with its reason. The run fails on any failure that
isn't listed. `--update` rewrites the list: only when a listed test now passes, or when a change is
meant to alter a test, and the commit says which.

## What the known failures are (TS-02, 2026-10-26)

| Kind | Examples | Why |
|---|---|---|
| Heart & Soul's modes at zero | Fairy Aura, Aura Break, Filter (Prism Armor), Focus Punch vs Sturdy, type plates, Sitrus heal, Harvest | A test save has every challenge setting at 0, which is HnS's "original" mode: no Fairy type, Gen 3 Sturdy and Sitrus Berry, old movepool and legendary abilities. These pass with the RECOMMENDED modes set. |
| Heart & Soul's battle config | spread moves (and Levitate, spread Absorb), Quick Ball, Heavy Ball, missing-badge malus at 250 | `B_MULTIPLE_TARGETS_DMG GEN_3` (×0.5), `B_QUICK_BALL_MODIFIER GEN_3` (×4), `B_HEAVY_BALL_MODIFIER GEN_3`: HGSS-era choices, not bugs. |
| Skipped messages | "Matched ABILITY_POPUP/ANIMATION/STATUS_ICON", Assurance with Life Orb, Misty Terrain | A `NOT {...}` or `captureDamage` that a `MESSAGE()` kept in its place now reaches the wrong event. Judge these with `--strict`, where they fail on HnS's text instead. |
| Data never seen in play | ELECTRIC TERA SHARD, FRESH-START MOCHI and PARABOLIC CHARGE too wide for some boxes; learnsets of disabled species | All-caps names are wider than RHH's; none of those items is placed anywhere in HnS. |
| Probability and AI | about 60 "Expected N passes", 4 AI move choices | Not triaged one by one: HnS's mechanics and AI settings differ; a bug here would show as a change against this list. |
| Not explained yet | Sheer Force (2 moves), trainer party customisation, G-Max Wildfire, Daycare regional forms, Intimidate/Download on an empty field (also at 2.0.6 before any Mutagen change) | Open in BACKLOG TS-02. |

Fixed on the way and gone from the list: zeroed one-type challenge, catch odds reaching 0, Totem
Raticate's form table, the Magnet Train Pass description running out of its box (the description
test now measures HnS's real 109 px window, not RHH's 102), and the save-size tests (now pinned to
Heart & Soul 2.0.6's layout, so a save break fails here).
