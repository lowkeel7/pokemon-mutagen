#include "global.h"
#include "test/battle.h"
#include "relic.h"

// Pokémon Mutagen (SG-09): the misc parts, one effect each, read by the part's name where the battle
// needs it, behind MUTAGEN → RELICS. Read while worn, never written, nothing used up: the Shedinja
// Shell's once a battle is a bit of the battle's own state, gone when the battle ends.

SINGLE_BATTLE_TEST("Relics: a worn Beautifly Proboscis makes HP-stealing moves heal 30% more", s16 damage, s16 heal)
{
    bool32 worn;

    PARAMETRIZE { worn = FALSE; }
    PARAMETRIZE { worn = TRUE; }

    GIVEN {
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_XURKITREE) { HP(200); if (worn) Relic(RELIC_BEAUTIFLY_PROBOSCIS); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_ABSORB); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_ABSORB, player);
        HP_BAR(opponent, captureDamage: &results[i].damage);
        HP_BAR(player, captureDamage: &results[i].heal);
    } FINALLY {
        EXPECT_EQ(results[0].damage, results[1].damage); // the move hits no harder
        EXPECT_MUL_EQ(results[0].heal, Q_4_12(1.3), results[1].heal);
    }
}

SINGLE_BATTLE_TEST("Relics: a worn Beautifly Proboscis makes Leech Seed heal 30% more", s16 heal)
{
    bool32 worn;

    PARAMETRIZE { worn = FALSE; }
    PARAMETRIZE { worn = TRUE; }

    GIVEN {
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_WOBBUFFET) { HP(1); if (worn) Relic(RELIC_BEAUTIFLY_PROBOSCIS); }
        OPPONENT(SPECIES_WOBBUFFET) { MaxHP(160); HP(160); }
    } WHEN {
        TURN { MOVE(player, MOVE_LEECH_SEED); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_LEECH_SEED, player);
        HP_BAR(opponent);
        HP_BAR(player, captureDamage: &results[i].heal);
    } FINALLY {
        EXPECT_MUL_EQ(results[0].heal, Q_4_12(1.3), results[1].heal);
    }
}

SINGLE_BATTLE_TEST("Relics: a worn Beautifly Proboscis does nothing with RELICS off", s16 heal)
{
    bool32 worn;

    PARAMETRIZE { worn = FALSE; }
    PARAMETRIZE { worn = TRUE; }

    GIVEN {
        gSaveBlock3Ptr->mutagenSettings.relics = FALSE;
        PLAYER(SPECIES_XURKITREE) { HP(200); if (worn) Relic(RELIC_BEAUTIFLY_PROBOSCIS); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_ABSORB); }
    } SCENE {
        HP_BAR(opponent);
        HP_BAR(player, captureDamage: &results[i].heal);
    } FINALLY {
        EXPECT_EQ(results[0].heal, results[1].heal);
    }
}

SINGLE_BATTLE_TEST("Relics: a worn Hypno Pendulum makes sleep moves 20% more accurate")
{
    PASSES_RANDOMLY(72, 100, RNG_ACCURACY);
    GIVEN {
        ASSUME(GetMoveAccuracy(MOVE_HYPNOSIS) == 60);
        ASSUME(GetMoveNonVolatileStatus(MOVE_HYPNOSIS) == MOVE_EFFECT_SLEEP);
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_WOBBUFFET) { Relic(RELIC_HYPNO_PENDULUM); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_HYPNOSIS); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_HYPNOSIS, player);
        STATUS_ICON(opponent, sleep: TRUE);
    }
}

SINGLE_BATTLE_TEST("Relics: a worn Hypno Pendulum leaves other moves' accuracy alone")
{
    PASSES_RANDOMLY(70, 100, RNG_ACCURACY);
    GIVEN {
        ASSUME(GetMoveAccuracy(MOVE_THUNDER) == 70);
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_WOBBUFFET) { Relic(RELIC_HYPNO_PENDULUM); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_THUNDER); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_THUNDER, player);
        HP_BAR(opponent);
    }
}

SINGLE_BATTLE_TEST("Relics: worn Sunflora Petals give back 1/16 of the HP each turn in harsh sunlight")
{
    GIVEN {
        ASSUME(GetMoveWeatherType(MOVE_SUNNY_DAY) == BATTLE_WEATHER_SUN);
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_WOBBUFFET) { HP(1); MaxHP(160); Relic(RELIC_SUNFLORA_PETALS); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(opponent, MOVE_SUNNY_DAY); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_SUNNY_DAY, opponent);
        HP_BAR(player, damage: -(160 / 16));
    }
}

SINGLE_BATTLE_TEST("Relics: worn Sunflora Petals give nothing without the sun, or with RELICS off")
{
    bool32 relics;
    enum Move move;

    PARAMETRIZE { relics = TRUE;  move = MOVE_RAIN_DANCE; }
    PARAMETRIZE { relics = FALSE; move = MOVE_SUNNY_DAY; }

    GIVEN {
        gSaveBlock3Ptr->mutagenSettings.relics = relics;
        PLAYER(SPECIES_WOBBUFFET) { HP(1); MaxHP(160); Relic(RELIC_SUNFLORA_PETALS); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(opponent, move); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, move, opponent);
        NONE_OF { HP_BAR(player); }
    }
}

SINGLE_BATTLE_TEST("Relics: a worn Shedinja Shell endures one hit a battle that the wearer isn't weak to")
{
    GIVEN {
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_WOBBUFFET) { HP(5); Relic(RELIC_SHEDINJA_SHELL); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); }
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, player);
        HP_BAR(opponent, hp: 1);
        ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, player);
        HP_BAR(opponent, hp: 0); // once a battle
    }
}

SINGLE_BATTLE_TEST("Relics: a worn Shedinja Shell does not endure a super-effective hit, or with RELICS off")
{
    bool32 relics;
    enum Move move;

    PARAMETRIZE { relics = TRUE;  move = MOVE_BITE; }   // Dark against Psychic
    PARAMETRIZE { relics = FALSE; move = MOVE_TACKLE; }

    GIVEN {
        ASSUME(GetMoveType(MOVE_BITE) == TYPE_DARK);
        gSaveBlock3Ptr->mutagenSettings.relics = relics;
        gSaveBlock3Ptr->mutagenSettings.thirdType = FALSE;
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_WOBBUFFET) { HP(5); Relic(RELIC_SHEDINJA_SHELL); }
    } WHEN {
        TURN { MOVE(player, move); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, move, player);
        HP_BAR(opponent, hp: 0);
    }
}

SINGLE_BATTLE_TEST("Relics: a worn Shedinja Shell spends nothing, and leaves a held Focus Sash alone")
{
    GIVEN {
        ASSUME(gItemsInfo[ITEM_FOCUS_SASH].holdEffect == HOLD_EFFECT_FOCUS_SASH);
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_WOBBUFFET) { HP(5); Item(ITEM_FOCUS_SASH); Relic(RELIC_SHEDINJA_SHELL); } // not at full HP: the Sash can't, the shell can
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, player);
        HP_BAR(opponent, hp: 1);
    } THEN {
        EXPECT_EQ(opponent->item, ITEM_FOCUS_SASH);
        EXPECT_EQ(GetMonData(&gEnemyParty[0], MON_DATA_RELIC), RELIC_SHEDINJA_SHELL);
    }
}
