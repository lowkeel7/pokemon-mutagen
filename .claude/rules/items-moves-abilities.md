---
paths:
  - "include/constants/items.h"
  - "src/data/items.h"
  - "include/constants/hold_effects.h"
  - "src/data/hold_effects.h"
  - "include/constants/moves.h"
  - "src/data/moves_info.h"
  - "include/constants/abilities.h"
  - "src/data/abilities.h"
  - "include/constants/species.h"
  - "src/data/pokemon/**"
  - "src/item_use.c"
---

# Recipes: items, hold effects, moves, abilities, forms

Anchors at HnS 2.0.6 (`167aa6d`). Every new thing also needs a BACKLOG row and, for art, a PROVENANCE line.

## Item
1. Enum before `ITEMS_COUNT`: `include/constants/items.h:1084`.
2. Data: `src/data/items.h` (model: `[ITEM_PUNCHING_GLOVE]` :14930).
3. Icon: `graphics/items/icons/*.png` + `graphics/items/icon_palettes/*.pal`, INCBIN in
   `src/data/graphics/items.h` (:1981), extern in `include/graphics.h` (:1834).
4. Field use: `.fieldUseFunc` in the item data, implemented in `src/item_use.c`, declared in
   `include/item_use.h:10`. PC-anywhere already exists: `ITEM_POKEMON_BOX_LINK` (items.h:875,
   data :14215-14229) → `ItemUseOutOfBattle_PokemonBoxLink` (item_use.c:755-765) →
   `EventScript_AccessPokemonBoxLink` (`data/scripts/pc.inc:176`).

## Hold effect
1. Enum before `HOLD_EFFECT_COUNT`: `include/constants/hold_effects.h:143`.
2. Entry: `src/data/hold_effects.h` (:583).
3. Logic: `src/battle_util.c` (hook sites in `battle.md`); AI: `src/battle_ai_util.c` (:5182);
   debug name: `src/battle_debug.c:2288`.
4. Test under `test/battle/hold_effect/`.

## Worn species part (a relic, SG-09)
The hook exists: `GetMonAbility` (pokemon.c) returns the worn part's ability, so a new ABIL part is
data. `src/relic.c` holds the overlay sprite, the drops' lookup and the battle hooks;
`docs/pokerom/design/items.md` the list of parts, `docs/pokerom/relics.md` the built ones. Two rules
hold for every part: reversible (a part writes nothing but its index, nothing is used up) and lean
(no palette copies, compressed art, a 12-byte row).
1. `X(NAME)` at the end of `RELICS_LIST` in `include/constants/relics.h` (append only: saves store
   the index; 63 parts at most). The enum, the table's bounds and the ability test follow from it.
2. The art spec in `tools/relics/cut.py` `PARTS`: the donor folder, a box of its first front frame
   and one of its back sprite (or `MIRROR`), the palette indices to keep so the part comes away from
   the body, the anchor (HEAD, FACE, BODY, BACK), a nudge, and `drop` boxes for another part of the
   donor sharing the cut (an arm on a shell). `--palettes` prints the indices,
   `--preview --only name` shows the cut on a sample wearer. Then run it: it writes
   `graphics/relics/<part>.png` (32x64, index 0 transparent, the donor's palette) and the bag icon
   `graphics/items/icons/<part>.png`; no `.pal` files, the ROM points both at the donor's
   `gMonPalette_X`. A box of the donor's own pixels, never a drawing; add the donor to the
   PROVENANCE row's list if it is a new one.
3. `const u32 gRelicGfx_X[] = INCBIN_U32("graphics/relics/<part>.4bpp.smol")` in `src/graphics.c`,
   the extern in `include/graphics.h`; the icon likewise in `src/data/graphics/items.h` (no palette
   symbol); the donor's `gMonPalette_X` extern in `include/relic.h` if missing.
4. The item as above with `.fieldUseFunc = ItemUseOutOfBattle_Relic`, `ITEM_USE_PARTY_MENU`,
   `.iconPalette = gMonPalette_<Donor>`; `RelicFromItem` finds the row by the item.
5. The row in `src/data/relics.h`: `RELIC(NAME, ITEM_X, SPECIES_DONOR, ABILITY_Y, RELIC_ANCHOR_Z, dy, Sym)`.
   A move-family part instead: `ABILITY_NONE` and, after `Sym`, `FAM(STAB, 2)` (stab moves ×1.2),
   then `.rider = RELIC_RIDER_CRIT` / `RELIC_RIDER_POISON` or `.poached = TRUE` (no wild drop) as
   needed. A stat part: `ABILITY_NONE` and `STAT(SPEED, 2)` (Speed ×1.2; `DEFENSES` is both defenses)
   with `.typed = TRUE` for a wearer of the part's type only; the battle reads
   `GetBattlerRelicStatModifier` in `CalcAttackStat`, `CalcDefenseStat` (battle_util.c) and
   `GetBattlerTotalSpeedStat` (battle_main.c). A misc part: `ABILITY_NONE` and nothing after `Sym`;
   its one effect is read by its name (`GetBattlerRelic(battler) == RELIC_X`) where the battle needs it
   (the Proboscis in `GetDrainedBigRootHp`, the Pendulum in `GetTotalAccuracy`, the Petals in the end
   turn's `FIRST_EVENT_BLOCK_RELIC`, the Shell in `GetAdjustedDamage` and `CallHangedOnScript`). One donor per part (`RelicOfDonor` is the drop lookup; `test/relic.c` checks both lookups
   and every row's family against the move flags). A new family is a flag in `include/move.h`
   (spare bits, `padding1`), its moves flagged in `src/data/moves_info.h`, one case in
   `IsMoveOfRelicFamily` (relic.c) and one row in `sFamilyMove` (test/relic.c); the battle reads
   `GetBattlerRelic` (a byte cached by `SetBattlerThirdType`) in `CalcMoveBasePowerAfterModifiers`,
   `CalcCritChanceStage` and the attacker's move end (battle_util.c).
6. `tools/relics/cut.py --docs` regenerates the parts' page. `test/battle/relic/abilities.c` covers
   every part's ability from the list, `family.c` one part per move family and the riders, `stat.c`
   the stat parts, `misc.c` the misc parts; a part
   with a second effect gets its own test there.

## Move
1. Enum at `include/constants/moves.h:908` ("Add any custom moves here"); bump `MOVES_COUNT`.
2. Data: `src/data/moves_info.h` (`.effect`, `.battleAnimScript`, flags; example :142).
3. Animation: `gBattleAnimMove_X::` in `data/battle_anim_scripts.s` + `include/battle_anim_scripts.h`.
4. New effect: `include/constants/battle_move_effects.h` + `src/data/battle_move_effects.h`, script in `data/battle_scripts_1.s`.
5. Learnsets: `src/data/pokemon/level_up_learnsets/gen_*.h` and `level_up_learnsets_gen3.c` (the
   HnS Gen 3 movepool option), plus `all_learnables.json` / `tools/learnset_helpers`.
6. Guide: `docs/tutorials/how_to_new_move.md`.

## Ability
1. Enum before `ABILITIES_COUNT`: `include/constants/abilities.h:335-336`.
2. Data: `src/data/abilities.h` (example :1533).
3. Logic: `AbilityBattleEffects` (`battle_util.c:3066`) and the damage modifiers.

## Species form
1. `#define SPECIES_X_FORM` in `include/constants/species.h`; move `SPECIES_EGG` (:1691).
2. Data: `src/data/pokemon/species_info/gen_N_families.h` (example Typhlosion-Hisui `gen_2_families.h:512`).
3. `form_species_tables.h` (:824), `form_change_tables.h`.
4. Gfx: `graphics/pokemon/<mon>/<form>/`, `src/data/graphics/pokemon.h` (:6717), `include/graphics.h`.
   Followers are on, so a form also needs an overworld sprite.
5. Mind the `P_*_FORMS` gates in `include/config/species_enabled.h:9-41`.
6. Guide: `docs/tutorials/how_to_new_pokemon.md`.
