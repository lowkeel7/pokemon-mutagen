# Provenance

Where every piece of Pokerom comes from. Add a row when code, art, music or text arrives from outside
this repo. Never use leaked Game Freak material.

## Credit chain
pret pokeemerald → rh-hideout pokeemerald-expansion → Modern Emerald (resetes12) → Pokémon Heart & Soul
(PokemonHnS-Development; its own credits list in its README and docs) → Pokerom.

## Imported work
| What | From | Commit / version | Author(s) | Terms |
|---|---|---|---|---|
| CI that builds only `hns` and reports ROM fill; BPS patch script (adapted: macOS-portable, renamed cache) | HnS+ (Marcogn/pokehns-expansion-plus) | 08b2f86, 3769c5a, 6701618, 209a8f1 | Marcogn + Claude Code | unstated (public repo, no license) |
| Battle type icons: final `src/type_icons.c` + `include/type_icons.h` (positioning, retract fix, Soulgold-style behaviour) | HnS+ | 3c72554, 79def04 (type-icon half), a58e9cc, 5f6b65b, 9b137be, 1449251; behaviour after Soulgold (Eemeliri) | Marcogn + Claude Code | unstated |
| Title screen: the MUTAGEN banner (`graphics/title_screen/hns/emerald_version.png`) and the `v0.1.0` under PRESS START (`press_start.png`) | HnS's own banner and version pixels | HnS 2.0.6 | U, T, A, E and all the digits, dots and the v reused pixel for pixel from HnS's art; M, G, N and 1 drawn in the same strokes by the coding assistant at the maintainer's request (script: lines up glyph bitmaps, no generated imagery) | as HnS's assets; replace with human-made art when there is some |
