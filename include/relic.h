#ifndef GUARD_RELIC_H
#define GUARD_RELIC_H

#include "fpmath.h"
#include "constants/relics.h"

// Pokémon Mutagen (SG-09): species parts worn by a Pokémon. A part is put on from the bag, shows on
// the Pokémon's battle sprite and in its summary, and grants its ability whatever the species is.
// Everything is behind MUTAGEN → RELICS (zero = Heart & Soul: the field is kept but does nothing).
//
// Reversible by construction: wearing a part writes nothing but the part's index. Its ability, the
// type it lends, the move family it strengthens and the stat it raises are read while it is worn,
// so taking the part off gives the Pokémon back exactly as it was, and the part goes back to the
// bag; no part is ever used up. The art is each donor's own pixels, cut by tools/relics/cut.py,
// stored compressed and coloured by the donor's palette, which the ROM holds once already.

enum RelicAnchor
{
    RELIC_ANCHOR_HEAD,  // the cell's bottom a little below the head line: hats, crests, horns
    RELIC_ANCHOR_FACE,  // the cell centred over the face: masks, eyes, markings
    RELIC_ANCHOR_BODY,  // the cell centred on the sprite's middle: a shell worn in front, belts, wool
    RELIC_ANCHOR_BACK,  // on the back: rising over the shoulders behind the Pokémon when it faces us, on its back when it faces away
};

// The move families a part can strengthen (FAM rows): the engine's own flags, and two of ours in move.h.
enum RelicFamily
{
    RELIC_FAMILY_NONE,
    RELIC_FAMILY_PUNCH,      // punching moves
    RELIC_FAMILY_SLASH,      // slicing moves
    RELIC_FAMILY_STAB,       // stabbing moves: horns, drills, stings, needles, spears, jabs (stabbingMove)
    RELIC_FAMILY_BITE,       // biting moves
    RELIC_FAMILY_SOUND,      // sound moves
    RELIC_FAMILY_WIND,       // wind moves
    RELIC_FAMILY_BALLISTIC,  // ballistic moves
    RELIC_FAMILY_BLUNT,      // the punches, and hammers, clubs, slams, head and tail blows (bluntMove)
};

// What else a part's family moves do while it is worn.
enum RelicRider
{
    RELIC_RIDER_NONE,
    RELIC_RIDER_CRIT,    // one critical-hit stage more
    RELIC_RIDER_POISON,  // a hit poisons the target one time in ten
};

// The stat a part raises (STAT rows) by the row's boost, for a wearer of the part's type (the type it
// lends: with THIRD TYPE on the part lends it, so every wearer qualifies but one keeping a third type
// of its own) or for any wearer when the row says so.
enum RelicStat
{
    RELIC_STAT_NONE,
    RELIC_STAT_ATK,
    RELIC_STAT_DEF,
    RELIC_STAT_SPATK,
    RELIC_STAT_SPDEF,
    RELIC_STAT_SPEED,
    RELIC_STAT_DEFENSES,  // Defense and Sp. Def both
};

struct RelicInfo  // twelve bytes
{
    u16 item;        // the bag item that puts the part on (and comes back when it is taken off)
    u16 donor;       // the species the part is cut from: its palette colours the art, and a wild one may drop the part
    u16 ability:9;   // enum Ability, granted while worn whatever the species; ABILITY_NONE grants nothing (nine bits hold ABILITIES_COUNT: relic.c asserts it)
    u16 stat:3;      // enum RelicStat, the stat the part raises by `boost`; RELIC_STAT_NONE for none
    u16 typed:1;     // the stat rises only for a wearer of the part's type (GetRelicType); clear, for any wearer
    u16 unused:3;
    u8 anchor:2;     // enum RelicAnchor
    u8 family:4;     // enum RelicFamily, the moves the part strengthens; RELIC_FAMILY_NONE for none
    u8 boost:2;      // by how much the family's moves, or the stat, rise, in tenths: 1 = x1.1, 2 = x1.2, 3 = x1.3
    s8 dy:5;         // nudge in pixels, down from the anchor
    u8 rider:2;      // enum RelicRider
    u8 poached:1;    // no wild donor drops it: the black market's (DP-18)
    const u32 *gfx;  // 32x64 4bpp, smol-compressed: the front view in the top 32x32 cell, the back view below it
};

extern const struct RelicInfo gRelicsInfo[RELICS_COUNT];

u32 RelicFromItem(u16 item);                 // RELIC_NONE if the item is not a part
u32 RelicOfDonor(u16 species);               // the part a wild Pokémon of this species may drop, RELIC_NONE for none
u32 GetMonRelic(struct Pokemon *mon);        // the worn part, RELIC_NONE when the option is off
enum Ability GetRelicAbility(u32 relic);
u32 GetRelicType(u32 relic);                 // the type a worn part lends: its donor's first type; TYPE_NONE for none
u32 GetMonRelicType(struct Pokemon *mon);    // the type the worn part lends this Pokémon, TYPE_NONE when none shows (options off, nothing worn, or the own type kept)

// The move family a part strengthens (battle_util.c reads these on its hot paths). The battler's
// part is cached by SetBattlerThirdType with its types, so each is one byte read and, with
// RELICS off or nothing worn, one test.
u32 GetBattlerRelic(u32 battler);
bool32 IsMoveOfRelicFamily(u32 move, u32 family);
uq4_12_t GetRelicMovePowerModifier(u32 relic, u32 move);  // x1.1, x1.2 or x1.3 for a move of the part's family, x1.0 for any other
u32 GetRelicCritStageIncrease(u32 relic, u32 move);       // 1 when the part's rider is a critical-hit stage and the move is of its family
bool32 RelicPoisonsOnHit(u32 relic, u32 move);            // the part's rider is venom and the move is of its family (one hit in ten poisons; the caller rolls)

// The stat parts: the row's rise of `stat` (STAT_ATK, STAT_DEF, STAT_SPATK, STAT_SPDEF or STAT_SPEED), the
// wearer aside; and the battle's, x1.0 unless the battler wears the part and is of its type (or the row
// takes any wearer). battle_util.c asks on the attack and defence paths, battle_main.c for the Speed.
uq4_12_t GetRelicStatBoost(u32 relic, u32 stat);
uq4_12_t GetBattlerRelicStatModifier(u32 battler, u32 stat);

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
extern const u16 gMonPalette_Kabutops[];
extern const u16 gMonPalette_Pinsir[];
extern const u16 gMonPalette_Beedrill[];
extern const u16 gMonPalette_Pidgeot[];
extern const u16 gMonPalette_Feraligatr[];
extern const u16 gMonPalette_Sandslash[];
extern const u16 gMonPalette_Rhydon[];
extern const u16 gMonPalette_Bayleef[];
extern const u16 gMonPalette_Loudred[];
extern const u16 gMonPalette_Seviper[];
extern const u16 gMonPalette_Absol[];
extern const u16 gMonPalette_Empoleon[];
extern const u16 gMonPalette_Mamoswine[];
extern const u16 gMonPalette_Octillery[];
extern const u16 gMonPalette_Haxorus[];
extern const u16 gMonPalette_Tinkaton[];
extern const u16 gMonPalette_Hitmonchan[];
extern const u16 gMonPalette_Sceptile[];
extern const u16 gMonPalette_Bulbasaur[];
extern const u16 gMonPalette_Heracross[];
extern const u16 gMonPalette_Shiftry[];
extern const u16 gMonPalette_Spoink[];
extern const u16 gMonPalette_Shinx[];
extern const u16 gMonPalette_Shuckle[];

#endif // GUARD_RELIC_H
