---
paths:
  - "src/battle_*.c"
  - "include/battle*.h"
  - "src/data/types_info.h"
  - "include/config/battle.h"
  - "test/battle/**"
---

# Battle engine hooks

Anchors at HnS 2.0.6 (`167aa6d`).

## Types and the third slot
| What | Where |
|---|---|
| `types[3]` | BattlePokemon `pokemon.h:355`; AI_SavedBattleMon `battle.h:175`; macros `battle.h:756-787` |
| loaded on switch-in | `CopyMonAbilityAndTypesToBattleMon`, `battle_util.c:9599-9614` → `GetSpeciesType` (`pokemon.c:5733`; applies the randomizer and the HnS Fairy toggle via `sPreFairyTypes` :5710) |
| slot 3 reset | `Cmd_switchindataupdate` (`battle_script_commands.c:5307`), `FaintClearSetData` (`battle_main.c:3576`) |
| read API | `GetBattlerTypes`, `battle_util.c:9787` |
| type chart | `gTypeEffectivenessTable`, `src/data/types_info.h:14`; read through `GetTypeModifier`, `battle_util.c:8530` |

A persistent third type means storing it per Pokémon (`save.md`), writing it into slot 3 at
switch-in, and keeping the two resets from wiping it: Forest's Curse and Trick-or-Treat use the
same slot, so decide what they do to a Pokémon that already has one.

## Turn order
- `GetBattleMovePriority`, `battle_main.c:5015`: the priority bracket. A new priority rule goes here.
- `GetBattlerTotalSpeedStat`, `battle_main.c:4935`: effective Speed. A new Speed modifier is one line here.
- Prototypes: `battle_main.h:102,104`. Mid-turn recalculation: `B_RECALC_TURN_AFTER_ACTIONS` (`include/config/battle.h`).

## Held items that boost move families
- Move flags: `struct MoveInfo`, `include/move.h:75` (punching :106 … slicing :114); getters such as `IsPunchingMove` :343 and `IsSlicingMove` :383.
- Power hook: the switch in `CalcMoveBasePowerAfterModifiers` (`battle_util.c:6573`; the Punching Glove case at :6844 is the model).
- Contact removal: `IsMoveMakingContact` (:5868-5878). Item stat modifiers: `GetAttackerItemsModifier` (:7656).

## Display switches (`include/config/battle.h`)
`B_SHOW_TYPES` :414 is `SHOW_TYPES_NEVER`; `B_SHOW_EFFECTIVENESS` :420 is ALWAYS. HnS+ turned the
type icons on and aligned the art (`src/type_icons.c`).

## Tests
- `test/battle/{ability,hold_effect,move_effect,ai,…}`. A good model is `test/battle/hold_effect/quick_claw.c`
  (ASSUMPTIONS, then `SINGLE_BATTLE_TEST` with GIVEN/WHEN/SCENE). Many files are `TO_DO_BATTLE_TEST`
  stubs (punching_glove.c): fill the stub when you touch that item.
- Tests override configs in `include/config/test.h`. Plain `make check` builds the Emerald config;
  use `BUILD=hns`. Guide: `docs/tutorials/how_to_testing_system.md`.
- New Pokerom mechanics get tests with the toggle on, and the existing tests must still pass with it off.
