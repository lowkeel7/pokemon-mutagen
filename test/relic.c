#include "global.h"
#include "item.h"
#include "item_use.h"
#include "move.h"
#include "pokemon.h"
#include "relic.h"
#include "test/test.h"
#include "constants/abilities.h"
#include "constants/items.h"
#include "constants/moves.h"
#include "constants/species.h"

// Pokémon Mutagen (SG-09): the species parts' table is whole, and each part's item and donor lead
// back to it (the bag, the drops and the sandbox all look the part up that way). A part strengthens
// a move family or grants an ability, by its row alone.

// The engine's stat each stat kind raises (Shuckle's both: its Defense here, its Sp. Def below).
static const u8 sStatOf[] =
{
    [RELIC_STAT_ATK] = STAT_ATK,
    [RELIC_STAT_DEF] = STAT_DEF,
    [RELIC_STAT_SPATK] = STAT_SPATK,
    [RELIC_STAT_SPDEF] = STAT_SPDEF,
    [RELIC_STAT_SPEED] = STAT_SPEED,
    [RELIC_STAT_DEFENSES] = STAT_DEF,
};

// A move inside each family, to check every row's family against the flags.
static const u16 sFamilyMove[] =
{
    [RELIC_FAMILY_PUNCH] = MOVE_MACH_PUNCH,
    [RELIC_FAMILY_SLASH] = MOVE_CUT,
    [RELIC_FAMILY_STAB] = MOVE_HORN_ATTACK,
    [RELIC_FAMILY_BITE] = MOVE_BITE,
    [RELIC_FAMILY_SOUND] = MOVE_ROUND,
    [RELIC_FAMILY_WIND] = MOVE_GUST,
    [RELIC_FAMILY_BALLISTIC] = MOVE_SEED_BOMB,
    [RELIC_FAMILY_BLUNT] = MOVE_POUND,
};

TEST("Relics: every part's row is whole and leads back to itself")
{
    u32 relic;

    for (relic = RELIC_NONE + 1; relic < RELICS_COUNT; relic++)
    {
        const struct RelicInfo *info = &gRelicsInfo[relic];

        EXPECT_NE(info->item, ITEM_NONE);
        EXPECT_EQ(RelicFromItem(info->item), relic);
        EXPECT_NE(info->donor, SPECIES_NONE);
        EXPECT_EQ(RelicOfDonor(info->donor), info->poached ? RELIC_NONE : relic); // a poached part is never a wild drop
        EXPECT(IsSpeciesEnabled(info->donor));
        EXPECT(info->ability < ABILITIES_COUNT);
        EXPECT(info->gfx != NULL);
        EXPECT(GetItemFieldFunc(info->item) == ItemUseOutOfBattle_Relic);
        EXPECT_EQ(GetItemType(info->item), ITEM_USE_PARTY_MENU);
        // One effect a part: an ability, a move family or a stat, the last two by one to three tenths
        EXPECT((info->ability != ABILITY_NONE) + (info->family != RELIC_FAMILY_NONE) + (info->stat != RELIC_STAT_NONE) <= 1);
        if (info->stat != RELIC_STAT_NONE)
        {
            EXPECT(info->stat < ARRAY_COUNT(sStatOf));
            EXPECT(info->boost >= 1 && info->boost <= 3);
            EXPECT_NE(GetRelicStatBoost(relic, sStatOf[info->stat]), UQ_4_12(1.0));
            EXPECT_EQ(GetRelicStatBoost(relic, STAT_HP), UQ_4_12(1.0));
        }
        else
        {
            EXPECT_EQ((u32)info->typed, 0);
            EXPECT_EQ(GetRelicStatBoost(relic, STAT_DEF), UQ_4_12(1.0));
            EXPECT_EQ(GetRelicStatBoost(relic, STAT_SPEED), UQ_4_12(1.0));
        }
        if (info->family != RELIC_FAMILY_NONE)
        {
            EXPECT(info->family < ARRAY_COUNT(sFamilyMove));
            EXPECT(info->boost >= 1 && info->boost <= 3);
            EXPECT(IsMoveOfRelicFamily(sFamilyMove[info->family], info->family));
            EXPECT_NE(GetRelicMovePowerModifier(relic, sFamilyMove[info->family]), UQ_4_12(1.0));
            EXPECT_EQ(GetRelicMovePowerModifier(relic, MOVE_TACKLE), UQ_4_12(1.0));
        }
        else
        {
            if (info->stat == RELIC_STAT_NONE)
                EXPECT_EQ((u32)info->boost, 0); // (cast: the macro's typeof cannot take a bit-field)
            EXPECT_EQ((u32)info->rider, RELIC_RIDER_NONE);
            EXPECT_EQ(GetRelicMovePowerModifier(relic, MOVE_CUT), UQ_4_12(1.0));
        }
    }
}

TEST("Relics: the move families follow the flags, the stab and blunt ones included")
{
    EXPECT(IsMoveOfRelicFamily(MOVE_HORN_ATTACK, RELIC_FAMILY_STAB));
    EXPECT(IsMoveOfRelicFamily(MOVE_MEGAHORN, RELIC_FAMILY_STAB));
    EXPECT(!IsMoveOfRelicFamily(MOVE_TACKLE, RELIC_FAMILY_STAB));
    EXPECT(IsMoveOfRelicFamily(MOVE_HAMMER_ARM, RELIC_FAMILY_BLUNT));
    EXPECT(IsMoveOfRelicFamily(MOVE_MACH_PUNCH, RELIC_FAMILY_BLUNT)); // a punch is blunt too
    EXPECT(!IsMoveOfRelicFamily(MOVE_CUT, RELIC_FAMILY_BLUNT));
    EXPECT(IsMoveOfRelicFamily(MOVE_CUT, RELIC_FAMILY_SLASH));
    EXPECT(!IsMoveOfRelicFamily(MOVE_CUT, RELIC_FAMILY_NONE));
    EXPECT_EQ(GetRelicMovePowerModifier(RELIC_KABUTOPS_CLEAVERS, MOVE_CUT), UQ_4_12(1.2));
    EXPECT_EQ(GetRelicMovePowerModifier(RELIC_BOXING_GLOVES, MOVE_MACH_PUNCH), UQ_4_12(1.1));
    EXPECT_EQ(GetRelicCritStageIncrease(RELIC_ABSOL_BLADE, MOVE_CUT), 1);
    EXPECT_EQ(GetRelicCritStageIncrease(RELIC_ABSOL_BLADE, MOVE_TACKLE), 0);
    EXPECT(RelicPoisonsOnHit(RELIC_SEVIPER_VENOM, MOVE_BITE));
    EXPECT(!RelicPoisonsOnHit(RELIC_SEVIPER_VENOM, MOVE_TACKLE));
    EXPECT(!RelicPoisonsOnHit(RELIC_NONE, MOVE_BITE));
}

TEST("Relics: the stat parts raise their stat alone, Shuckle's shell both defenses for any wearer")
{
    EXPECT_EQ(GetRelicStatBoost(RELIC_SCEPTILE_TAIL, STAT_SPEED), UQ_4_12(1.2));
    EXPECT_EQ(GetRelicStatBoost(RELIC_SCEPTILE_TAIL, STAT_DEF), UQ_4_12(1.0));
    EXPECT(gRelicsInfo[RELIC_SCEPTILE_TAIL].typed);
    EXPECT_EQ(GetRelicType(RELIC_SCEPTILE_TAIL), TYPE_GRASS);
    EXPECT_EQ(GetRelicStatBoost(RELIC_SHINX_STAR, STAT_SPEED), UQ_4_12(1.2));
    EXPECT_EQ(GetRelicType(RELIC_SHINX_STAR), TYPE_ELECTRIC);
    EXPECT_EQ(GetRelicStatBoost(RELIC_SPOINK_PEARL, STAT_SPATK), UQ_4_12(1.2));
    EXPECT_EQ(GetRelicStatBoost(RELIC_SPOINK_PEARL, STAT_ATK), UQ_4_12(1.0));
    EXPECT_EQ(GetRelicStatBoost(RELIC_HERACROSS_SHELL, STAT_DEF), UQ_4_12(1.2));
    EXPECT_EQ(GetRelicStatBoost(RELIC_HERACROSS_SHELL, STAT_SPDEF), UQ_4_12(1.0));
    EXPECT_EQ(GetRelicStatBoost(RELIC_SHIFTRY_BARK, STAT_DEF), UQ_4_12(1.2));
    EXPECT_EQ(GetRelicStatBoost(RELIC_BULBASAUR_BULB, STAT_SPDEF), UQ_4_12(1.2));
    EXPECT_EQ(GetRelicStatBoost(RELIC_BULBASAUR_BULB, STAT_DEF), UQ_4_12(1.0));
    EXPECT_EQ(GetRelicStatBoost(RELIC_SHUCKLE_SHELL, STAT_DEF), UQ_4_12(1.1));
    EXPECT_EQ(GetRelicStatBoost(RELIC_SHUCKLE_SHELL, STAT_SPDEF), UQ_4_12(1.1));
    EXPECT_EQ(GetRelicStatBoost(RELIC_SHUCKLE_SHELL, STAT_SPEED), UQ_4_12(1.0));
    EXPECT(!gRelicsInfo[RELIC_SHUCKLE_SHELL].typed);
    EXPECT_EQ(GetRelicStatBoost(RELIC_KABUTOPS_CLEAVERS, STAT_ATK), UQ_4_12(1.0));
    EXPECT_EQ(GetRelicStatBoost(RELIC_NONE, STAT_SPEED), UQ_4_12(1.0));
}

TEST("Relics: the type a part lends is its donor's, Flying for a bird rather than Normal")
{
    EXPECT_EQ(GetRelicType(RELIC_LOTAD_LILY), TYPE_WATER);
    EXPECT_EQ(GetRelicType(RELIC_SWELLOW_TAIL), TYPE_FLYING);
    EXPECT_EQ(GetRelicType(RELIC_PIDGEOT_FEATHERS), TYPE_FLYING);
    EXPECT_EQ(GetRelicType(RELIC_LOUDRED_EARS), TYPE_NORMAL);
    EXPECT_EQ(GetRelicType(RELIC_NONE), TYPE_NONE);
}

TEST("Relics: a part's index fits the Pokémon's six bits, and the empty row is RELIC_NONE")
{
    EXPECT(RELICS_COUNT <= 64);
    EXPECT_EQ(RelicFromItem(ITEM_NONE), RELIC_NONE);
    EXPECT_EQ(RelicOfDonor(SPECIES_NONE), RELIC_NONE);
    EXPECT_EQ(GetRelicAbility(RELIC_NONE), ABILITY_NONE);
}
