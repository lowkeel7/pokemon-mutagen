---
paths:
  - "graphics/pokemon/**"
  - "src/data/graphics/pokemon.h"
  - "src/data/pokemon/species_info/**"
  - "src/data/pokemon/species_info.h"
  - "src/data/pokemon/species_gfx_ds.h"
  - "src/species_gfx_style.c"
  - "include/species_gfx_style.h"
  - "tools/spritecheck/**"
---

# Pokémon sprites

## Two styles in one ROM (SG-23)

The build is GBA style (`P_GBA_STYLE_SPECIES_GFX` TRUE): Gen 1-3 use the Emerald-era art, Gen 4+
the DS-era art they only have. The SPRITES option (challenge menu, FEATURES; zero = GBA, HnS's
look; `tx_Features_SpriteStyle`) swaps in the DS art of the 393 species that have both, with Gen 4
enemy shadows and female forms.

- Read a Pokémon's battle art through `include/species_gfx_style.h` (`GetSpeciesFrontPic`,
  `GetSpeciesFrontPicYOffset`, `GetSpeciesEnemyMonElevation`, `UseGen4EnemyShadows`…), never
  straight from `gSpeciesInfo`, or DS style shows GBA numbers on DS art.
- `src/data/pokemon/species_gfx_ds.h` is generated. After any change to Pokémon graphics, their
  coordinates or animations: build once with `P_GBA_STYLE_SPECIES_GFX` FALSE, copy the ROM and ELF
  aside, set it back, build, then `tools/spritecheck/gen_ds_style.py --ds-rom <copy>.gba` and
  build again (`--check` exits 1 when the header is stale). Its header has the steps.
- `SHADOW()`/`NO_SHADOW` data is compiled in GBA builds too; DS style needs it.

## Checks

- `tools/spritecheck/spritecheck.py --strict` checks every species in both styles: Y offsets,
  animation frames, shiny palettes, icon palettes, female art, followers. A finding that is right
  as it is goes in `tools/spritecheck/known.txt` with its reason.
- The Y offset is the number of blank rows under the first frame's drawing ("pixels between the drawn
  area and the bottom edge"). It gives Emerald's own front offset for every Gen 1-3 species. One
  offset serves both genders, so a female sprite drawn lower or higher sits off by that much.
- `tools/spritecheck/sheet.py` renders a review page or contact sheets of what the game shows.

## Art

No AI-generated art. New art gets a `docs/pokerom/PROVENANCE.md` row (source, author, terms) and
its bytes in the commit message (CLAUDE.md §4).
