// Pokémon Mutagen (SG-09): the species parts. Art: each part is cut from its donor's own sprite
// (graphics/relics/, PROVENANCE.md); the index 0 of its palette is transparent.
const struct RelicInfo gRelicsInfo[RELICS_COUNT] =
{
    [RELIC_NONE] = {0},
    [RELIC_CUBONE_SKULL] =
    {
        .item = ITEM_CUBONE_SKULL,
        .ability = ABILITY_ROCK_HEAD,
        .gfx = gRelicGfx_CuboneSkull,
        .palette = gRelicPal_CuboneSkull,
    },
};
