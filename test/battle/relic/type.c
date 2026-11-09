#include "global.h"
#include "test/battle.h"
#include "relic.h"

// Pokémon Mutagen (SG-09): a worn part lends its donor's first type as the wearer's third type
// while MUTAGEN → THIRD TYPE is on, read while worn and never written: the Pokémon's own third
// type waits under it, and the player may keep the own one showing instead.

SINGLE_BATTLE_TEST("Relics: a worn part lends its donor's type as the third type (THIRD TYPE on)", s16 damage)
{
    bool32 worn;
    PARAMETRIZE { worn = FALSE; }
    PARAMETRIZE { worn = TRUE; }
    GIVEN {
        ASSUME(GetRelicType(RELIC_LOTAD_LILY) == TYPE_WATER);
        ASSUME(GetSpeciesType(SPECIES_WOBBUFFET, 0) == TYPE_PSYCHIC && GetSpeciesType(SPECIES_WOBBUFFET, 1) == TYPE_PSYCHIC);
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        gSaveBlock3Ptr->mutagenSettings.thirdType = TRUE;
        PLAYER(SPECIES_WOBBUFFET) { if (worn) Relic(RELIC_LOTAD_LILY); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(opponent, MOVE_THUNDER_SHOCK); }
    } SCENE {
        HP_BAR(player, captureDamage: &results[i].damage);
    } FINALLY {
        EXPECT_MUL_EQ(results[0].damage, Q_4_12(2.0), results[1].damage);
    }
}

SINGLE_BATTLE_TEST("Relics: with THIRD TYPE off a worn part lends no type", s16 damage)
{
    bool32 worn;
    PARAMETRIZE { worn = FALSE; }
    PARAMETRIZE { worn = TRUE; }
    GIVEN {
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_WOBBUFFET) { if (worn) Relic(RELIC_LOTAD_LILY); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(opponent, MOVE_THUNDER_SHOCK); }
    } SCENE {
        HP_BAR(player, captureDamage: &results[i].damage);
    } FINALLY {
        EXPECT_EQ(results[0].damage, results[1].damage);
    }
}

SINGLE_BATTLE_TEST("Relics: the own third type kept under the part is the one that counts", s16 damage)
{
    bool32 keepOwn;
    PARAMETRIZE { keepOwn = FALSE; }
    PARAMETRIZE { keepOwn = TRUE; }
    GIVEN {
        ASSUME(GetRelicType(RELIC_LOTAD_LILY) == TYPE_WATER);
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        gSaveBlock3Ptr->mutagenSettings.thirdType = TRUE;
        // Normal under the lily: Thunder Shock is neutral on Psychic/Normal, doubled on Psychic/Water.
        PLAYER(SPECIES_WOBBUFFET) { ThirdType(TYPE_NORMAL); Relic(RELIC_LOTAD_LILY); if (keepOwn) RelicTypeOff(); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(opponent, MOVE_THUNDER_SHOCK); }
    } SCENE {
        HP_BAR(player, captureDamage: &results[i].damage);
    } FINALLY {
        EXPECT_MUL_EQ(results[1].damage, Q_4_12(2.0), results[0].damage);
    }
}
