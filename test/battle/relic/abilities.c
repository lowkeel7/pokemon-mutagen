#include "global.h"
#include "test/battle.h"
#include "relic.h"

// Pokémon Mutagen (SG-09): every species part grants its ability to whatever wears it, behind the
// MUTAGEN → RELICS option. One case per part, from the same list that makes the enum.

SINGLE_BATTLE_TEST("Relics: a worn part's ability is the wearer's, whatever its species (RELICS on)")
{
    u32 relic = RELIC_NONE;
    #define RELIC_CASE(name) PARAMETRIZE { relic = RELIC_##name; }
    RELICS_LIST(RELIC_CASE)
    #undef RELIC_CASE
    GIVEN {
        ASSUME(gRelicsInfo[relic].ability != ABILITY_NONE);
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_WOBBUFFET) { Relic(relic); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE); }
    } THEN {
        EXPECT_EQ(player->ability, (u32)gRelicsInfo[relic].ability); // (cast: the macro's typeof cannot take a bit-field)
    }
}

SINGLE_BATTLE_TEST("Relics: with RELICS off a worn part leaves the species' own ability")
{
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Relic(RELIC_LAPRAS_SHELL); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_CELEBRATE); }
    } THEN {
        EXPECT_EQ(player->ability, ABILITY_SHADOW_TAG);
    }
}
