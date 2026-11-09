---
paths:
  - "include/pokemon.h"
  - "include/global.h"
  - "include/save.h"
  - "src/save.c"
  - "src/load_save.c"
  - "src/new_game.c"
  - "include/constants/flags_hns.h"
  - "include/constants/vars_hns.h"
---

# Save data: what is free, and what breaks saves

Anchors at HnS 2.0.6 (`167aa6d`). None of the `unused_*` fields below are referenced in `src/`.

## Per-Pokémon bits (`include/pokemon.h`)
| Where | Free | Notes |
|---|---|---|
| Substruct0 (:129) | `unused_04:2`, `unused_0A:2` | `teraType:5` at :132; reusable only if Tera stays off. `relic:6` (SG-09, was `unused_02:6`) is the worn species part; `relicTypeOff:1` (SG-09, from `unused_04`) keeps the own third type under it |
| Substruct1 | `unused_06:2` | `thirdType:5` (SG-01) and `thirdTypePending:1` (SG-17) claimed, were `unused_04:5` and one bit of `unused_06` |
| Substruct3 | (none) | `isMutagen:1` claimed by SG-17 (was `unused_0B`) |
| BoxPokemon (:255) | `unused_13:1`, `unused_1E:1` | `shinyModifier:1` at :273 |

Total about 8 bits free. Claimed: SG-17 `isMutagen` (Substruct3), SG-01 `thirdType:5` + `thirdTypePending:1` (Substruct1; `teraType` was not usable: CreateBoxMon fills it for every Pokémon), SG-09 `relic:6` + `relicTypeOff:1` (Substruct0, `MON_DATA_RELIC`, `MON_DATA_RELIC_TYPE_OFF`). Planned: variant flags (1 each).
Claim them in BACKLOG before writing code, so two features don't take the same bits.

## Option bits (`struct ChallengeSettings`)
Pinned to exactly 32 bytes (`STATIC_ASSERT`, `src/save.c:94`): never grow it. u8 bitfields don't
straddle bytes, so counting byte by byte: bytes 0-29 are HnS's, byte 30 holds `tx_Features_ShinyChance:4`,
`typeIcons:2` and `tx_Features_SpriteStyle:1`, byte 31 is empty: **9 free bits at the tail** (checked
2026-11-08). Only display options that HnS's option menu saves belong there. Claimed so far:

| Field | Bits | Backlog |
|---|---|---|
| `typeIcons` | 2 | QW-01 |
| `tx_Features_SpriteStyle` | 1 | SG-23 |

Mutagen's own toggles go in `struct MutagenSettings` at the end of SaveBlock3 (QW-29, done
2026-11-08): 32 bytes pinned in `src/save.c`, 24 bits used (`relics:1` for SG-09 took one of byte 1's spare bits), SaveBlock3 now 84 bytes of the 14 × 116
available. Appending there is safe because `src/save.c` zero-fills every sector before writing it
(:210, :235, :346), so a field appended to SaveBlock3 reads zero from an old save; `test/save.c`
pins the size (update it when the struct grows at its end; that is not a save break).

## SaveBlocks
| Block | Struct | Compile-time limit |
|---|---|---|
| SaveBlock1 | `global.h:1198` (HnS adds `momSavings` :1319) | 4 sectors, `src/save.c:96` |
| SaveBlock2 | `global.h:674` | 3968 B, `src/save.c:95` |
| SaveBlock3 | `global.h:343` (ChallengeSettings :359) | 116×14 B, `src/save.c:82` |

- `include/save.h:8-22` `FREE_*` switches reclaim bytes (Trainer Hill, Match Call, Union Room chat…).
- A new SaveBlock3 field goes **at the end** of the struct.
- `NewGameInitData` clears SaveBlock1 and 3 but not SaveBlock2: a game field in SaveBlock2 must be
  cleared by hand, or a new game started over a loaded save inherits it. (This matters for New Game+.)
- Runtime check: debug menu → ROM Info → "Save Block space" (`CheckSaveBlock1/2/3Size`, debug.c:1632-1660).

## Free flags (`include/constants/flags_hns.h`)
- `FLAG_UNUSED_3` 0x2E2 (:816); `FLAG_UNUSED_36..39` 0x304-0x307 (:850-853).
- `FLAG_UNUSED_EXTENDED_33/39/79-99` (:911, :919, :963-983).
- `FLAG_EXTENDED_CONTENT_111..199` (:996-1084): a contiguous placeholder run. 103-110 are set in
  `data/scripts/new_game.inc:374-381`, so they are not free.
- 0x496-0x4FF is reserved (:1187).
- The extended block starts at 0x36A, right after the rematch flags. A 91st rematch trainer
  collides with it (:859-871).

## Free vars (`include/constants/vars_hns.h:110-184`)
- Safe: 0x40B4, C2, C6, C9, CA, D8-DA, DD-E5, F7-FC, FF.
- Conditional: 0x40EC-F0 (secret base); 0x40F2-F6 (PokéNav call counters, live again if their flags get real values).
- Never: 0x40E6-EB, F1, FD, FE.

## Save breaks
Touching the save blocks, `NUM_SPECIES`, or flag/var meanings can break saves. Prefer appending
plus a version-stepped migration on load (HnS+'s `SAVE_VERSION` in `include/save.h` is prior art).
The P2 engine upgrade is the one planned, announced break.
