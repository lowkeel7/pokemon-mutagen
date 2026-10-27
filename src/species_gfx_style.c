#include "global.h"
#include "data.h"
#include "graphics.h"
#include "pokemon.h"
#include "species_gfx_style.h"

#include "data/pokemon/species_gfx_ds.h"

#if P_GBA_STYLE_SPECIES_GFX
static const u32 sSubstituteDs[] = INCBIN_U32("graphics/battle_anims/sprites/substitute.4bpp.smol");
static const u32 sSubstituteBackDs[] = INCBIN_U32("graphics/battle_anims/sprites/substitute_back.4bpp.smol");
static const u16 sSubstitutePalDs[] = INCBIN_U16("graphics/battle_anims/sprites/substitute.gbapal");
#endif

// The SPRITES option (BACKLOG SG-23), zero = GBA style. A DS-style build has nothing to swap in.
bool32 UseDsSpriteStyle(void)
{
    if (!P_GBA_STYLE_SPECIES_GFX)
        return TRUE;
    return gSaveBlock3Ptr != NULL && gSaveBlock3Ptr->challengeSettings.tx_Features_SpriteStyle;
}

// Gen 4 shadows are placed for the DS-style art, so they come with it.
bool32 UseGen4EnemyShadows(void)
{
    return B_ENEMY_MON_SHADOW_STYLE >= GEN_4 && UseDsSpriteStyle();
}

// The DS-style art of a species, or NULL in GBA style and for the species whose art is the same.
static const struct SpeciesGfxDs *GetSpeciesGfxDs(u32 species)
{
#if P_GBA_STYLE_SPECIES_GFX
    if (species < NUM_SPECIES && sSpeciesGfxDsIndex[species] != 0 && UseDsSpriteStyle())
        return &sSpeciesGfxDs[sSpeciesGfxDsIndex[species] - 1];
#endif
    return NULL;
}

const u32 *GetSpeciesFrontPic(u32 species, bool32 isFemale)
{
    const struct SpeciesGfxDs *ds = GetSpeciesGfxDs(species);
    const u32 *pic = ds != NULL ? ds->frontPic : gSpeciesInfo[species].frontPic;
#if P_GENDER_DIFFERENCES
    const u32 *female = ds != NULL ? ds->frontPicFemale : gSpeciesInfo[species].frontPicFemale;
    if (isFemale && female != NULL)
        return female;
#endif
    return pic != NULL ? pic : gSpeciesInfo[SPECIES_NONE].frontPic;
}

const u32 *GetSpeciesBackPic(u32 species, bool32 isFemale)
{
    const struct SpeciesGfxDs *ds = GetSpeciesGfxDs(species);
    const u32 *pic = ds != NULL ? ds->backPic : gSpeciesInfo[species].backPic;
#if P_GENDER_DIFFERENCES
    const u32 *female = ds != NULL ? ds->backPicFemale : gSpeciesInfo[species].backPicFemale;
    if (isFemale && female != NULL)
        return female;
#endif
    return pic != NULL ? pic : gSpeciesInfo[SPECIES_NONE].backPic;
}

// The DS-style palette, or NULL when the caller's own rules apply. HnS's modern shiny palettes are
// drawn for the GBA-style art; the DS-style shinies already have the modern colours.
const u16 *GetSpeciesPaletteDs(u32 species, bool32 isShiny, bool32 isFemale)
{
    const struct SpeciesGfxDs *ds = GetSpeciesGfxDs(species);
    if (ds == NULL)
        return NULL;
    if (isShiny)
        return isFemale && ds->shinyPaletteFemale != NULL ? ds->shinyPaletteFemale : ds->shinyPalette;
    return isFemale && ds->paletteFemale != NULL ? ds->paletteFemale : ds->palette;
}

// NULL when the species has no female icon.
const u8 *GetSpeciesIconFemale(u32 species)
{
#if P_GENDER_DIFFERENCES
    const struct SpeciesGfxDs *ds = GetSpeciesGfxDs(species);
    return ds != NULL ? ds->iconSpriteFemale : gSpeciesInfo[species].iconSpriteFemale;
#else
    return NULL;
#endif
}

u32 GetSpeciesIconPalIndexFemale(u32 species)
{
#if P_GENDER_DIFFERENCES
    const struct SpeciesGfxDs *ds = GetSpeciesGfxDs(species);
    return ds != NULL ? ds->iconPalIndexFemale : gSpeciesInfo[species].iconPalIndexFemale;
#else
    return gSpeciesInfo[species].iconPalIndex;
#endif
}

u32 GetSpeciesFrontPicSize(u32 species, bool32 isFemale)
{
    const struct SpeciesGfxDs *ds = GetSpeciesGfxDs(species);
#if P_GENDER_DIFFERENCES
    if (isFemale && (ds != NULL ? ds->frontPicFemale : gSpeciesInfo[species].frontPicFemale) != NULL)
        return ds != NULL ? ds->frontPicSizeFemale : gSpeciesInfo[species].frontPicSizeFemale;
#endif
    return ds != NULL ? ds->frontPicSize : gSpeciesInfo[species].frontPicSize;
}

u32 GetSpeciesBackPicSize(u32 species, bool32 isFemale)
{
    const struct SpeciesGfxDs *ds = GetSpeciesGfxDs(species);
#if P_GENDER_DIFFERENCES
    if (isFemale && (ds != NULL ? ds->backPicFemale : gSpeciesInfo[species].backPicFemale) != NULL)
        return ds != NULL ? ds->backPicSizeFemale : gSpeciesInfo[species].backPicSizeFemale;
#endif
    return ds != NULL ? ds->backPicSize : gSpeciesInfo[species].backPicSize;
}

u32 GetSpeciesFrontPicYOffset(u32 species)
{
    const struct SpeciesGfxDs *ds = GetSpeciesGfxDs(species);
    return ds != NULL ? ds->frontPicYOffset : gSpeciesInfo[species].frontPicYOffset;
}

u32 GetSpeciesBackPicYOffset(u32 species)
{
    const struct SpeciesGfxDs *ds = GetSpeciesGfxDs(species);
    return ds != NULL ? ds->backPicYOffset : gSpeciesInfo[species].backPicYOffset;
}

u32 GetSpeciesEnemyMonElevation(u32 species)
{
    const struct SpeciesGfxDs *ds = GetSpeciesGfxDs(species);
    return ds != NULL ? ds->enemyMonElevation : gSpeciesInfo[species].enemyMonElevation;
}

u32 GetSpeciesFrontAnimId(u32 species)
{
    const struct SpeciesGfxDs *ds = GetSpeciesGfxDs(species);
    return ds != NULL ? ds->frontAnimId : gSpeciesInfo[species].frontAnimId;
}

u32 GetSpeciesBackAnimId(u32 species)
{
    const struct SpeciesGfxDs *ds = GetSpeciesGfxDs(species);
    return ds != NULL ? ds->backAnimId : gSpeciesInfo[species].backAnimId;
}

u32 GetSpeciesFrontAnimDelay(u32 species)
{
    const struct SpeciesGfxDs *ds = GetSpeciesGfxDs(species);
    return ds != NULL ? ds->frontAnimDelay : gSpeciesInfo[species].frontAnimDelay;
}

const union AnimCmd *const *GetSpeciesFrontAnimFrames(u32 species)
{
    const struct SpeciesGfxDs *ds = GetSpeciesGfxDs(species);
    if (ds != NULL && ds->frontAnimFrames != NULL)
        return ds->frontAnimFrames;
    return gSpeciesInfo[species].frontAnimFrames;
}

// The Substitute doll that stands in for a battler, in the same style as the Pokémon.
const u32 *GetSubstitutePic(bool32 isBack)
{
#if P_GBA_STYLE_SPECIES_GFX
    if (UseDsSpriteStyle())
        return isBack ? sSubstituteBackDs : sSubstituteDs;
#endif
    return isBack ? gBattleAnimSpriteGfx_SubstituteBack : gBattleAnimSpriteGfx_Substitute;
}

const u16 *GetSubstitutePalette(void)
{
#if P_GBA_STYLE_SPECIES_GFX
    if (UseDsSpriteStyle())
        return sSubstitutePalDs;
#endif
    return gBattleAnimSpritePal_Substitute;
}
