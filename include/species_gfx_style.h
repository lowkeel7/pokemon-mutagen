#ifndef GUARD_SPECIES_GFX_STYLE_H
#define GUARD_SPECIES_GFX_STYLE_H

// The SPRITES option (BACKLOG SG-23). GBA style, zero and HnS's look, is gSpeciesInfo as built;
// DS style swaps in the DS-era art of the species that have both (Gen 1-3), from
// src/data/pokemon/species_gfx_ds.h. Read a Pokémon's battle art through these, not gSpeciesInfo.

union AnimCmd;

struct SpeciesGfxDs
{
    const u32 *frontPic;
    const u32 *backPic;
    const u16 *palette;
    const u16 *shinyPalette;
    const u32 *frontPicFemale;
    const u32 *backPicFemale;
    const u16 *paletteFemale;
    const u16 *shinyPaletteFemale;
    const u8 *iconSpriteFemale;
    const union AnimCmd *const *frontAnimFrames; // NULL: the same as gSpeciesInfo's
    u8 frontPicSize;
    u8 frontPicYOffset;
    u8 backPicSize;
    u8 backPicYOffset;
    u8 frontPicSizeFemale;
    u8 backPicSizeFemale;
    u8 enemyMonElevation;
    u8 frontAnimId;
    u8 backAnimId;
    u8 frontAnimDelay;
    u8 iconPalIndexFemale;
};

bool32 UseDsSpriteStyle(void);
bool32 UseGen4EnemyShadows(void);
const u32 *GetSpeciesFrontPic(u32 species, bool32 isFemale);
const u32 *GetSpeciesBackPic(u32 species, bool32 isFemale);
const u16 *GetSpeciesPaletteDs(u32 species, bool32 isShiny, bool32 isFemale);
const u8 *GetSpeciesIconFemale(u32 species);
u32 GetSpeciesIconPalIndexFemale(u32 species);
u32 GetSpeciesFrontPicSize(u32 species, bool32 isFemale);
u32 GetSpeciesBackPicSize(u32 species, bool32 isFemale);
u32 GetSpeciesFrontPicYOffset(u32 species);
u32 GetSpeciesBackPicYOffset(u32 species);
u32 GetSpeciesEnemyMonElevation(u32 species);
u32 GetSpeciesFrontAnimId(u32 species);
u32 GetSpeciesBackAnimId(u32 species);
u32 GetSpeciesFrontAnimDelay(u32 species);
const union AnimCmd *const *GetSpeciesFrontAnimFrames(u32 species);
const u32 *GetSubstitutePic(bool32 isBack);
const u16 *GetSubstitutePalette(void);

#endif // GUARD_SPECIES_GFX_STYLE_H
