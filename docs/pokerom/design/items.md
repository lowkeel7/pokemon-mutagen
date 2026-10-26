# Species items (SG-09): draft

Status: **draft for review**. Decided: about 6 effect templates; each item is a data row.

## The idea: hold one way, use another
Every species part has two sides:
- **Hold**: one template effect (below), active while held.
- **Use** (consumed): grafts the donor species' type onto the target as its **third type**
  (SG-01/SG-04). That's the Mutagen theme in one rule, and it costs no per-item code. Only works
  with the THIRD TYPE option on; otherwise "Use" is greyed out.

Where they come from: HnS's **WildMonDropItems** option (`tx_Features_WildMonDropItems`) already
drops held items from wild Pokémon, so each part drops from its donor species. Donors that aren't
obtainable in HnS (Gen 4+: Haxorus, Tinkaton, Hoopa, Torterra…) sell at the Rocket black market
(DP-18/19) instead. Poached parts (tusks, antennae) are black-market only.

## Templates
| Code | Hold effect | Engine hook |
|---|---|---|
| ABIL | grants an ability (replaces the holder's while held) | one new hook where the battler's ability is resolved; build first |
| FAM | a move family ×1.2 (punch, slash, stab, bite, sound, wind, ballistic, blunt) | `CalcMoveBasePowerAfterModifiers`, the Punching Glove case |
| SPEC | big boost for its own species line only (like Thick Club) | `GetAttackerItemsModifier` / defender equivalent |
| STAT | a stat ×1.2 for holders of a matching type | stat modifier |
| EVO | evolves or changes form (held at a level, or used) | evolution / form-change tables |
| ING | crafting ingredient only (DP-07) | crafting recipe table |
| MISC | a one-off effect, written by hand | per item; keep these few |

New move flag needed: `stabbingMove` (horn, drill, sting moves). Blunt = `punchingMove` plus a short
list of hammer/body moves. Every non-ING item is also an ingredient.

## The items
| # | Item | Donor (use → type) | Hold | Effect |
|---|---|---|---|---|
| 1 | Cubone Skull | Cubone (Ground) | SPEC | Cubone/Marowak Defense ×1.5. ❓ "Charizard skull" variant: a Fire-type skull for the evolution-cross story |
| 2 | Kabutops Cleavers | Kabutops (Rock) | FAM | slash ×1.2 |
| 3 | Pinsir Horns | Pinsir (Bug) | FAM | stab ×1.2 |
| 4 | Brick | — | EVO | Eevee → ghost Eeveelution (DP-11; needs art) |
| 5 | Shell Core (Cloyster/Clamperl) | Cloyster (Water) | ING | spirit-core ingredient (DP-09) |
| 6 | Starmie Gem | Starmie (Psychic) | FAM | consumed: first Water or Psychic move ×1.3 |
| 7 | Boxing Gloves | Hitmonchan (Fighting) | EVO | Tyrogue holding it at Lv 20 → Hitmonchan; otherwise punch ×1.1 |
| 8 | Victreebel Nectar | Victreebel (Grass) | MISC | consumed: heals ¼ HP below half HP |
| 9 | Empty Bottle | — | ING | container: bottle + nectar / venom / spirit = a vial |
| 10 | Beedrill Stinger | Beedrill (Poison) | FAM | stab ×1.2; stab hits 10% poison |
| 11 | Feathers | birds (Flying) | FAM | wind ×1.2 |
| 12 | Predator Teeth (shark/croc) | Sharpedo, Feraligatr (Water) | FAM | bite ×1.2 |
| 13 | Sceptile Tail | Sceptile (Grass) | STAT | Speed ×1.2 for Grass holders |
| 14 | Beautifly Proboscis | Beautifly (Bug) | MISC | draining moves heal 30% more (Big Root clone) |
| 15 | Bulbasaur Bulb | Bulbasaur (Grass) | STAT | Sp. Def ×1.2 for Grass holders |
| 16 | Arbok Venom | Arbok (Poison) | ABIL | Poison Touch |
| 17 | Sandslash Claws | Sandslash (Ground) | FAM | slash ×1.1 and +1 crit stage |
| 18 | Ninetales Spirit Drop | Ninetales (Fire) | ING | spirit-core ingredient |
| 19 | Diglett Ore | Dugtrio (Ground) | ING | metal for crafting |
| 20 | Alakazam Spoons | Alakazam (Psychic) | SPEC | Abra line Sp. Atk ×1.5 (Twisted Spoon stays for everyone) |
| 21 | Magnemite Core | Magnemite (Electric) | ING | spirit-core ingredient |
| 22 | Leek (exists) | Farfetch'd (Normal) | FAM | adds slash ×1.2 to the existing crit effect; option: its slash moves become Grass |
| 23 | Head Shell (Onix/Aron/Cranidos) | Onix (Rock) | ABIL | Rock Head |
| 24 | Hypno Pendulum | Hypno (Psychic) | MISC | sleep moves' accuracy ×1.2 |
| 25 | Drill Horn | Rhydon (Ground) | FAM | stab ×1.2; Drill Run +1 crit |
| 26 | Dragonite Antenna (poached) | Dragonite (Dragon) | ING | black market only; high sell price |
| 27 | Bayleef Leaf Blade | Bayleef (Grass) | FAM | slash ×1.2 |
| 28 | Togepi Shell | Togepi (Fairy) | ABIL | Serene Grace ❓ (strong; maybe Super Luck) |
| 29 | Sudowoodo Berry | Sudowoodo (Rock) | MISC | consumed: when hit by a Water move, Defense +2 |
| 30 | Heracross Shell | Heracross (Bug) | STAT | Defense ×1.2 for Bug holders |
| 31 | Donphan Tusk (poached) | Donphan (Ground) | FAM | stab ×1.2; black market only |
| 32 | Smeargle Paint | Smeargle (Normal) | MISC | use: teach the target any one move (consumed) |
| 33 | Pupitar Shell | Pupitar (Rock) | ABIL | Shed Skin |
| 34 | Lotad Lily | Lotad (Water) | ABIL | Rain Dish |
| 35 | Shiftry Bark | Shiftry (Grass) | STAT | Defense ×1.2 for Grass holders |
| 36 | Swellow Tail | Swellow (Flying) | ABIL | Guts ❓ |
| 37 | Kirlia Antenna | Kirlia (Psychic) | ABIL | Telepathy |
| 38 | Breloom Cap | Breloom (Grass) | ABIL | Effect Spore |
| 39 | Shedinja Shell | Shedinja (Bug) | MISC | once per battle, survive a hit that isn't super effective with 1 HP (a softer Wonder Guard) |
| 40 | Loudred Ears | Loudred (Normal) | FAM | sound ×1.2 |
| 41 | Hariyama Belt | Hariyama (Fighting) | ABIL | Thick Fat |
| 42 | Sableye Eyes | Sableye (Dark) | ABIL | Keen Eye |
| 43 | Roselia Rose | Roselia (Grass) | ABIL | Natural Cure |
| 44 | Gulpin Bile | Gulpin (Poison) | ING | bottle + bile = Toxin Vial |
| 45 | Sharpedo Skin | Sharpedo (Water) | ABIL | Rough Skin |
| 46 | Spoink Pearl | Spoink (Psychic) | STAT | Sp. Atk ×1.2 for Psychic holders |
| 47 | Compound Eyes (Flygon/Claydol) | Flygon (Ground) | ABIL | Compound Eyes |
| 48 | Cacnea Spikes | Cacnea (Grass) | MISC | consumed on switch-in: one layer of Spikes on the foe's side |
| 49 | Snake Venom | Seviper (Poison) | FAM | bite ×1.1; bite hits 10% poison |
| 50 | Duskull Mask | Duskull (Ghost) | ABIL | Infiltrator; the Skulls' story item (DP-14) |
| 51 | Absol Blade | Absol (Dark) | FAM | slash ×1.1 and +1 crit stage |
| 52 | Heart Scale (exists) | Luvdisc (Water) | — | unchanged (move relearner currency) |
| 53 | Metagross Cross | Metagross (Steel) | ABIL | Clear Body |
| 54 | Torterra Wood | Torterra (Grass) | ING | homestead building material (DP-08) |
| 55 | Empoleon Trident | Empoleon (Water) | FAM | stab ×1.2 |
| 56 | Shinx Star | Shinx (Electric) | STAT | Speed ×1.2 for Electric holders |
| 57 | Bastiodon Shield | Bastiodon (Rock) | ABIL | Sturdy |
| 58 | Skuntank Oil | Skuntank (Poison) | ABIL | Stench |
| 59 | Mamoswine Tusk (poached) | Mamoswine (Ice) | FAM | stab ×1.2; black market only |
| 60 | Dragon Flame | Charmander (Fire → Draco Fire) | EVO | use: Draco Fire third type (needs TYPE ROOTS = FULL); story hook for "the flame goes out" crosses |
| 61 | Spirit Tether | Gengar (Ghost) | EVO | ghost forms (Clefable → Gengar-like); needs art ❓ |
| 62 | Scyther Wings | Scyther (Bug) | ABIL | Technician |
| 63 | Lapras Shell | Lapras (Water) | ABIL | Shell Armor |
| 64 | Mareep Wool | Mareep (Electric) | ABIL | Static; also cloth for wearables (DP-12) |
| 65 | Sunflora Seeds | Sunflora (Grass) | MISC | heals 1/16 per turn in sun |
| 66 | Shuckle Shell | Shuckle (Bug) | STAT | Defense and Sp. Def ×1.1 for any holder |
| 67 | Sneasel Feather | Sneasel (Dark) | ABIL | Pickpocket |
| 68 | Magcargo Shell | Magcargo (Fire) | ABIL | Flame Body |
| 69 | Octillery Cannon | Octillery (Water) | FAM | ballistic ×1.2 |
| 70 | Beast Masks (Entei/Suicune/Raikou) | the beasts | — | cosmetic wearables (DP-12) ❓ |
| 71 | Tropius Bananas | Tropius (Grass) | MISC | consumed: heals ¼ HP below half HP |
| 72 | Spiritomb Spirit | Spiritomb (Ghost → Spirit) | EVO | use: Spirit third type (FULL); possession story (DP-09) |
| 73 | Haxorus Blade | Haxorus (Dragon) | FAM | slash ×1.2 |
| 74 | Tinkaton Hammer | Tinkaton (Fairy) | FAM | blunt ×1.2 |
| 75 | Hoopa Hoop | Hoopa (Psychic) | MISC | key item: story warps (DP-14) |

## Crafted
| Item | Recipe | Effect |
|---|---|---|
| Axe of Hax | Haxorus Blade + Tinkaton Hammer | slash and blunt ×1.2 |
| Fortified Leaf Blade | Bayleef Leaf Blade + Absol Blade | slash ×1.3; Grass slash moves +1 crit |
| Venom / Toxin / Spirit Vial | Empty Bottle + venom / bile / spirit drop | use: badly poison / Septic-coat a move / spirit third type ❓ |

## Build order
1. ABIL hook + FAM flags (unlocks 40 of the rows as data).
2. Third-type USE (needs SG-01).
3. EVO rows; MISC rows one by one; ING after crafting exists.
4. Icons: 24×24, 16 colours, made by hand or taken from credited asset packs (PROVENANCE). No AI art.

## Open for review
The ❓ rows; any item you meant differently; whether a held ABIL item should replace the
holder's ability or add a second one (proposal: replace, which the engine already understands).
