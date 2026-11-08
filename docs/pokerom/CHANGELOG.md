# Pokémon Mutagen changelog

Pokémon Mutagen is a fork of Pokémon Heart & Soul 2.0.6. Changes are listed against that base; for
Heart & Soul's own history see its documentation, and for the engine see `CHANGELOG.md`
(pokeemerald-expansion).

## Unreleased

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

### New
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
