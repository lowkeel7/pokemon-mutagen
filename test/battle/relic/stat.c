#include "global.h"
#include "test/battle.h"
#include "relic.h"

// Pokémon Mutagen (SG-09): a worn species part raises one stat of a wearer of the part's type, the
// type it lends (Shuckle's shell: both defenses, of any wearer), behind MUTAGEN → RELICS. Read while
// worn, never written: the Pokémon is itself again without it.

// Damage shows the stat: the wearer attacks (Spoink's pearl) or is hit (the shells, the bark, the bulb).
// The stats are pinned, 150 attacking 200, so the floors of the formula (the /50, the +2 and the
// runner's lowest roll, 85%) and the fixed-point boost (a hair under 1.2) leave every ratio below
// exact: Tackle does 22, 19 behind a fifth more defence, and 19 x 1.2 floors to 22 again.
static const struct { u32 relic; u16 wearer; u16 move; u16 otherMove; bool32 wearerAttacks; u32 tenths; } sStatParts[] =
{
    { RELIC_SPOINK_PEARL,    SPECIES_WOBBUFFET, MOVE_SWIFT,  MOVE_TACKLE, TRUE,  2 }, // Sp. Atk, a Psychic type
    { RELIC_HERACROSS_SHELL, SPECIES_HERACROSS, MOVE_TACKLE, MOVE_SWIFT,  FALSE, 2 }, // Defense, a Bug type
    { RELIC_SHIFTRY_BARK,    SPECIES_TREECKO,   MOVE_TACKLE, MOVE_SWIFT,  FALSE, 2 }, // Defense, a Grass type
    { RELIC_BULBASAUR_BULB,  SPECIES_TREECKO,   MOVE_SWIFT,  MOVE_TACKLE, FALSE, 2 }, // Sp. Def, a Grass type
    { RELIC_SHUCKLE_SHELL,   SPECIES_WOBBUFFET, MOVE_TACKLE, MOVE_NONE,   FALSE, 1 }, // Defense, any wearer
    { RELIC_SHUCKLE_SHELL,   SPECIES_WOBBUFFET, MOVE_SWIFT,  MOVE_NONE,   FALSE, 1 }, // and Sp. Def
};

static const u32 sBoost[] = { Q_4_12(1.0), Q_4_12(1.1), Q_4_12(1.2), Q_4_12(1.3) };

SINGLE_BATTLE_TEST("Relics: a worn stat part raises the wearer's stat by the row's boost (RELICS on)", s16 damage)
{
    u32 j, part = 0, worn = FALSE;
    for (j = 0; j < ARRAY_COUNT(sStatParts); j++)
    {
        PARAMETRIZE { part = j; worn = FALSE; }
        PARAMETRIZE { part = j; worn = TRUE; }
    }
    GIVEN {
        ASSUME(gRelicsInfo[sStatParts[part].relic].stat != RELIC_STAT_NONE);
        ASSUME(gRelicsInfo[sStatParts[part].relic].boost == sStatParts[part].tenths);
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        if (sStatParts[part].wearerAttacks) {
            PLAYER(sStatParts[part].wearer) { Attack(150); SpAttack(150); if (worn) Relic(sStatParts[part].relic); }
            OPPONENT(SPECIES_WOBBUFFET) { Defense(200); SpDefense(200); }
        } else {
            PLAYER(SPECIES_WOBBUFFET) { Attack(150); SpAttack(150); }
            OPPONENT(sStatParts[part].wearer) { Defense(200); SpDefense(200); if (worn) Relic(sStatParts[part].relic); }
        }
    } WHEN {
        TURN { MOVE(player, sStatParts[part].move); }
    } SCENE {
        HP_BAR(opponent, captureDamage: &results[i].damage);
    } FINALLY {
        for (j = 0; j < ARRAY_COUNT(sStatParts); j++)
        {
            if (sStatParts[j].wearerAttacks) // the wearer hits harder
                EXPECT_MUL_EQ(results[2 * j].damage, sBoost[sStatParts[j].tenths], results[2 * j + 1].damage);
            else // the wearer is hit less
                EXPECT_MUL_EQ(results[2 * j + 1].damage, sBoost[sStatParts[j].tenths], results[2 * j].damage);
        }
    }
}

SINGLE_BATTLE_TEST("Relics: a worn stat part leaves the wearer's other stats alone", s16 damage)
{
    u32 j, part = 0, worn = FALSE;
    for (j = 0; j < ARRAY_COUNT(sStatParts); j++)
    {
        if (sStatParts[j].otherMove == MOVE_NONE)
            continue;
        PARAMETRIZE { part = j; worn = FALSE; }
        PARAMETRIZE { part = j; worn = TRUE; }
    }
    GIVEN {
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        if (sStatParts[part].wearerAttacks) {
            PLAYER(sStatParts[part].wearer) { if (worn) Relic(sStatParts[part].relic); }
            OPPONENT(SPECIES_WOBBUFFET);
        } else {
            PLAYER(SPECIES_WOBBUFFET);
            OPPONENT(sStatParts[part].wearer) { if (worn) Relic(sStatParts[part].relic); }
        }
    } WHEN {
        TURN { MOVE(player, sStatParts[part].otherMove); }
    } SCENE {
        HP_BAR(opponent, captureDamage: &results[i].damage);
    } FINALLY {
        for (j = 0; j + 1 < i; j += 2)
            EXPECT_EQ(results[j].damage, results[j + 1].damage);
    }
}

// A wearer of another type gets nothing from a typed part (THIRD TYPE off, so the part lends no type).
static const struct { u32 relic; u16 wearer; u16 move; bool32 wearerAttacks; } sOtherTypes[] =
{
    { RELIC_SPOINK_PEARL,    SPECIES_TREECKO,   MOVE_SWIFT,  TRUE  }, // a Grass type with the Psychic pearl
    { RELIC_HERACROSS_SHELL, SPECIES_WOBBUFFET, MOVE_TACKLE, FALSE }, // a Psychic type with the Bug shell
    { RELIC_BULBASAUR_BULB,  SPECIES_WOBBUFFET, MOVE_SWIFT,  FALSE }, // and with the Grass bulb
};

SINGLE_BATTLE_TEST("Relics: a typed stat part raises nothing for a wearer of another type", s16 damage)
{
    u32 j, part = 0, worn = FALSE;
    for (j = 0; j < ARRAY_COUNT(sOtherTypes); j++)
    {
        PARAMETRIZE { part = j; worn = FALSE; }
        PARAMETRIZE { part = j; worn = TRUE; }
    }
    GIVEN {
        ASSUME(gRelicsInfo[sOtherTypes[part].relic].typed);
        ASSUME(GetSpeciesType(sOtherTypes[part].wearer, 0) != GetRelicType(sOtherTypes[part].relic));
        ASSUME(GetSpeciesType(sOtherTypes[part].wearer, 1) != GetRelicType(sOtherTypes[part].relic));
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        if (sOtherTypes[part].wearerAttacks) {
            PLAYER(sOtherTypes[part].wearer) { if (worn) Relic(sOtherTypes[part].relic); }
            OPPONENT(SPECIES_WOBBUFFET);
        } else {
            PLAYER(SPECIES_WOBBUFFET);
            OPPONENT(sOtherTypes[part].wearer) { if (worn) Relic(sOtherTypes[part].relic); }
        }
    } WHEN {
        TURN { MOVE(player, sOtherTypes[part].move); }
    } SCENE {
        HP_BAR(opponent, captureDamage: &results[i].damage);
    } FINALLY {
        for (j = 0; j < ARRAY_COUNT(sOtherTypes); j++)
            EXPECT_EQ(results[2 * j].damage, results[2 * j + 1].damage);
    }
}

SINGLE_BATTLE_TEST("Relics: with RELICS off a worn stat part raises nothing", s16 damage)
{
    bool32 worn;
    PARAMETRIZE { worn = FALSE; }
    PARAMETRIZE { worn = TRUE; }
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET);
        OPPONENT(SPECIES_WOBBUFFET) { if (worn) Relic(RELIC_SHUCKLE_SHELL); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        HP_BAR(opponent, captureDamage: &results[i].damage);
    } FINALLY {
        EXPECT_EQ(results[0].damage, results[1].damage);
    }
}

// Who moves first tells whose Speed is higher: 100 against 110, so only the part's fifth more turns it.
SINGLE_BATTLE_TEST("Relics: Sceptile's tail makes a Grass-type wearer a fifth faster")
{
    bool32 worn;
    PARAMETRIZE { worn = FALSE; }
    PARAMETRIZE { worn = TRUE; }
    GIVEN {
        ASSUME(gRelicsInfo[RELIC_SCEPTILE_TAIL].stat == RELIC_STAT_SPEED && gRelicsInfo[RELIC_SCEPTILE_TAIL].boost == 2);
        ASSUME(GetRelicType(RELIC_SCEPTILE_TAIL) == TYPE_GRASS);
        ASSUME(GetSpeciesType(SPECIES_TREECKO, 0) == TYPE_GRASS);
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_TREECKO) { Speed(100); if (worn) Relic(RELIC_SCEPTILE_TAIL); }
        OPPONENT(SPECIES_WOBBUFFET) { Speed(110); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); MOVE(opponent, MOVE_TACKLE); }
    } SCENE {
        if (worn) {
            ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, player);
            ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, opponent);
        } else {
            ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, opponent);
            ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, player);
        }
    }
}

SINGLE_BATTLE_TEST("Relics: Shinx's star makes an Electric-type wearer a fifth faster")
{
    bool32 worn;
    PARAMETRIZE { worn = FALSE; }
    PARAMETRIZE { worn = TRUE; }
    GIVEN {
        ASSUME(gRelicsInfo[RELIC_SHINX_STAR].stat == RELIC_STAT_SPEED && gRelicsInfo[RELIC_SHINX_STAR].boost == 2);
        ASSUME(GetRelicType(RELIC_SHINX_STAR) == TYPE_ELECTRIC);
        ASSUME(GetSpeciesType(SPECIES_PIKACHU, 0) == TYPE_ELECTRIC);
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_PIKACHU) { Ability(ABILITY_LIGHTNING_ROD); Speed(100); if (worn) Relic(RELIC_SHINX_STAR); }
        OPPONENT(SPECIES_WOBBUFFET) { Speed(110); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); MOVE(opponent, MOVE_TACKLE); }
    } SCENE {
        if (worn) {
            ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, player);
            ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, opponent);
        } else {
            ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, opponent);
            ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, player);
        }
    }
}

// The part's type is the one it lends: with THIRD TYPE on a Psychic type wearing the tail is a Grass
// type too, and runs faster for it; with it off the tail lends nothing and the wearer is as fast as it was.
SINGLE_BATTLE_TEST("Relics: Sceptile's tail speeds a wearer of another type only when THIRD TYPE lends it Grass")
{
    bool32 thirdType;
    PARAMETRIZE { thirdType = FALSE; }
    PARAMETRIZE { thirdType = TRUE; }
    GIVEN {
        ASSUME(GetSpeciesType(SPECIES_WOBBUFFET, 0) == TYPE_PSYCHIC && GetSpeciesType(SPECIES_WOBBUFFET, 1) == TYPE_PSYCHIC);
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        gSaveBlock3Ptr->mutagenSettings.thirdType = thirdType;
        PLAYER(SPECIES_WOBBUFFET) { Speed(100); Relic(RELIC_SCEPTILE_TAIL); }
        OPPONENT(SPECIES_WOBBUFFET) { Speed(110); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); MOVE(opponent, MOVE_TACKLE); }
    } SCENE {
        if (thirdType) {
            ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, player);
            ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, opponent);
        } else {
            ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, opponent);
            ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, player);
        }
    }
}
