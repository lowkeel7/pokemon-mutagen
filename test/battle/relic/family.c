#include "global.h"
#include "test/battle.h"
#include "relic.h"

// Pokémon Mutagen (SG-09): a worn species part strengthens one family of moves while it is worn,
// behind MUTAGEN → RELICS, and leaves every other move alone; a rider may add a critical-hit stage
// or venom to those moves. Read while worn, never written: the Pokémon is itself again without it.

// One part per family with a move inside it and one outside; Wobbuffet wears each.
static const struct { u32 relic; u16 inside; u16 outside; u32 tenths; } sFamilies[] =
{
    { RELIC_BOXING_GLOVES,     MOVE_MACH_PUNCH,    MOVE_TACKLE, 1 }, // punch
    { RELIC_KABUTOPS_CLEAVERS, MOVE_CUT,           MOVE_TACKLE, 2 }, // slash
    { RELIC_PINSIR_HORNS,      MOVE_HORN_ATTACK,   MOVE_TACKLE, 2 }, // stab
    { RELIC_PREDATOR_TEETH,    MOVE_PSYCHIC_FANGS, MOVE_TACKLE, 2 }, // bite
    { RELIC_LOUDRED_EARS,      MOVE_ROUND,         MOVE_TACKLE, 2 }, // sound
    { RELIC_PIDGEOT_FEATHERS,  MOVE_GUST,          MOVE_TACKLE, 2 }, // wind
    { RELIC_OCTILLERY_CANNON,  MOVE_SEED_BOMB,     MOVE_TACKLE, 2 }, // ballistic
    { RELIC_TINKATON_HAMMER,   MOVE_POUND,         MOVE_TACKLE, 2 }, // blunt
    { RELIC_TINKATON_HAMMER,   MOVE_MACH_PUNCH,    MOVE_TACKLE, 2 }, // a punch is blunt too
};

static const u32 sBoost[] = { Q_4_12(1.0), Q_4_12(1.1), Q_4_12(1.2), Q_4_12(1.3) };

SINGLE_BATTLE_TEST("Relics: a worn part's family moves hit harder by the part's boost (RELICS on)", s16 damage)
{
    u32 j, fam = 0, worn = FALSE;
    for (j = 0; j < ARRAY_COUNT(sFamilies); j++)
    {
        PARAMETRIZE { fam = j; worn = FALSE; }
        PARAMETRIZE { fam = j; worn = TRUE; }
    }
    GIVEN {
        ASSUME(gRelicsInfo[sFamilies[fam].relic].family != RELIC_FAMILY_NONE);
        ASSUME(gRelicsInfo[sFamilies[fam].relic].boost == sFamilies[fam].tenths);
        ASSUME(IsMoveOfRelicFamily(sFamilies[fam].inside, gRelicsInfo[sFamilies[fam].relic].family));
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_WOBBUFFET) { if (worn) Relic(sFamilies[fam].relic); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, sFamilies[fam].inside); }
    } SCENE {
        HP_BAR(opponent, captureDamage: &results[i].damage);
    } FINALLY {
        for (j = 0; j < ARRAY_COUNT(sFamilies); j++)
            EXPECT_MUL_EQ(results[2 * j].damage, sBoost[sFamilies[j].tenths], results[2 * j + 1].damage);
    }
}

SINGLE_BATTLE_TEST("Relics: a worn part leaves moves outside its family alone", s16 damage)
{
    u32 j, fam = 0, worn = FALSE;
    for (j = 0; j < ARRAY_COUNT(sFamilies); j++)
    {
        PARAMETRIZE { fam = j; worn = FALSE; }
        PARAMETRIZE { fam = j; worn = TRUE; }
    }
    GIVEN {
        ASSUME(!IsMoveOfRelicFamily(sFamilies[fam].outside, gRelicsInfo[sFamilies[fam].relic].family));
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_WOBBUFFET) { if (worn) Relic(sFamilies[fam].relic); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, sFamilies[fam].outside); }
    } SCENE {
        HP_BAR(opponent, captureDamage: &results[i].damage);
    } FINALLY {
        for (j = 0; j < ARRAY_COUNT(sFamilies); j++)
            EXPECT_EQ(results[2 * j].damage, results[2 * j + 1].damage);
    }
}

SINGLE_BATTLE_TEST("Relics: with RELICS off a worn part strengthens nothing", s16 damage)
{
    bool32 worn;
    PARAMETRIZE { worn = FALSE; }
    PARAMETRIZE { worn = TRUE; }
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { if (worn) Relic(RELIC_KABUTOPS_CLEAVERS); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_CUT); }
    } SCENE {
        HP_BAR(opponent, captureDamage: &results[i].damage);
    } FINALLY {
        EXPECT_EQ(results[0].damage, results[1].damage);
    }
}

// The test runner lands every critical-hit roll tails unless the odds leave it no tails: Focus
// Energy's two stages and the claws' one make three, every slash a critical hit (the Gen 6+ odds);
// two stages alone are a coin toss, which lands tails here. So the rider shows without randomness.
SINGLE_BATTLE_TEST("Relics: Sandslash's claws give slash moves a critical-hit stage")
{
    bool32 worn;
    PARAMETRIZE { worn = FALSE; }
    PARAMETRIZE { worn = TRUE; }
    GIVEN {
        ASSUME(gRelicsInfo[RELIC_SANDSLASH_CLAWS].rider == RELIC_RIDER_CRIT);
        ASSUME(GetMoveCriticalHitStage(MOVE_CUT) == 0);
        ASSUME(IsSlicingMove(MOVE_CUT));
        ASSUME(B_CRIT_CHANCE >= GEN_6);
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_WOBBUFFET) { if (worn) Relic(RELIC_SANDSLASH_CLAWS); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_FOCUS_ENERGY); }
        TURN { MOVE(player, MOVE_CUT); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_CUT, player);
        if (worn)
            MESSAGE("A critical hit!");
        else
            NONE_OF { MESSAGE("A critical hit!"); }
    }
}

SINGLE_BATTLE_TEST("Relics: Sandslash's claws give no critical-hit stage outside the slash family")
{
    GIVEN {
        ASSUME(GetMoveCriticalHitStage(MOVE_TACKLE) == 0);
        ASSUME(!IsSlicingMove(MOVE_TACKLE));
        ASSUME(B_CRIT_CHANCE >= GEN_6);
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_WOBBUFFET) { Relic(RELIC_SANDSLASH_CLAWS); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_FOCUS_ENERGY); }
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, player);
        NONE_OF { MESSAGE("A critical hit!"); }
    }
}

// (No MESSAGE check: the gate runs with TEST_SKIP_MESSAGES, Heart & Soul's texts being its own; the
// plain, no-ability wording is the script's, BattleScript_RelicStatusEffect.)
SINGLE_BATTLE_TEST("Relics: Beedrill's stingers poison one stab in ten, with no ability popup")
{
    PASSES_RANDOMLY(1, 10, RNG_RELIC_POISON);
    GIVEN {
        ASSUME(gRelicsInfo[RELIC_BEEDRILL_STINGER].rider == RELIC_RIDER_POISON);
        ASSUME(IsStabbingMove(MOVE_HORN_ATTACK));
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_WOBBUFFET) { Relic(RELIC_BEEDRILL_STINGER); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_HORN_ATTACK); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_HORN_ATTACK, player);
        NONE_OF { ABILITY_POPUP(player); }
        ANIMATION(ANIM_TYPE_STATUS, B_ANIM_STATUS_PSN, opponent);
        STATUS_ICON(opponent, poison: TRUE);
    }
}

SINGLE_BATTLE_TEST("Relics: Beedrill's stingers never poison with a move outside the stab family")
{
    GIVEN {
        ASSUME(!IsStabbingMove(MOVE_TACKLE));
        gSaveBlock3Ptr->mutagenSettings.relics = TRUE;
        PLAYER(SPECIES_WOBBUFFET) { Relic(RELIC_BEEDRILL_STINGER); }
        OPPONENT(SPECIES_WOBBUFFET);
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_TACKLE, player);
        NONE_OF { STATUS_ICON(opponent, poison: TRUE); }
    }
}

