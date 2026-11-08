#ifndef GUARD_SPECIES_PICKER_H
#define GUARD_SPECIES_PICKER_H

// A scrolling list of every species, drawn over the field like the debug menu (Pokémon Mutagen,
// BACKLOG SG-16). The caller's script stops with waitstate; when the list closes, gSpecialVar_Result
// holds the species, or 0 when the player backed out, and the script is enabled again.
void SpeciesPicker_Open(u16 initialSpecies);

#endif // GUARD_SPECIES_PICKER_H
