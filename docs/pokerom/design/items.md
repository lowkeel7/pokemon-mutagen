# Species items (SG-09): draft

Status: **draft for review; slices 1, 2 and 3 built 2026-11-09** (RELICS option, the worn-part field, the bag
flow, the ability hook, the overlay sprite placed by anchor; all 24 ability parts as data rows with art
cut by `tools/relics/cut.py`; wild donors drop their part; the type a part lends while worn, with the
player's pick when the Pokémon has a third type of its own; `src/relic.c`, the parts' page
[relics.md](../relics.md)). Decided: about 6 effect templates; each item is a data row.

## Two rules every slice keeps (owner, 2026-11-09)
- **Reversible by construction** ("Toffoli", nothing destroyed). Every Mutagen action on a Pokémon has
  an exact inverse, so an undo is always one action away and no information is lost: a part writes
  nothing to the Pokémon but its own index, its ability (and, next, its type) are *read while worn*, so
  taking it off restores the Pokémon exactly; the part returns to the bag; no part is ever used up.
  A third type a part lends is never written over the Pokémon's own: it shows while worn and the own
  one comes back after (the one bit the choice needs records the player's pick, not a type). Where a
  mechanic cannot be inverted in place (evolution), the inverse is a later feature (DP-10 devolution),
  never a silent loss.
- **The ceiling of memory and speed.** ROM: a row is 12 bytes, a part's art is its donor's pixels
  smol-compressed (about 0.5 KB; the 24 parts take 13 KB of art), the palette is the donor's, which
  the ROM holds anyway (none is stored twice, not for the bag icons either). RAM: four bytes of EWRAM
  for the battle's overlays; the Pokémon pays its 6 bits. VRAM: 512 bytes per part on screen (the
  view that is not shown stays in ROM), one palette per kind of part. CPU: placing a part reads the
  wearer's frame once, two pixels a step and one test for a blank byte (about 2,000 steps), at
  send-out; each frame after that the overlay copies five fields from the wearer's sprite; reading
  the worn part costs one `GetMonData`, and nothing at all with RELICS off.

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

## Built: the 24 ability parts (slice 2, 2026-11-09)
What each part shows is a cut of the donor's own sprite, placed by an anchor (`src/relic.c`): HEAD
sits on the head line, FACE over the face, BODY around the middle, BACK at the shoulders and behind
the Pokémon when it faces you. The table and both views of every part: [relics.md](../relics.md).

| Part | Donor | Worn | What shows | Where |
|---|---|---|---|---|
| CUBONE SKULL | Cubone | Rock Head | the skull | head |
| CHARIZARD SKULL | Cubone, in Charizard's colours | Solar Power ❓ (Charizard's hidden ability; Rock Head is taken twice already) | the skull, orange | head |
| HEAD SHELL | Onix | Rock Head | the rock crest of the head | head |
| ARBOK VENOM | Arbok | Poison Touch | the hood's marking | face |
| TOGEPI SHELL | Togepi | Serene Grace | the shell | body |
| PUPITAR SHELL | Pupitar | Shed Skin | the spiked crest | head |
| LOTAD LILY | Lotad | Rain Dish | the lily pad | head |
| SWELLOW TAIL | Swellow | Guts | the tail feathers | back |
| KIRLIA ANTENNA | Kirlia | Telepathy | the two horns | head |
| BRELOOM CAP | Breloom | Effect Spore | the cap | head |
| HARIYAMA PANTS | Hariyama | Thick Fat | the wrap and belt (the owner's word is pants) | body, low |
| SABLEYE EYES | Sableye | Keen Eye | the gem eyes | face |
| ROSELIA ROSE | Roselia | Natural Cure | one rose | head |
| SHARPEDO SKIN | Sharpedo | Rough Skin | the dorsal fin | head |
| FLYGON EYES | Flygon | Compound Eyes | the eye covers, one eye mirrored into two | face |
| DUSKULL MASK | Duskull | Infiltrator | the mask, the eye hole open | face |
| METAGROSS CROSS | Metagross | Clear Body | the steel X | face |
| BASTIODON SHIELD | Bastiodon | Sturdy | the face shield | face |
| SKUNTANK OIL | Skuntank | Stench | the striped tail fur | head |
| SCYTHER WINGS | Scyther | Technician | one wing mirrored into two, crossed at the root | back |
| LAPRAS SHELL | Lapras | Shell Armor | the shell | back |
| MAREEP WOOL | Mareep | Static | the wool | body |
| SNEASEL FEATHER | Sneasel | Pickpocket | the ear feather | head |
| MAGCARGO SHELL | Magcargo | Flame Body | the rock shell | back |

Source: a wild Pokémon of the donor species drops its part one time in four when it faints (RELICS
on); CHEAT SHELF → ALL sells them; the sandbox bag starts with one of each. Parts whose donors are not
wild in Johto and Kanto (Charizard, Bastiodon, Skuntank, Metagross…) wait for the black market
(DP-18/19). A new part is one row and one cut (`tools/relics/cut.py`, the repo's items rule).

## Build order
1. ~~ABIL hook~~ (built) + FAM flags (unlocks the FAM rows as data).
2. ~~Third-type USE~~ → ~~the type a part lends while worn~~ (built 2026-11-09: a worn part's donor type
   shows as the third type while THIRD TYPE is on, read, never written; a Pokémon with a third type of its
   own is asked which to show, the pick is one bit, `relicTypeOff`; off comes the part, back comes the own).
   TAKE OFF in the party menu's ITEM submenu takes a worn part off without a second copy in the bag.
3. EVO rows; MISC rows one by one; ING after crafting exists.
4. ~~Icons~~: every part's icon is its own cut, no asset pack needed.

## Owner's notes (2026-11-09)
- **Worn, not held.** Using a part on a Pokémon puts it *on* the Pokémon: the part shows on its
  battle sprite (front and back) and in the summary, and its ABIL effect applies whatever the
  species is. The example: a Cubone Skull worn by any Pokémon draws the skull on its sprite and
  gives it Rock Head, regardless of the Pokémon's type or anything else. The worn part is a
  per-Pokémon field (one index, 6 bits: up to 63 parts), separate from the held item, so a worn
  part and a held item coexist. Using another part asks to swap; the old one goes back to the bag.
- **The third type is the player's choice.** Whenever a source offers a third type (the Mutagen's
  graft, a part's USE, inheritance) and the Pokémon already has one, the game asks which to keep;
  nothing overwrites a third type silently. Breeding (SG-18): when the parents carry different
  third types, the player chooses which one the egg inherits; one parent's type passes down
  unasked. Evolution keeps the third type (it is per-Pokémon data already).
- Build order, revised: (1) the worn-part field and option (MUTAGEN → RELICS OFF (0) / ON), the
  bag "use" flow with the swap prompt, the ABIL hook in `GetMonAbility` (summary and battle read
  it), the sprite overlay (an extra OAM sprite following the battler as the DS shadows do, anchored
  at the top centre of the first frame's drawn pixels, with a per-species override table for the
  odd shapes), and the Cubone Skull as the first part; its art is cut from Cubone's own sprite
  (PROVENANCE row, no new drawing). (2) The other ABIL rows as data. (3) USE → third type with the
  choice prompt. (4) FAM / STAT / EVO / MISC rows. **Done: (1) and (2), 2026-11-09.** The per-species
  override table became a per-part anchor (head, face, body, back) plus a nudge: the frame's shape
  places the part well enough on every wearer tried.
- The owner's full list arrived again on 2026-11-09 with notes: the Charizard skull variant, the
  Kabutops cleavers as a set, "Hariyama pants", Spoink's "ball", "Hypno circle on string", Sceptile's
  "shed tail", Spirit Tether as Gengar's ghost item, Spiritomb's possession; "crafting later" with the
  Axe of Hax and the Fortified Leaf Blade. And two rules for everything: **the ceiling of memory and
  speed**, and **everything reversible, an undo for every action ("Toffoli gates")**; both above.

## Open for review
The ❓ rows; any item you meant differently; whether a worn ABIL part should replace the
holder's ability or add a second one (proposal: replace, which the engine already understands).
