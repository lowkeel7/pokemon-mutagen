# Pokémon Mutagen backlog

Public name: **Pokémon Mutagen** (`pokerom` stays the internal codename for paths and branches).

**Pillars**, in order, to break ties between designs:
1. Maximum configurability: every system is an in-game option, and off means plain HnS.
2. A delight to play: no friction, no grind walls, no bottlenecks.
3. A GBA feel, completely revamped: it should feel like the GBA games you remember, made modern.

Target: one `.gba` that runs on real hardware (flash cart) and on RetroArch's mGBA core on a phone (CLAUDE.md §0). Anything that can't run there is a desktop extra, never part of the game.

Every requested feature, sized and phased. One row per feature. Status changes land here in the
same commit as the code.

**Tier**: `exists` config switch / already in HnS · `S` days · `M` weeks · `L` months, engine
redesign · `C` content (art, maps, writing) · `R` research first.
**Phase**: P1 quick wins on the 1.15 engine · P2 RHH engine upgrade · P3 signature systems ·
P4 deep redesigns + content. Nothing deep lands before P2 (it multiplies merge conflicts).
**Prior art**: `HnS+` = `hnsplus/master` (Marcogn/pokehns-expansion-plus), cherry-pick after review;
`RHH` = arrives with the engine upgrade; `dbg` = already in `src/debug.c`.
**Status**: `todo` · `design` (needs a decision, see ❓) · `wip` · `done` · `cut`.

## P1 — quick wins (1.15 engine)

| ID | Feature | Tier | Prior art / hook | Status |
|---|---|---|---|---|
| QW-01 | Type icons in battle (own + foe), move type + live effectiveness | exists | HnS+ `src/type_icons.c` wiring, `B_SHOW_TYPES` | todo |
| QW-02 | Exp multiplier, Exp to whole party | exists | HnS gamemode options; Gen 6 Exp. Share | todo (verify) |
| QW-03 | Mints | exists | HnS challenge `MINTS` toggle | todo (verify) |
| QW-04 | Random modes: moves / types / abilities / evos / starters | exists | HnS randomizer menu | todo (verify) |
| QW-05 | Multi configurable modes (Nuzlocke, caps, party limit, IV/EV…) | exists | HnS gamemode/difficulty/challenge | todo (verify) |
| QW-06 | Elite Four heals between fights | S | E4 room scripts | todo |
| QW-07 | Buy everything at every shop | S | mart scripts / shop.c, as a ruleset toggle | todo |
| QW-08 | Battle Points from every battle | S | post-battle hook | todo |
| QW-09 | Legendaries in place from day one, all of them (no story gates when on) | S | legendary map scripts + flags; toggle, off = HnS gating | todo |
| QW-10 | Trains / fly open from day one | S | flags at new game, as a toggle | todo |
| QW-11 | HM field moves need no Pokémon | S | field-move party check | todo |
| QW-12 | Fly from roofs and mountains | S | Fly map-type check | todo |
| QW-13 | Mobile PC (key item / start-menu entry) | S | `dbg` "Access PC" call | todo |
| QW-14 | Shiny token (toggle shiny bit) | S | HnS+ Shiny Genome (one-way); make it a toggle | todo |
| QW-15 | Ability token (pick from species' abilities) | S | Ability Capsule/Patch → picker | todo |
| QW-16 | Cheat menu, in-game toggle: every QW-17/18/26 entry plus fly anywhere; save-corrupting debug entries stay dev-only | S | `dbg` cheat entries; HnS+ Easy Catch, party editor | todo |
| QW-17 | Cheats: rare candy / master balls in PC, all TMs/items/berries/battle items, teach any move | S | `dbg` Fill PC Items / Fill Pocket *, relearner | todo (part of QW-16) |
| QW-18 | Cheats: walk through walls, infinite PP, master-ball catch rate (keep ball art) | S | collision test, PP decrement, catch formula; HnS+ Easy Catch | todo |
| QW-19 | Visible natures (summary marker; eye-expression art later) | S | summary screen | todo |
| QW-20 | Pokérus higher chance | S | `include/config/pokerus.h` | todo |
| QW-21 | Pick a partner from a story-character roster (rival, beaten Gym Leaders, Kimono Girls…), manage their team, double battles | exists+S | RHH follower-NPC partner (`FNPC_*`, off in HnS); one script per partner | todo |
| QW-22 | Tutors / trades use PC Pokémon | exists | `OW_CHOOSE_FROM_PC_AND_PARTY` | todo |
| QW-23 | Catch trainers' Pokémon: HnS+ TcloneR as the engine, plus Thief + held ball (the Pokémon throws it, reuse allowed) | exists+S | HnS+ TcloneR (key item) | todo |
| QW-24 | Every HnS+ feature, each behind a toggle (off = HnS): quest book, pause strip, box sort/search, DexNav, overworld wild Pokémon, level scaling, battle/OW speed-up, SwSh party menu, Dark UI, Candy Jar, Fast HMs, battle music theme, Frostbite, item description box, nickname/wild-battle toggles, Red's Path | exists | `hnsplus-pick` | todo |
| QW-25 | Save profiles + version control (tree off a common ancestor) | S | outside the ROM: git repo of `.sav` files | todo |
| HW-01 | Release gate on hardware + phone: RetroArch mGBA core on a phone and a flash cart; save type, RTC/fake RTC, 60 fps, 10-minute play (CLAUDE.md §0) | S | `make release BUILD=hns`, debug menu off | todo (every release) |
| QW-26 | Pokédex "set complete" | S | `dbg` Pokédex flags | todo (part of QW-16) |
| QW-27 | Deoxys forms from the Meteorite (use it to cycle Normal → Attack → Defense → Speed) | exists | `form_change_tables.h:770-791`; Meteorite given on Birth Island (`BirthIsland_Exterior_hns/scripts.inc:116-122`). Verify in mGBA; QW-09 must open Birth Island without the event ticket. Story tie-in: DP-14 | todo (verify) |

## P2 — engine upgrade

| ID | Feature | Tier | Prior art / hook | Status |
|---|---|---|---|---|
| UP-01 | Merge RHH master (1.17.x / 1.18), run `migration_scripts/`, save break | L | `rhh` remote | todo |
| UP-02 | Battle AI strategy for harder modes | exists | RHH `AI_FLAG_*` (smart switch, prediction) | todo after UP-01 |
| UP-03 | Smarter move learning (level/egg/tutor/TM in one menu) | M | RHH 1.16 relearner rework + HnS+ summary relearner | todo after UP-01 |
| UP-04 | Lingering overworld weather after battle weather | M | RHH 1.16 dynamic weather | todo after UP-01 |

## P3 — signature systems (Pokerom ruleset)

| ID | Feature | Tier | Prior art / hook | Status |
|---|---|---|---|---|
| SG-01 | Third type: stored in `teraType:5` (raw 0 = none, so old saves read none; Tera stays off for good), loaded into battle slot 3 | M | `types[3]`; new accessor reads the raw field, not `MON_DATA_TERA_TYPE` (that one defaults to a species type, `pokemon.c:4850`); audit the 16 `MON_DATA_TERA_TYPE` sites | todo |
| SG-02 | Third type: from double-battle partner type | M | post-battle hook | design |
| SG-03 | Third type: from EVs / fighting with off-type moves | M | stat-change / move-use hooks | design |
| SG-04 | Any stone on any Pokémon, each effect a separate option: grant the stone's type as third type; unlock that type's learnset; a stone form/sprite where one exists (needs space); Mega with any type stone (SG-10) | M | item-use hook | todo |
| SG-05 | Third type unlocks extra movesets; type-generic learnsets | M | build-time learnset generation | design |
| SG-06 | Signature moves: each species has a group of 2–4 and picks one at the relearner (swappable, like an ability); some transfer through a third-type match or a stone | M | per-species tables + relearner | design (the per-species groups) |
| SG-07 | More abilities, more moves | M each | RHH new-move/ability docs | design (list needed) |
| SG-08 | Held items boost move families (Punching Glove, Leek → slash, opt. Grass) | S each | move flags punching/slicing/… | todo |
| SG-09 | ~60 custom items on ~6 effect templates (grant ability, boost move family, add third type, evolve/form, crafting ingredient, stat/misc); each item is a data row | M + C | build the template hooks once (ability-from-item hook first), then items as data + icons | design (assign each item a template) |
| SG-10 | Any Pokémon uses other Pokémon's Mega stones / type stones | M | HnS+ `claude/mega-type-stones` branch; needs Megas on (space) | design |
| SG-11 | Permanent Mega, optional revert | M | form-change revert rules | todo after SG-10 |
| SG-12 | Albino variants + curated recolor/shiny palettes | M | 1 spare bit per variant; build-time palette gen | design ❓ space |
| SG-13 | Hexagon IV/EV graph | M | new summary page, polygon into a BG tile buffer | todo |
| SG-14 | EV editing (in-game) | M | HnS+ party editor (debug) → player UI | todo |
| SG-15 | New Game+: keep party, PC, bag, key items, money, Pokédex; reset story flags, badges, trainers, map events; scenes gated on a kept key item are skipped | M | Emerald Enhanced `ClearSav1_NewGamePlus` (keeps less); SaveBlock2 isn't cleared by `NewGameInitData` | todo |
| SG-16 | Pick any starter (dex-style picker) | M | Pokédex list UI | todo |
| SG-17 | Mutant Pokérus (third type, mutations) | M | Pokérus hooks | design |
| SG-18 | Breeding: move + third-type inheritance | M | daycare egg code | todo after SG-01 |
| SG-19 | Custom party size 1–6 | exists | HnS party-limit mode | todo (verify) |
| SG-20 | Make everything configurable in game (config menu) | M | one options screen over HnS options + ruleset | todo |
| SG-21 | Weight classes (5), more egg groups and crosses | S | species data | todo |
| SG-22 | Different Pokédex views | M | HGSS dex already in HnS | design |
| SG-23 | Better / alternate sprite sets | C | per-species sprite option | design ❓ space |

## P4 — deep redesigns and content

| ID | Feature | Tier | Prior art / hook | Status |
|---|---|---|---|---|
| DP-01 | Type tree as a layer: the 18 types stay; each type maps to a root (Mana / Chi / Spirit / Vibration) that adds one matchup step on top of the chart; about 6 new subtypes (Air, Voice/Noise, Mist, Telekinesis, Spirit, Draco fire). Total stays ≤ 32 (fits SG-01's 5 bits) | L | `gTypeEffectivenessTable`, `GetTypeModifier`, AI, type icons; ruleset toggle | design (root chart + subtype list) |
| DP-02 | Physical / special subcategories (blunt, slash, stab, wave / mana, chi, vibration, spirit) | L | move flags as head start | design |
| DP-03 | Move hierarchy (priority rules) | M | `GetBattleMovePriority` | design |
| DP-04 | Status escalation: the same status again upgrades it (paralysis → prone, poison → septic, sleep → coma); bleed is a poison variant from slicing moves. One in-battle tier bit per battler, no save cost | L | status bits, battle scripts, AI | design (tier effects + numbers) |
| DP-05 | Equip slots, second held item, permanent equips (Marowak bone club) | L | save struct + battle hooks | design ❓ save budget |
| DP-06 | Item binding (Slowbro + Shellder, Girafarig) | L | with DP-05 | design |
| DP-07 | Crafting / alchemy (combo items: Axe of Hax, Fortified Leaf Blade) | M | recipe table + menu | design |
| DP-08 | Homestead | M | secret base / room decoration | design |
| DP-09 | Daemon helper spirits, spirit core | C | story + system | design |
| DP-10 | Evolution crosses / devolution, taxonomy-based trees | L | custom evolution methods | design |
| DP-11 | More Eevee evolutions, new species | C | needs artists (no AI art) | design |
| DP-12 | Wearable items on sprites (toggleable) | C | sprite layers, space | design |
| DP-13 | Limb loss in scenario battles, regrown by mutant Pokérus | C | forms + story | design |
| DP-14 | Story: main lines across 3 time periods, Bill's lab time travel | C | maps reused with era palettes | design |
| DP-15 | Side quests per town, rewards | C | HnS+ quest book; HnS quest flags | design |
| DP-16 | Multiple routes to places / key items (no bottlenecks) | C | map + script design | design |
| DP-17 | Puzzles | C | scripts | design |
| DP-18 | Key areas: radio stations, power grid, Rocket black market | C | maps + scripts | design |
| DP-19 | Sell Pokémon (black market), market pricing | M | shop changes | design |
| DP-20 | Hoenn + Johto + Kanto + islands in one ROM | C | Emerald maps in-repo; needs space plan | design ❓ space |
| DP-21 | Voxel overworld as a companion viewer (separate app, mGBA Lua TCP sync; ROM untouched). Desktop mGBA only: RetroArch's core has no Lua, and hardware has neither, so it never reaches the phone or the cart | M | see "Voxel" below | todo (parallel track, desktop extra) |

## Voxel

The voxel mod people mean is *Dramatic Shape* for the Gen 1 PC recompilation: a LÖVE GPU pipeline
with real geometry, a depth buffer and shadow maps. A GBA (ARM7 at 16.78 MHz, tile/sprite PPU, no
GPU) can't run that. Routes, cheapest first:

| Route | What it is | Cost |
|---|---|---|
| Companion viewer | An external app renders the decomp's own map data (`data/layouts`, metatiles) as voxels, synced live from mGBA over Lua TCP (map id, player x/y, facing). The ROM stays a ROM. | M |
| PC port | Build the decomp natively on PC and add a render backend; voxel becomes a real option. | L, research |
| On-GBA pseudo-3D | Affine BG + HBlank scaling for a tilted-plane "Mode 7" overworld. Not voxels; fights the map renderer. | L, low payoff |

## Space and save budgets

Measure before any art lands (`make hns`, then the map file). ROM: about 1.8 MiB free of 32 MiB
(Megas alone measured at 99.46% full in HnS+). Save: 22 spare bits per stored Pokémon. The space
plan (keep or cut the Gen 4–9 randomizer art) is open and blocks SG-10, SG-12, SG-23, DP-11, DP-12,
DP-20.
