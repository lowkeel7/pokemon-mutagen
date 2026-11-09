#ifndef GUARD_CONSTANTS_RELICS_H
#define GUARD_CONSTANTS_RELICS_H

// Species parts a Pokémon can wear (Pokémon Mutagen, SG-09). One index per Pokémon, 6 bits
// (PokemonSubstruct0.relic); RELIC_NONE is zero so every older save reads "nothing worn".
#define RELIC_NONE          0
#define RELIC_CUBONE_SKULL  1
#define RELICS_COUNT        2

#endif // GUARD_CONSTANTS_RELICS_H
