#ifndef GUARD_RELIC_H
#define GUARD_RELIC_H

#include "constants/relics.h"

// Pokémon Mutagen (SG-09): species parts worn by a Pokémon. A part is put on from the bag, shows on
// the Pokémon's battle sprite and in its summary, and grants its ability whatever the species is.
// Everything is behind MUTAGEN → RELICS (zero = Heart & Soul: the field is kept but does nothing).
//
// Reversible by construction: wearing a part writes nothing but the part's index. Its ability is
// read while it is worn, so taking the part off gives the Pokémon back exactly as it was, and the
// part goes back to the bag; no part is ever used up. The art is each donor's own pixels, cut by
// tools/relics/cut.py, stored compressed and coloured by the donor's palette, which the ROM holds
// once already.

enum RelicAnchor
{
    RELIC_ANCHOR_HEAD,  // the cell's bottom a little below the head line: hats, crests, horns
    RELIC_ANCHOR_FACE,  // the cell centred over the face: masks, eyes, markings
    RELIC_ANCHOR_BODY,  // the cell centred on the sprite's middle: a shell worn in front, belts, wool
    RELIC_ANCHOR_BACK,  // on the back: rising over the shoulders behind the Pokémon when it faces us, on its back when it faces away
};

struct RelicInfo
{
    u16 item;        // the bag item that puts the part on (and comes back when it is taken off)
    u16 donor;       // the species the part is cut from: its palette colours the art, and a wild one may drop the part
    u16 ability;     // enum Ability, granted while worn whatever the species; ABILITY_NONE grants nothing
    u8 anchor:2;     // enum RelicAnchor
    u8 padding:6;
    s8 dy;           // nudge in pixels, down from the anchor
    const u32 *gfx;  // 32x64 4bpp, smol-compressed: the front view in the top 32x32 cell, the back view below it
};

extern const struct RelicInfo gRelicsInfo[RELICS_COUNT];

u32 RelicFromItem(u16 item);                 // RELIC_NONE if the item is not a part
u32 RelicOfDonor(u16 species);               // the part a wild Pokémon of this species may drop, RELIC_NONE for none
u32 GetMonRelic(struct Pokemon *mon);        // the worn part, RELIC_NONE when the option is off
enum Ability GetRelicAbility(u32 relic);

// The overlay sprite: `frame` is the wearer's decompressed first frame (64x64 4bpp), which places
// the part. Returns SPRITE_NONE when nothing is worn or nothing can be drawn.
u8 Relic_CreateOverlay(u32 relic, u8 monSpriteId, const u8 *frame, bool32 back, u8 subpriority);

// Battle: one overlay per battler, following its sprite.
void Relic_BattleInit(void);
void Relic_AttachToBattler(u32 battler);
void Relic_DetachFromBattler(u32 battler);

// The donors' palettes (src/data/graphics/pokemon.h), which also colour the parts' bag icons.
extern const u16 gMonPalette_Cubone[];
extern const u16 gMonPalette_Charizard[];
extern const u16 gMonPalette_Onix[];
extern const u16 gMonPalette_Arbok[];
extern const u16 gMonPalette_Togepi[];
extern const u16 gMonPalette_Pupitar[];
extern const u16 gMonPalette_Lotad[];
extern const u16 gMonPalette_Swellow[];
extern const u16 gMonPalette_Kirlia[];
extern const u16 gMonPalette_Breloom[];
extern const u16 gMonPalette_Hariyama[];
extern const u16 gMonPalette_Sableye[];
extern const u16 gMonPalette_Roselia[];
extern const u16 gMonPalette_Sharpedo[];
extern const u16 gMonPalette_Flygon[];
extern const u16 gMonPalette_Duskull[];
extern const u16 gMonPalette_Metagross[];
extern const u16 gMonPalette_Bastiodon[];
extern const u16 gMonPalette_Skuntank[];
extern const u16 gMonPalette_Scyther[];
extern const u16 gMonPalette_Lapras[];
extern const u16 gMonPalette_Mareep[];
extern const u16 gMonPalette_Sneasel[];
extern const u16 gMonPalette_Magcargo[];

#endif // GUARD_RELIC_H
