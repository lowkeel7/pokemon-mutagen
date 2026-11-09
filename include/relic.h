#ifndef GUARD_RELIC_H
#define GUARD_RELIC_H

#include "constants/relics.h"

// Pokémon Mutagen (SG-09): species parts worn by a Pokémon. A part is put on from the bag, shows on
// the Pokémon's battle sprite and in its summary, and grants its ability whatever the species is.
// Everything is behind MUTAGEN → RELICS (zero = Heart & Soul: the field is kept but does nothing).

struct RelicInfo
{
    u16 item;             // the bag item that puts the part on (and comes back when it is taken off)
    enum Ability ability; // granted while worn, whatever the species; ABILITY_NONE grants nothing
    const u32 *gfx;       // 32x64 4bpp: the front view in the top 32x32, the back view below it
    const u16 *palette;   // its 16 colours
};

extern const struct RelicInfo gRelicsInfo[RELICS_COUNT];

u32 RelicFromItem(u16 item);                 // RELIC_NONE if the item is not a part
u32 GetMonRelic(struct Pokemon *mon);        // the worn part, RELIC_NONE when the option is off
enum Ability GetRelicAbility(u32 relic);

// The overlay sprite: `frame` is the wearer's decompressed first frame (64x64 4bpp), used to find
// the top of its head. Returns SPRITE_NONE when nothing is worn or nothing can be drawn.
u8 Relic_CreateOverlay(u32 relic, u8 monSpriteId, const u8 *frame, bool32 back, u8 subpriority);

// Battle: one overlay per battler, following its sprite.
void Relic_BattleInit(void);
void Relic_AttachToBattler(u32 battler);
void Relic_DetachFromBattler(u32 battler);

#endif // GUARD_RELIC_H
