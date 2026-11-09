#include "global.h"
#include "test/battle.h"
#include "relic.h"

// Pokémon Mutagen (SG-09): a worn Cubone Skull grants Rock Head whatever the species, behind the
// MUTAGEN → RELICS option (zero = Heart & Soul: the part does nothing).

SINGLE_BATTLE_TEST("Cubone Skull: the wearer takes no recoil, as with Rock Head (RELICS on)")
{
    GIVEN {
        ASSUME(GetMoveRecoil(MOVE_TAKE_DOWN) > 0);
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_WOBBUFFET) { Relic(RELIC_CUBONE_SKULL); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_TAKE_DOWN); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_TAKE_DOWN, player);
        HP_BAR(opponent);
        NOT HP_BAR(player);
    }
}

SINGLE_BATTLE_TEST("Cubone Skull: with RELICS off the part does nothing")
{
    GIVEN {
        ASSUME(GetMoveRecoil(MOVE_TAKE_DOWN) > 0);
        PLAYER(SPECIES_WOBBUFFET) { Relic(RELIC_CUBONE_SKULL); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_TAKE_DOWN); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_TAKE_DOWN, player);
        HP_BAR(opponent);
        HP_BAR(player);
    }
}
