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
