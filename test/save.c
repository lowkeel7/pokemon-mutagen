#include "global.h"
#include "pokemon_storage_system.h"
#include "test/test.h"

// If you would like to ensure save compatibility, update the values below with those for your hack. You can find these through the debug menu.
// Please note that this simple check is not 100% foolproof, but should be able to catch most unintended shifts.
// Pokemon Mutagen: Heart & Soul 2.0.6's sizes, so that its saves keep loading. A change to
// SaveBlock1, SaveBlock2 or PokemonStorage, or in front of an existing SaveBlock3 field, is a
// save break: it needs SAVE_VERSION and a migration in save.c, and a line in the changelog.
// SaveBlock3 may grow at its end (sectors are zero-filled before every write, so older saves read
// the new bytes as zero): 52 in 2.0.6, 84 with MutagenSettings (QW-29).
#define T_SAVEBLOCK1_SIZE 15760
#define T_SAVEBLOCK2_SIZE 3892
#define T_SAVEBLOCK3_SIZE 84
#define T_POKEMONSTORAGE_SIZE 34144

TEST("SaveBlock1 is backwards compatible")
{
    EXPECT_EQ(sizeof(struct SaveBlock1), T_SAVEBLOCK1_SIZE);
}

TEST("SaveBlock2 is backwards compatible")
{
    EXPECT_EQ(sizeof(struct SaveBlock2), T_SAVEBLOCK2_SIZE);
}

TEST("SaveBlock3 is backwards compatible")
{
    EXPECT_EQ(sizeof(struct SaveBlock3), T_SAVEBLOCK3_SIZE);
}

TEST("PokemonStorage is backwards compatible")
{
    EXPECT_EQ(sizeof(struct PokemonStorage), T_POKEMONSTORAGE_SIZE);
}

#undef T_SAVEBLOCK1_SIZE
#undef T_SAVEBLOCK2_SIZE
#undef T_SAVEBLOCK3_SIZE
#undef T_POKEMONSTORAGE_SIZE
