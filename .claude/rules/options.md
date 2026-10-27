---
paths:
  - "src/challenge_menu.c"
  - "src/option_menu.c"
  - "src/oak_speech_hns.c"
  - "include/global.h"
  - "include/option_menu.h"
---

# In-game options: where a Pokerom toggle lives

Two menus, the same table-driven design. Anchors are at HnS 2.0.6 (`167aa6d`).

| | challenge menu | option menu |
|---|---|---|
| file | `src/challenge_menu.c` | `src/option_menu.c` |
| tabs | MODE, FEATURES, RANDOMIZER, NUZLOCKE, DIFFICULTY, CHALLENGES (:35-42) | MAIN, BATTLE, SOUND (:30-35) |
| item enums | :49-135, `MAX_ITEMS_PER_TAB 20` (:138) | :41-78, `MAX_ITEMS_PER_TAB 16` (:80) |
| row tables | `sTabItems_Mode` :425, `_Features` :660, `_Randomizer` :775, `_Nuzlocke` :920, `_Difficulty` :1025, `_Challenges` :1146; `sTabs` :1208 | `sTabItems_Main/Battle/Sound` :372/:453/:498; `sTabs` :535 |
| gating | `CheckConditions` :1273, mid-game locks `sMidGameLockPolicy` :182 | `CheckConditions` :587 |
| save | `Task_ConfirmSaveYes` :1951 | `Task_Save` :1063 (vanilla → SaveBlock2 :1066-1071; "options plus" → ChallengeSettings :1074-1098) |
| load | `CB2_InitChallengeMenu` :2128, block at :2185 | `CB2_InitOptionMenu` :1120, at :1178-1186 |
| opened from | new game `oak_speech_hns.c:637-639`; PC `callnative Script_OpenChallengeMenu` (`data/scripts/pc.inc:85,92`) | start menu |

Storage: `struct ChallengeSettings` bitfields, `include/global.h:253-341`, held in
`SaveBlock3.challengeSettings` (:359).

## Add a toggle
1. Add a bitfield to `ChallengeSettings`. Zero = HnS behaviour (CLAUDE.md §2). HnS fields that
   break that: `tx_Challenges_OneTypeChallenge` (OFF is 31; `IsOneTypeChallengeActive` also reads 0
   as off, so a zeroed save no longer sends every gift to the PC) and `optionStyle` (0 = phys/spec
   split ON, the inverse of its menu row). A test save or `ClearSav3()` leaves every field at 0.
2. Add `ITEM_<TAB>_X` before the tab enum's `_NEXT`/`_COUNT`.
3. Add the row to `sTabItems_<Tab>` (`.name`, `.descriptions`, `.numChoices`, `.choiceNames`) and a `sDesc_*` array.
4. Optional: a lock in `sMidGameLockPolicy` and gating in `CheckConditions`.
5. Write it in the save task and read it in the load block. Options picked from the title screen
   go through `oak_speech_hns.c` and must survive `ClearSav3()` in `NewGameInitData`: add the field
   in both places, or the choice silently disappears.
6. Add an accessor next to the existing ones (challenge_menu.c:2338-2476) and read it at the gameplay site.
7. Check the size: debug menu → ROM Info → "Save Block space".

A Pokerom toggle that is a mechanic (not a difficulty knob) goes in a POKEROM tab once one exists.
Until then, FEATURES. Keep each tab under its `MAX_ITEMS_PER_TAB`.
