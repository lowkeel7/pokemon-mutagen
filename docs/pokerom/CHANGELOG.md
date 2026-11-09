# Pokémon Mutagen changelog

Pokémon Mutagen is a fork of Pokémon Heart & Soul 2.0.6. Changes are listed against that base; for
Heart & Soul's own history see its documentation, and for the engine see `CHANGELOG.md`
(pokeemerald-expansion).

## Unreleased

### Brand and documentation (no change to the ROM)
- Pokémon Mutagen has a look of its own: the MUTAGEN wordmark traced from the title screen's banner,
  a fork mark for "one line becomes two", the banner's greys with a strain magenta and a graft lime,
  Space Grotesk and Silkscreen (both OFL). The README opens on a cover composed from the game's own
  sprites, the documentation site carries the theme with the Mutagen chapters first and a landing
  page, the evolution tree shows the fork on the Mutagen's line, and the videos get title cards and
  captions in the same type. Rules and files: `docs/pokerom/design/brand.md`; generator:
  `tools/brand/brand.py`. Nothing in it is a generated image.
- A **Sprite styles** page on the site shows every Gen 1 to 3 Pokémon in its GBA and DS art side by
  side, with the shiny colours and the DS female forms on toggles (`tools/site/sprites.py`).

### Fixed
- The Mutagen's grafted third type (MUTAGEN → THIRD TYPE) showed in the summary but did not count
  in battle: the battle filled a Pokémon's types from its species at the first send-out and at
  every switch-in and left the third slot empty; only the AI's switch simulation read it. Both
  paths now read the live third type, which the relic tests caught (the first battle tests to
  depend on a third type).
- Day Care: with a LEVEL CAP set, a Pokémon deposited above the cap "grew by 2xx levels" and the
  fee ran to over ¥20,000 (a u8 underflow); the shown level and the fee now follow the capped
  experience the Pokémon really gets. From Heart & Soul+ (Soulgold).
- Battle Pyramid: X items (and other items used on a battler) did nothing from the Pyramid bag.
  From Heart & Soul+ (Soulgold).
- Bug-Catching Contest: an item taken from your lead Pokémon in the park was duplicated when you
  left, and one given there was lost. From Heart & Soul+ (Soulgold).
- A following Pokémon returning to its ball right after a sprite change (surfing, for one) could
  read past its animation table. From Heart & Soul+ (Soulgold).
- Elm's lab: after choosing your starter, walking to the door only ever got "Wait! Where are you
  going?" and a push back, until you thought of talking to Elm. He now goes on with the Mr. Pokémon
  errand right there, as in HeartGold.
- The map-name banner sat its longest names on the frame's flowers, so CHERRYGROVE CITY read as
  "CHERRYGROVE CIT!" on a phone; names wider than the banner's clear area use the narrower face.
- Alolan Dugtrio's Pokédex entry: "heir" → "their" (an unmerged Heart & Soul pull request).
- Sandbox builds: the Pokémon stocked into the PC are now also seen and caught in the Pokédex.
- Evolving into a species with a slower growth curve (Donphan into Great Tusk) no longer drops the
  level: the experience is re-mapped the way the randomizer's evolutions already were.

### New
- **MUTAGEN → RELICS** (OFF, Heart & Soul / ON): species parts a Pokémon can wear. Used from the
  bag on a party Pokémon, a part is worn: it shows on the Pokémon's battle sprite (on the head, over
  the face, around the body or on the back, placed by the shape of the Pokémon's own sprite) and in
  its summary, and it grants its ability whatever the species. Using another part asks to swap it,
  using the same part takes it off, and the part taken off goes back to the bag. Nothing is written
  to the Pokémon but the part's index, so taking a part off gives the Pokémon back exactly as it
  was, and no part is ever used up. **24 parts**: CUBONE SKULL and CHARIZARD SKULL (Rock Head,
  Solar Power), HEAD SHELL (Onix, Rock Head), ARBOK VENOM (Poison Touch), TOGEPI SHELL (Serene
  Grace), PUPITAR SHELL (Shed Skin), LOTAD LILY (Rain Dish), SWELLOW TAIL (Guts), KIRLIA ANTENNA
  (Telepathy), BRELOOM CAP (Effect Spore), HARIYAMA PANTS (Thick Fat), SABLEYE EYES (Keen Eye),
  ROSELIA ROSE (Natural Cure), SHARPEDO SKIN (Rough Skin), FLYGON EYES (Compound Eyes), DUSKULL
  MASK (Infiltrator), METAGROSS CROSS (Clear Body), BASTIODON SHIELD (Sturdy), SKUNTANK OIL
  (Stench), SCYTHER WINGS (Technician), LAPRAS SHELL (Shell Armor), MAREEP WOOL (Static), SNEASEL
  FEATHER (Pickpocket), MAGCARGO SHELL (Flame Body). Every part's art is its donor's own pixels,
  cut from the donor's sprites by a script (the Charizard skull is Cubone's skull in Charizard's
  colours); nothing is drawn. A wild Pokémon of a donor species drops its part one time in four
  when it faints; CHEAT SHELF → ALL sells them all, and the sandbox build starts with one of each.
  With **MUTAGEN → THIRD TYPE** on, a worn part also lends its donor's type as the wearer's third
  type (Lotad Lily: Water; Lapras Shell: Water; Charizard Skull: Fire), shown in the summary and
  counted in battle, for as long as it is worn. A Pokémon that already has a third type of its own
  is asked which to show; its own type is never written over and comes back when the part comes
  off. A worn part also comes off from the party menu (the Pokémon → ITEM → TAKE OFF), so a single
  part is never stuck on. **Seventeen move-family parts** join them: worn, each makes one family of
  moves hit harder (KABUTOPS CLEAVERS, BAYLEEF LEAF BLADE and HAXORUS BLADE: slash ×1.2; PINSIR
  HORNS, DRILL HORN, EMPOLEON TRIDENT and MAMOSWINE TUSK: stab ×1.2; PREDATOR TEETH: bite ×1.2;
  PIDGEOT FEATHERS: wind ×1.2; LOUDRED EARS: sound ×1.2; OCTILLERY CANNON: ballistic ×1.2; TINKATON
  HAMMER: blunt ×1.2, punches included; BOXING GLOVES: punch ×1.1), and a few add something to
  those moves (SANDSLASH CLAWS and ABSOL BLADE: slash ×1.1 and a critical-hit stage; BEEDRILL
  STINGER: stab ×1.2 and SEVIPER VENOM: bite ×1.1, each poisoning one hit in ten). Stab (horns,
  drills, stings, needles, spears, jabs, pecks) and blunt (hammers, clubs, slams, head and tail
  blows) are two move families of Mutagen's own. The Mamoswine tusk is poached: no wild Pokémon
  drops it (it waits for the black market; the sandbox bag and CHEAT SHELF → ALL have it). A part's
  type is its donor's, Flying rather than Normal for a bird. The parts' page: `docs/pokerom/relics.md`.
- **A MUTAGEN tab** in the new-game and PC options, and **GAMEMODE → MUTAGEN** on the new-game
  menu: the recommended settings plus every Mutagen feature switched on in one press. Every row's
  first choice is Heart & Soul's behaviour, and older saves read every row as that.
- **GAMEMODE presets EASY, HARDCORE and MINIMAL GRINDING** beside RECOMMENDED, CUSTOM and MUTAGEN,
  each described on its row: the recommended settings plus a bundle of DIFFICULTY rows (EASY: no
  level cap, double EXP, foes use no battle items, your Pokémon's IVs 31; HARDCORE: a hard level
  cap, no battle items for you, foes with HARD IVs and EVs, EXPERT trainer AI; MINIMAL GRINDING: no
  cap, double EXP, IVs 31 and the CHEAT SHELF on). A preset is a starting point: every row stays
  yours to change.
- **POKÉRUS odds** (MUTAGEN tab): RARE (the main games' 3 in 65,536 battles), UNCOMMON (1 in
  1,024), COMMON (1 in 128) or EPIDEMIC (1 in 16). Above RARE, a wild battle in which a party
  member catches it says so afterwards. It spreads through the party as it always did.
- **TRAINER AI** (MUTAGEN tab): OFF, SMART (every trainer knows your moves and items and switches
  with a plan, the set Emerald Imperium's bosses use) or EXPERT (SMART plus switch and move
  prediction).
- **SHINY TOKEN** (MUTAGEN tab, SHINY TOKENS ON): sold in every Poké Mart for ¥30,000; use one on a
  Pokémon to make it shiny, or on a shiny Pokémon to take its shine away.
- **Any starter** (MUTAGEN tab, STARTER → ANY): touching a Poké Ball in Elm's lab opens a list of
  every Pokémon; pick one and the rest of the scene runs as usual. **SHINY STARTER**: CHANCE (as in
  Heart & Soul), ASK (Elm asks) or ALWAYS.
- **The Mutagen** (MUTAGEN tab, MUTAGEN → ON or RAMPANT): a mutant strain of Pokérus. Wild Pokémon
  at the Lake of Rage, in the Rocket hideouts, Cerulean Cave, the Power Plant and the Burned Tower
  carry it (RAMPANT: everywhere); it is caught eight times as readily as Pokérus, spreads through
  the party like it, lasts four days, and when it ends the Pokémon awakens its hidden ability. Its
  next level up may then evolve it into an Ancient or Future form: Donphan into Great Tusk or Iron
  Treads, Misdreavus into Flutter Mane, Jigglypuff into Scream Tail, Magneton into Sandy Shocks,
  Delibird into Iron Bundle, Hariyama into Iron Hands, Tyranitar into Iron Thorns, Salamence into
  Roaring Moon, Gardevoir into Iron Valiant, Raikou, Entei and Suicune into Raging Bolt, Gouging
  Fire and Walking Wake, Diglett and Dugtrio into Wiglett and Wugtrio, Tentacool and Tentacruel
  into Toedscool and Toedscruel; Farfetch'd into Sirfetch'd, Corsola into Cursola, Mr. Mime into
  Mr. Rime, Meowth into Perrserker, Linoone into Obstagoon, Wooper into Clodsire, Qwilfish into
  Overqwil, Sneasel into Sneasler, Scyther into Kleavor and Gallade into Iron Valiant.
- **New Game+** (MUTAGEN tab, NEW GAME+ → KEEP LV or LEVEL 1): once you have beaten the League, NEW
  GAME on the title screen becomes NEW GAME+, and the new adventure keeps your party and boxes (as
  they are, or every Pokémon back at level 1 with a fresh moveset, as in R.O.W.E.), your whole bag,
  your PC items, money and Pokédex. The story, badges and trainers start over,
  and every wild and trainer Pokémon is one level higher per loop.
- **Discovery** (MUTAGEN tab, DISCOVERY → ON): one wild Pokémon in 128 is a boss, five levels up with
  perfect IVs and its hidden ability, announced as "A powerful wild X appeared!"; and eighteen more
  abilities on your lead Pokémon pull wild Pokémon of their type, the way Static and Magnet Pull
  always have (Blaze for Fire, Torrent for Water, Overgrow for Grass, Swarm for Bug…).
- **Third type** (MUTAGEN tab, THIRD TYPE → ON): when the Mutagen strain runs its course, the
  Pokémon takes on the first type of the Pokémon that passed the strain on as a third type, shown
  as a third icon in its summary and counted in battle. The strain's end is announced after the
  next wild battle, with what it awakened.
- **A CHEATS tab** (fourth tab of the new-game and PC options), every row off by default: CHEAT
  SHELF (ON: every Poké Mart also sells Rare Candies, Master Balls, stones, caps…; ALL: every Poké
  Mart sells every item in the game but the key items), INFINITE PP, CATCH ALWAYS (any ball, its
  own look), MOBILE PC (the POKéMON BOX LINK in your bag), WALK ANYWHERE, WILD BATTLES OFF,
  TRAINERS SEE OFF, POKéDEX COMPLETE.
- **DS-style sprites**: FEATURES → SPRITES switches every Pokémon's battle art between GBA (the
  default, Heart & Soul's look) and DS: DS-era art for the 393 Gen 1-3 species, Gen 4 shadows
  under foes, female forms and the DS-style Substitute doll. Older saves read GBA.

## 0.1.0

First release. Saves from Heart & Soul 2.0.6 load and keep playing.

### New
- **Type icons in battle**: OPTION → BATTLE → TYPE ICONS shows the foe's types next to its health
  bar while you pick a move: OFF (default, as in Heart & Soul), SEEN, CAUGHT (? for species you
  haven't caught) or ALL. Ported from Heart & Soul+.
- The title screen and the ROM header say Pokémon Mutagen 0.1.0.

### Fixed
Game-stopping:
- Birth Island: taking the ship home hung the game on a black screen. The sailor now takes you back
  to Olivine, as the other island sailors do.
- Battle Frontier: walking into either Artisan Cave entrance hung the game. Both entrances are closed
  for now.

Battle and catching:
- Catch odds could drop to zero, making a Pokémon impossible to catch, when it was high level and you
  had few badges. The penalty now makes a catch harder, never impossible.
- Mirror Armor: when the reflected stat drop couldn't lower the attacker any further, the rest of
  the move went on targeting the attacker.
- Bad Dreams' ability pop-up shows on every turn, not only the first.
- Revive (and other half or quarter heals in battle) brings Shedinja back with 1 HP, not 0.
- A Pokémon knocked out by entry hazards as it switches in no longer uses its switch-in ability or
  item (Intimidate, Imposter...).
- Court Change moves the number of hazards along with the hazards, so later hazards stack correctly.

Elsewhere:
- `make release` on the 2.0.6 code kept the developer menus (R + START in the field, SELECT in
  battle), a stray button press away for players; release builds no longer have them.
- Catching a Pokémon after the swap-into-party prompt counts the party correctly.
- Day Care: a foreign father's Everstone no longer passes his species to a different species' Egg.
- After the clock went back (a negative time difference), the in-game date could be a day off,
  giving the wrong weekday's events.
- Headbutt trees keep you in place until their battle starts.
- One Type challenge: a cleared setting no longer counts as "only typeless Pokémon" and sends every
  gift and catch to the PC.

Sprites:
- Gen 4 and later Pokémon show their female sprites again in battle, the summary and the Pokédex
  (36 species, Jellicent, Unfezant, Pyroar, Hippowdon and Garchomp among them, battled as males).
- 44 forms that floated above or sank into their battle platform sit on it: every Unown letter,
  Chimecho, the partner Pikachu and Eevee, Keldeo Resolute and others.
- Minior's Meteor icon is brown, not red, and Keldeo's Resolute form follows you as Keldeo instead
  of a substitute doll.

### Known issues
- Link features (trading, link battles, the Union Room, record mixing) haven't been tested.
- Artisan Cave is closed (see above).
- See the release notes for the result of the hardware check (a flash cart and RetroArch's mGBA
  core on a phone).

### Under the hood
- Builds on macOS without devkitPro; `make check` builds and runs again.
- Battle tests run as a regression gate (`tools/testgate/`), and the game can be played headless in
  RetroArch's mGBA core (`tools/playtest/`), including sweeps over every map and every trainer.
- `tools/release.sh` builds the release and its BPS patch.
