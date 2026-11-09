#ifndef GUARD_CONSTANTS_RELICS_H
#define GUARD_CONSTANTS_RELICS_H

// Species parts a Pokémon can wear (Pokémon Mutagen, SG-09). One index per Pokémon, 6 bits
// (PokemonSubstruct0.relic); RELIC_NONE is zero so every older save reads "nothing worn". One list
// makes the enum, bounds the data table and drives the tests. Append only: a save stores the index.
#define RELICS_LIST(X)      \
    X(CUBONE_SKULL)         \
    X(CHARIZARD_SKULL)      \
    X(HEAD_SHELL)           \
    X(ARBOK_VENOM)          \
    X(TOGEPI_SHELL)         \
    X(PUPITAR_SHELL)        \
    X(LOTAD_LILY)           \
    X(SWELLOW_TAIL)         \
    X(KIRLIA_ANTENNA)       \
    X(BRELOOM_CAP)          \
    X(HARIYAMA_PANTS)       \
    X(SABLEYE_EYES)         \
    X(ROSELIA_ROSE)         \
    X(SHARPEDO_SKIN)        \
    X(FLYGON_EYES)          \
    X(DUSKULL_MASK)         \
    X(METAGROSS_CROSS)      \
    X(BASTIODON_SHIELD)     \
    X(SKUNTANK_OIL)         \
    X(SCYTHER_WINGS)        \
    X(LAPRAS_SHELL)         \
    X(MAREEP_WOOL)          \
    X(SNEASEL_FEATHER)      \
    X(MAGCARGO_SHELL)       \
    X(KABUTOPS_CLEAVERS)    \
    X(PINSIR_HORNS)         \
    X(BEEDRILL_STINGER)     \
    X(PIDGEOT_FEATHERS)     \
    X(PREDATOR_TEETH)       \
    X(SANDSLASH_CLAWS)      \
    X(DRILL_HORN)           \
    X(BAYLEEF_LEAF_BLADE)   \
    X(LOUDRED_EARS)         \
    X(SEVIPER_VENOM)        \
    X(ABSOL_BLADE)          \
    X(EMPOLEON_TRIDENT)     \
    X(MAMOSWINE_TUSK)       \
    X(OCTILLERY_CANNON)     \
    X(HAXORUS_BLADE)        \
    X(TINKATON_HAMMER)      \
    X(BOXING_GLOVES)        \
    X(SCEPTILE_TAIL)        \
    X(BULBASAUR_BULB)       \
    X(HERACROSS_SHELL)      \
    X(SHIFTRY_BARK)         \
    X(SPOINK_PEARL)         \
    X(SHINX_STAR)           \
    X(SHUCKLE_SHELL)

#define RELIC_ENUM(name) RELIC_##name,
enum Relic
{
    RELIC_NONE,
    RELICS_LIST(RELIC_ENUM)
    RELICS_COUNT,
};
#undef RELIC_ENUM

#endif // GUARD_CONSTANTS_RELICS_H
