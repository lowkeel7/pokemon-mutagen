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

"Grants an ability from the item slot" (Rock Head from a head shell) needs one hook where the
engine resolves a battler's ability. Build it once, then let every such item be data.

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
