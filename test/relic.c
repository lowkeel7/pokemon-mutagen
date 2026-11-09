#include "global.h"
#include "item.h"
#include "item_use.h"
#include "pokemon.h"
#include "relic.h"
#include "test/test.h"
#include "constants/abilities.h"
#include "constants/items.h"
#include "constants/species.h"

// Pokémon Mutagen (SG-09): the species parts' table is whole, and each part's item and donor lead
// back to it (the bag, the drops and the sandbox all look the part up that way).

TEST("Relics: every part's row is whole and leads back to itself")
{
    u32 relic;

    for (relic = RELIC_NONE + 1; relic < RELICS_COUNT; relic++)
    {
        const struct RelicInfo *info = &gRelicsInfo[relic];

        EXPECT_NE(info->item, ITEM_NONE);
        EXPECT_EQ(RelicFromItem(info->item), relic);
        EXPECT_NE(info->donor, SPECIES_NONE);
        EXPECT_EQ(RelicOfDonor(info->donor), relic);
        EXPECT(IsSpeciesEnabled(info->donor));
        EXPECT(info->ability < ABILITIES_COUNT);
        EXPECT(info->gfx != NULL);
        EXPECT(GetItemFieldFunc(info->item) == ItemUseOutOfBattle_Relic);
        EXPECT_EQ(GetItemType(info->item), ITEM_USE_PARTY_MENU);
    }
}

TEST("Relics: a part's index fits the Pokémon's six bits, and the empty row is RELIC_NONE")
{
    EXPECT(RELICS_COUNT <= 64);
    EXPECT_EQ(RelicFromItem(ITEM_NONE), RELIC_NONE);
    EXPECT_EQ(RelicOfDonor(SPECIES_NONE), RELIC_NONE);
    EXPECT_EQ(GetRelicAbility(RELIC_NONE), ABILITY_NONE);
}
