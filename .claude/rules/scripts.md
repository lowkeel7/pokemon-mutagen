---
paths:
  - "data/maps/**"
  - "data/scripts/**"
  - "data/event_scripts.s"
  - "src/data/trainers_hns.party"
  - "include/constants/opponents_hns.h"
  - "src/shop.c"
---

# Event scripts, NPCs, trainers, shops

Anchors at HnS 2.0.6 (`167aa6d`).

- HnS maps are `data/maps/<Map>_hns/` (560 dirs, `"game_version": "hns"`). `tools/mapjson`
  drops maps and layouts of other versions (mapjson.cpp:722-733, :754-761).
- Map scripts are `data/maps/<Map>_hns/scripts.inc`, included from `data/event_scripts.s`, mostly in
  the `.if IS_HNS` block at :1863-2399 (exception: `LilycoveCity_ContestLobby_hns` at :296).
  Shared scripts are in `data/scripts/*.inc`.
- Poryscript is off: its Makefile rules are commented out (:240-241, :434-435, :460-461). Only
  `data/maps/NewSinjoh_hns/scripts.pory` exists. Write `.inc` unless Poryscript is turned on in its own change.

| Task | How |
|---|---|
| NPC | object_event in the map's `map.json` (Porymap), script label in `scripts.inc`; a new map also needs its include and an entry in `data/maps/map_groups.json` |
| Trainer | `#define TRAINER_*_HNS` in `include/constants/opponents_hns.h` (raise `TRAINERS_COUNT_HNS` :678; max :679), a `=== TRAINER_X_HNS ===` party in `src/data/trainers_hns.party` (model: Lance :9247), `trainerbattle_*` in the map script |
| Elite Four | `PokemonLeague_{Wills,Kogas,Brunos,Karens,Champions}Room_hns` (Will's battle `WillsRoom/scripts.inc:62`); shared `data/scripts/elite_four.inc` |
| Marts | `*_Mart_hns` maps call `pokemart 0`; HnS `src/shop.c:359-740` serves stock by badge count (`sShopInventories` :528, PC-challenge `_PC` :728, `SetShopItemsForSale` :988-1000). "Buy everything everywhere" is a toggle in `SetShopItemsForSale` |
| Legendaries | e.g. `WhirlIslands_LugiaChamber_hns` (:172), `TinTower_RoofDay_hns`; helpers `data/scripts/static_pokemon.inc` |
| Train | `GoldenrodCity_TrainStation_hns` (`EventScript_BoardTrain` :27, warp :61), `SaffronCity_TrainStation_hns` |

Script traps that compile fine but fail silently: a metatile from the wrong tileset, an encounter
table that is never registered, a flag reused by another map. After any script change, walk the
scene in mGBA.
