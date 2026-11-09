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
data. `src/relic.c` holds the overlay sprite and the battle hooks; `docs/pokerom/design/items.md`
the list of parts.
1. `RELIC_X` before `RELICS_COUNT` in `include/constants/relics.h` (6 bits per Pokémon: 63 parts at most).
2. A row in `src/data/relics.h`: its item, its ability (`ABILITY_NONE` for none), its art and palette.
3. The item as above (`.fieldUseFunc = ItemUseOutOfBattle_Relic`, `ITEM_USE_PARTY_MENU`); `RelicFromItem` finds the row.
4. Art: `graphics/relics/<part>.png`, a 32x64 4-bit PNG, the front view bottom-aligned in the top
   32x32 cell and the back view in the lower one, index 0 transparent, with `<part>.pal`; INCBIN in
   `src/graphics.c`, externs in `include/graphics.h`. Cut it from the donor's own sprite (a script,
   no drawing) and add the PROVENANCE row. The overlay sits on the wearer's head line (the first row
   of its first frame that is wide enough) with its cell bottom 6 px below it (`RELIC_SINK`).
5. A test in `test/battle/relic/` with `Relic(RELIC_X)` in the PLAYER block and
   `gSaveBlock3Ptr->mutagenSettings.relics = TRUE;` in GIVEN; the same test with the option off.

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
