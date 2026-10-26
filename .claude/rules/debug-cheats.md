---
paths:
  - "src/debug.c"
  - "data/scripts/debug.inc"
  - "include/config/debug.h"
  - "src/field_control_avatar.c"
---

# Debug menu and the player-facing cheat menu

Anchors at HnS 2.0.6 (`167aa6d`).

- `struct DebugMenuOption {text, action, actionParams}`: `src/debug.c:203`. Tables :507-743;
  main table `sDebugMenu_Actions_Main` :729; `Debug_ShowMainMenu` :795.
- Add an entry: `{ COMPOUND_STRING("X"), DebugAction_Foo }` in a table, a prototype near :262, and
  the implementation. Or `DebugAction_ExecuteScript, MyScript` with the script in `data/scripts/debug.inc`.
- Opened by the input check in `field_control_avatar.c:165` and :278.

## Existing cheat entries
| Table | Entries |
|---|---|
| Utilities :567 | Fly to map, Warp, Weather, Time, Cheat start (`DebugAction_Util_CheatStart` :1804 → `Debug_CheatStart`, debug.inc:11) |
| PC/Bag :586-605 | Access PC, Fill PC Boxes Fast/Slow, Fill PC Items, Fill each pocket, Clear |
| Party :618 | Heal, Hatch, Pokérus, Set Party, Battle |
| Give :634 | Item, Pokémon, Egg, Max Money/Coins/BP |
| Flags :698 | Pokédex all, fly flags, all badges, collision / encounters / trainer-see off |
| ROM Info :690 | Save Block space |

## Release gating
`make release` sets `-DRELEASE` → `NDEBUG` (`include/config/general.h:11-12`), which only disables
printf and asserts. **The debug menu is not gated on RELEASE**: it stays reachable until
`DEBUG_OVERWORLD_MENU` (`include/config/debug.h:5`) is FALSE. `DEBUG_BATTLE_MENU` (:11) and
`DEBUG_SPRITE_VISUALIZER` (:15) work the same way.

## Pokerom cheat menu (BACKLOG QW-16..18, QW-26)
Ship a curated, player-facing menu, not the raw debug menu: reuse the `DebugAction_*` functions
behind an in-game toggle, then turn the developer debug menu off for releases. Entries that can
corrupt a save (Fill PC Boxes over existing Pokémon, flag editors, Clear) stay developer-only.
Cheats that change rules (walk through walls, infinite PP, guaranteed catch) are toggles read at
their sites: the collision test, the PP decrement, the catch formula.
