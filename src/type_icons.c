#include "global.h"
#include "battle.h"
#include "battle_anim.h"
#include "battle_controllers.h"
#include "battle_gimmick.h"
#include "decompress.h"
#include "graphics.h"
#include "pokedex.h"
#include "sprite.h"
#include "type_icons.h"

static u32 GetShowTypesMode(void);
static void LoadTypeSpritesAndPalettes(void);
static void LoadTypeIconsPerBattler(enum BattlerId, u32);

static bool32 UseDoubleBattleCoords(u32);

static enum Type GetMonPublicType(enum BattlerId, u32);
static bool32 ShouldHideUncaughtType(u32 species);
static bool32 ShouldHideUnseenType(u32 species);
static enum Type GetMonDefensiveTeraType(struct Pokemon *, struct Pokemon *, enum BattlerId, u32, u32, u32);
static bool32 IsIllusionActiveAndTypeUnchanged(struct Pokemon *, u32, enum BattlerId);

static void CreateSpriteFromType(u32, bool32, enum Type[], u32, enum BattlerId);
static bool32 ShouldSkipSecondType(enum Type[], u32);
static void SetTypeIconXY(s32*, s32*, u32, bool32, u32);

static void CreateSpriteAndSetTypeSpriteAttributes(enum Type, u32 x, u32 y, u32, enum BattlerId);
static bool32 ShouldFlipTypeIcon(u32, enum Type);

static void SpriteCB_TypeIcon(struct Sprite*);
static void DestroyTypeIcon(struct Sprite*);
static void FreeAllTypeIconResources(void);
static bool32 ShouldHideTypeIcon(enum BattlerId);
static s32 GetTypeIconHideMovement(bool32, u32);
static s32 GetTypeIconSlideMovement(bool32, u32, s32, s32);
static s32 GetTypeIconBounceMovement(s32, u32);

const struct Coords16 sTypeIconPositions[][2] =
{
    [B_POSITION_PLAYER_LEFT] =
    {
        [FALSE] = {221, 86},
        [TRUE] = {144, 71},
    },
    [B_POSITION_OPPONENT_LEFT] =
    {
        // Measured, not derived. The healthbox is created with subpriority 1
        // and these icons with 255, so anything overlapping the box is drawn
        // behind it and simply never appears. Sampling a real frame of this
        // repo's Gen 4 opponent healthbox puts its right edge at x 106
        // (x 103 is still its white outline, x 110 is already background).
        // Singles: the icon sits to the LEFT of the healthbox, which is where
        // upstream expansion put it and where the entry animation makes sense -
        // it emerges from under the box and retracts back under it. Soulgold
        // puts it on the right instead, but its healthbox art is much narrower.
        //
        // Measured off a real frame (mGBA, 1:1 sample of the framebuffer): the
        // box's left outline is a vertical edge at x 12 on every row, so the
        // free strip is x 0..11, twelve pixels. The sprite is 8 wide and its
        // stored x is the centre, so the resting x of 7 lands it on x 3..10:
        // three pixels off the screen edge, one clear of the box.
        //
        // The slide below walks the sprite 10px left of the value stored here,
        // hence 17. It starts at x 13..20, i.e. behind the box, which is what
        // makes it look like it slides out of the healthbox.
        [FALSE] = {17, 26},  // was {20, 26}, the upstream expansion default
        // Doubles keeps Soulgold's placement, to the right of the box: at this
        // size there is no room on the left. Offset from the healthbox origin
        // is +66 on both sides here and in Soulgold.
        [TRUE] = {100, 14},  // was {97, 14}
    },
    // Dead entries: LoadTypeIconsPerBattler() returns before it reaches the
    // player's side, exactly as Soulgold's does. Left at the upstream values
    // rather than guessed at, so nothing untested can reach the screen.
    [B_POSITION_PLAYER_RIGHT] =
    {
        [TRUE] = {156, 96},
    },
    [B_POSITION_OPPONENT_RIGHT] =
    {
        [TRUE] = {88, 39},   // was {85, 39}
    },
};

const union AnimCmd sSpriteAnim_TypeIcon_Normal[] =
{
    ANIMCMD_FRAME(TYPE_ICON_1_FRAME(TYPE_NORMAL), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Fighting[] =
{
    ANIMCMD_FRAME(TYPE_ICON_1_FRAME(TYPE_FIGHTING), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Flying[] =
{
    ANIMCMD_FRAME(TYPE_ICON_1_FRAME(TYPE_FLYING), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Poison[] =
{
    ANIMCMD_FRAME(TYPE_ICON_1_FRAME(TYPE_POISON), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Ground[] =
{
    ANIMCMD_FRAME(TYPE_ICON_1_FRAME(TYPE_GROUND), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Rock[] =
{
    ANIMCMD_FRAME(TYPE_ICON_1_FRAME(TYPE_ROCK), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Bug[] =
{
    ANIMCMD_FRAME(TYPE_ICON_1_FRAME(TYPE_BUG), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Ghost[] =
{
    ANIMCMD_FRAME(TYPE_ICON_1_FRAME(TYPE_GHOST), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Steel[] =
{
    ANIMCMD_FRAME(TYPE_ICON_1_FRAME(TYPE_STEEL), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Mystery[] =
{
    ANIMCMD_FRAME(TYPE_ICON_1_FRAME(TYPE_MYSTERY), 0),
    ANIMCMD_END
};

const union AnimCmd sSpriteAnim_TypeIcon_Fire[] =
{
    ANIMCMD_FRAME(TYPE_ICON_2_FRAME(TYPE_FIRE), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Water[] =
{
    ANIMCMD_FRAME(TYPE_ICON_2_FRAME(TYPE_WATER), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Grass[] =
{
    ANIMCMD_FRAME(TYPE_ICON_2_FRAME(TYPE_GRASS), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Electric[] =
{
    ANIMCMD_FRAME(TYPE_ICON_2_FRAME(TYPE_ELECTRIC), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Psychic[] =
{
    ANIMCMD_FRAME(TYPE_ICON_2_FRAME(TYPE_PSYCHIC), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Ice[] =
{
    ANIMCMD_FRAME(TYPE_ICON_2_FRAME(TYPE_ICE), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Dragon[] =
{
    ANIMCMD_FRAME(TYPE_ICON_2_FRAME(TYPE_DRAGON), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Dark[] =
{
    ANIMCMD_FRAME(TYPE_ICON_2_FRAME(TYPE_DARK), 0),
    ANIMCMD_END
};
const union AnimCmd sSpriteAnim_TypeIcon_Fairy[] =
{
    ANIMCMD_FRAME(TYPE_ICON_2_FRAME(TYPE_FAIRY), 0),
    ANIMCMD_END
};

const union AnimCmd *const sSpriteAnimTable_TypeIcons[] =
{
    [TYPE_NONE] =       sSpriteAnim_TypeIcon_Mystery,
    [TYPE_NORMAL] =     sSpriteAnim_TypeIcon_Normal,
    [TYPE_FIGHTING] =   sSpriteAnim_TypeIcon_Fighting,
    [TYPE_FLYING] =     sSpriteAnim_TypeIcon_Flying,
    [TYPE_POISON] =     sSpriteAnim_TypeIcon_Poison,
    [TYPE_GROUND] =     sSpriteAnim_TypeIcon_Ground,
    [TYPE_ROCK] =       sSpriteAnim_TypeIcon_Rock,
    [TYPE_BUG] =        sSpriteAnim_TypeIcon_Bug,
    [TYPE_GHOST] =      sSpriteAnim_TypeIcon_Ghost,
    [TYPE_STEEL] =      sSpriteAnim_TypeIcon_Steel,
    [TYPE_MYSTERY] =    sSpriteAnim_TypeIcon_Mystery,
    [TYPE_FIRE] =       sSpriteAnim_TypeIcon_Fire,
    [TYPE_WATER] =      sSpriteAnim_TypeIcon_Water,
    [TYPE_GRASS] =      sSpriteAnim_TypeIcon_Grass,
    [TYPE_ELECTRIC] =   sSpriteAnim_TypeIcon_Electric,
    [TYPE_PSYCHIC] =    sSpriteAnim_TypeIcon_Psychic,
    [TYPE_ICE] =        sSpriteAnim_TypeIcon_Ice,
    [TYPE_DRAGON] =     sSpriteAnim_TypeIcon_Dragon,
    [TYPE_DARK] =       sSpriteAnim_TypeIcon_Dark,
    [TYPE_FAIRY] =      sSpriteAnim_TypeIcon_Fairy,
    [TYPE_STELLAR] =    sSpriteAnim_TypeIcon_Mystery,
};

const struct SpritePalette sTypeIconPal1 =
{
    .data = gBattleIcons_Pal1,
    .tag = TYPE_ICON_TAG
};

const struct SpritePalette sTypeIconPal2 =
{
    .data = gBattleIcons_Pal2,
    .tag = TYPE_ICON_TAG_2
};

const struct OamData sOamData_TypeIcons =
{
    .affineMode = ST_OAM_AFFINE_OFF,
    .objMode = ST_OAM_OBJ_NORMAL,
    .shape = SPRITE_SHAPE(8x16),
    .size = SPRITE_SIZE(8x16),
    .priority = 1,
};

const struct CompressedSpriteSheet sSpriteSheet_TypeIcons2 =
{
    .data = gBattleIcons_Gfx2,
    .size = (8*16) * 9,
    .tag = TYPE_ICON_TAG_2,
};

const struct CompressedSpriteSheet sSpriteSheet_TypeIcons1 =
{
    .data = gBattleIcons_Gfx1,
    .size = (8*16) * 10,
    .tag = TYPE_ICON_TAG,
};

const struct SpriteTemplate sSpriteTemplate_TypeIcons1 =
{
    .tileTag = TYPE_ICON_TAG,
    .paletteTag = TYPE_ICON_TAG,
    .oam = &sOamData_TypeIcons,
    .anims = sSpriteAnimTable_TypeIcons,
    .callback = SpriteCB_TypeIcon
};

const struct SpriteTemplate sSpriteTemplate_TypeIcons2 =
{
    .tileTag = TYPE_ICON_TAG_2,
    .paletteTag = TYPE_ICON_TAG_2,
    .oam = &sOamData_TypeIcons,
    .anims = sSpriteAnimTable_TypeIcons,
    .callback = SpriteCB_TypeIcon
};

// The in-game TYPE ICONS option stands in for the B_SHOW_TYPES build switch. Its index 0 is OFF,
// so a save from before the option existed shows no icons, as HnS did.
static u32 GetShowTypesMode(void)
{
    static const u8 sModes[] = {SHOW_TYPES_NEVER, SHOW_TYPES_SEEN, SHOW_TYPES_CAUGHT, SHOW_TYPES_ALWAYS};

    return sModes[gSaveBlock3Ptr->challengeSettings.typeIcons];
}

void LoadTypeIcons(enum BattlerId battler)
{
    u32 position;

    struct Pokemon* mon = GetBattlerMon(battler);
    u32 species = GetMonData(mon, MON_DATA_SPECIES);

    if (GetShowTypesMode() == SHOW_TYPES_NEVER
        || (GetShowTypesMode() == SHOW_TYPES_SEEN && !GetSetPokedexFlag(SpeciesToNationalPokedexNum(species), FLAG_GET_SEEN)))
        return;

    LoadTypeSpritesAndPalettes();

    for (position = 0; position < gBattlersCount; ++position)
        LoadTypeIconsPerBattler(battler, position);
}

static void LoadTypeSpritesAndPalettes(void)
{
    if (IndexOfSpritePaletteTag(TYPE_ICON_TAG) != UCHAR_MAX)
        return;

    LoadCompressedSpriteSheet(&sSpriteSheet_TypeIcons1);
    LoadCompressedSpriteSheet(&sSpriteSheet_TypeIcons2);
    LoadSpritePalette(&sTypeIconPal1);
    LoadSpritePalette(&sTypeIconPal2);
}

static void LoadTypeIconsPerBattler(enum BattlerId battler, u32 position)
{
    u32 typeNum;
    enum Type types[2];
    enum BattlerId battlerId = GetBattlerAtPosition(position);
    bool32 useDoubleBattleCoords = UseDoubleBattleCoords(battlerId);

    // Only the opposing side gets icons, as in Soulgold. Your own Pokemon's
    // types are never a question, and the player-side coordinates below are
    // the untested upstream defaults.
    if (IsOnPlayerSide(battlerId) || !IsBattlerAlive(battlerId))
        return;

    for (typeNum = 0; typeNum < 2; ++typeNum)
        types[typeNum] = GetMonPublicType(battlerId, typeNum);

    for (typeNum = 0; typeNum < 2; ++typeNum)
        CreateSpriteFromType(position, useDoubleBattleCoords, types, typeNum, battler);
}

static bool32 UseDoubleBattleCoords(u32 position)
{
    if (!IsDoubleBattle())
        return FALSE;

    if ((position == B_POSITION_PLAYER_LEFT) && (gBattleMons[B_POSITION_PLAYER_RIGHT].species == SPECIES_NONE))
        return FALSE;

    if ((position == B_POSITION_OPPONENT_LEFT) && (gBattleMons[B_POSITION_OPPONENT_RIGHT].species == SPECIES_NONE))
        return FALSE;

    return TRUE;
}

static enum Type GetMonPublicType(enum BattlerId battlerId, u32 typeNum)
{
    struct Pokemon *mon = GetBattlerMon(battlerId);
    u32 monSpecies = GetMonData(mon,MON_DATA_SPECIES,NULL);
    struct Pokemon *monIllusion;
    u32 illusionSpecies;

    if (ShouldHideUncaughtType(monSpecies) || ShouldHideUnseenType(monSpecies))
        return TYPE_MYSTERY;

    monIllusion = GetIllusionMonPtr(battlerId);
    // GetIllusionMonPtr() returns NULL whenever no Illusion is up, which is the
    // common case. Both helpers below already guard for it; this read did not.
    // Ported from Soulgold.
    illusionSpecies = monIllusion != NULL ? GetMonData(monIllusion, MON_DATA_SPECIES) : SPECIES_NONE;

    if (GetActiveGimmick(battlerId) == GIMMICK_TERA)
        return GetMonDefensiveTeraType(mon,monIllusion,battlerId,typeNum,illusionSpecies,monSpecies);

    if (IsIllusionActiveAndTypeUnchanged(monIllusion,monSpecies, battlerId))
        return GetSpeciesType(illusionSpecies, typeNum);

    return gBattleMons[battlerId].types[typeNum];
}

static bool32 ShouldHideUncaughtType(u32 species)
{
    if (GetShowTypesMode() != SHOW_TYPES_CAUGHT)
        return FALSE;

    if (GetSetPokedexFlag(SpeciesToNationalPokedexNum(species), FLAG_GET_CAUGHT))
        return FALSE;

    return TRUE;
}

static bool32 ShouldHideUnseenType(u32 species)
{
    if (GetShowTypesMode() != SHOW_TYPES_SEEN)
        return FALSE;

    if (GetSetPokedexFlag(SpeciesToNationalPokedexNum(species), FLAG_GET_SEEN))
        return FALSE;

    return TRUE;
}

static enum Type GetMonDefensiveTeraType(struct Pokemon *mon, struct Pokemon *monIllusion, enum BattlerId battlerId, u32 typeNum, u32 illusionSpecies, u32 monSpecies)
{
    enum Type teraType = GetBattlerTeraType(battlerId);
    u32 targetSpecies;

    if (teraType != TYPE_STELLAR)
        return teraType;

    targetSpecies = (monIllusion != NULL) ? illusionSpecies : monSpecies;

    return GetSpeciesType(targetSpecies, typeNum);
}

static bool32 IsIllusionActiveAndTypeUnchanged(struct Pokemon *monIllusion, u32 monSpecies, enum BattlerId battlerId)
{
    u32 typeNum;

    if (monIllusion == NULL)
        return FALSE;

    for (typeNum = 0; typeNum < 2; typeNum++)
        if (GetSpeciesType(monSpecies, typeNum) != gBattleMons[battlerId].types[typeNum])
        return FALSE;

    return TRUE;
}

static void CreateSpriteFromType(u32 position, bool32 useDoubleBattleCoords, enum Type types[], u32 typeNum, enum BattlerId battler)
{
    s32 x = 0, y = 0;

    if (ShouldSkipSecondType(types, typeNum))
        return;

    SetTypeIconXY(&x, &y, position, useDoubleBattleCoords, typeNum);

    CreateSpriteAndSetTypeSpriteAttributes(types[typeNum], x, y, position, battler);
}

static bool32 ShouldSkipSecondType(enum Type types[], u32 typeNum)
{
    if (!typeNum)
        return FALSE;

    if (types[0] != types[1])
        return FALSE;

    return TRUE;
}

static void SetTypeIconXY(s32* x, s32* y, u32 position, bool32 useDoubleBattleCoords, u32 typeNum)
{
    *x = sTypeIconPositions[position][useDoubleBattleCoords].x;
    *y = sTypeIconPositions[position][useDoubleBattleCoords].y + (11 * typeNum);

    // The two icons of a dual type are stacked 11px apart; Soulgold also steps
    // the lower one 4px right, which is the HGSS look. That only works where
    // the pair sits to the right of the healthbox, so it is kept for doubles
    // and dropped in singles: there the icons are in the 12px strip left of the
    // box, and 4px either way would clip the screen edge or hide half the glyph
    // behind the box.
    if (typeNum != 0 && useDoubleBattleCoords
     && GetBattlerSide(GetBattlerAtPosition(position)) == B_SIDE_OPPONENT)
        *x += 4;
}

static void CreateSpriteAndSetTypeSpriteAttributes(enum Type type, u32 x, u32 y, u32 position, enum BattlerId battler)
{
    struct Sprite* sprite;
    const struct SpriteTemplate* spriteTemplate = gTypesInfo[type].useSecondTypeIconPalette ? &sSpriteTemplate_TypeIcons2 : &sSpriteTemplate_TypeIcons1;
    u32 spriteId = CreateSpriteAtEnd(spriteTemplate, x, y, UCHAR_MAX);

    if (spriteId == MAX_SPRITES)
        return;

    sprite = &gSprites[spriteId];
    sprite->tMonPosition = position;
    sprite->tBattlerId = battler;
    sprite->tVerticalPosition = y;
    // Each icon remembers its own resting x. The slide animation used to clamp
    // against the shared table entry, which is only correct while both icons of
    // a dual type sit at the same x - it stops being true with the indent in
    // SetTypeIconXY below. Ported from Soulgold.
    sprite->tHorizontalPosition = x;

    sprite->hFlip = ShouldFlipTypeIcon(position, type);

    StartSpriteAnim(sprite, type);
}

// The glyphs in graphics/types/battle_icons*.png are strongly asymmetric, and
// which way they should face depends on which side of the healthbox the icon
// sits on - not on how many battlers there are. Upstream expansion picked the
// player side in singles and the opposing side in doubles, which cannot both be
// right; the effect here was that the opposing icons came out mirrored in
// singles and not in doubles. Soulgold flips on the opposing side in both,
// because it always draws the icons to the RIGHT of the box.
//
// Singles here does not: this repo's Gen 4 healthbox is much wider, so the icon
// goes to the LEFT of the box instead, in the 12 free pixels measured there
// (see sTypeIconPositions). With Soulgold's rule the asymmetric glyph then
// faced away from the box; unflipped it faces it. Doubles keeps Soulgold's
// layout, to the right of the box, so it keeps Soulgold's flip.
static bool32 ShouldFlipTypeIcon(u32 position, enum Type typeId)
{
    u32 battlerId = GetBattlerAtPosition(position);

    if (GetBattlerSide(battlerId) != B_SIDE_OPPONENT)
        return FALSE;

    if (!UseDoubleBattleCoords(battlerId))
        return FALSE;

    return !gTypesInfo[typeId].isSpecialCaseType;
}

static void SpriteCB_TypeIcon(struct Sprite *sprite)
{
    u32 position = sprite->tMonPosition;
    enum BattlerId battlerId = sprite->tBattlerId;
    bool32 useDoubleBattleCoords = UseDoubleBattleCoords(GetBattlerAtPosition(position));

    if (sprite->tHideIconTimer == NUM_FRAMES_HIDE_TYPE_ICON)
    {
        DestroyTypeIcon(sprite);
        return;
    }

    if (ShouldHideTypeIcon(battlerId))
    {
        sprite->x += GetTypeIconHideMovement(useDoubleBattleCoords, position);
        ++sprite->tHideIconTimer;
        return;
    }

    // tHideIconTimer is the frame counter of the retract animation, so it has
    // to start over every time the icon is visible again. Upstream only ever
    // increments it: any frame on which gBattlerControllerFuncs briefly holds
    // something outside sShowTypesControllerFuncs is banked, and after ten such
    // frames - spread over as long as it takes - the icon drifts back into the
    // healthbox and destroys itself in the middle of move selection. Resetting
    // it makes the retract need ten consecutive frames, which is what the
    // animation was written for; the slide below then pulls the icon back to
    // its resting x on its own.
    sprite->tHideIconTimer = 0;

    sprite->x += GetTypeIconSlideMovement(useDoubleBattleCoords, position, sprite->x, sprite->tHorizontalPosition);
    sprite->y = GetTypeIconBounceMovement(sprite->tVerticalPosition,position);
}

static const u32 typeIconTags[] =
{
    TYPE_ICON_TAG,
    TYPE_ICON_TAG_2
};

static void DestroyTypeIcon(struct Sprite* sprite)
{
    u32 spriteId, tag;

    DestroySpriteAndFreeResources(sprite);

    for (spriteId = 0; spriteId < MAX_SPRITES; ++spriteId)
    {
        if (!gSprites[spriteId].inUse)
            continue;

        for (tag = 0; tag < 2; tag++)
        {
            if (gSprites[spriteId].template->paletteTag == typeIconTags[tag])
                return;

            if (gSprites[spriteId].template->tileTag == typeIconTags[tag])
                return;
        }
    }

    FreeAllTypeIconResources();
}

static void FreeAllTypeIconResources(void)
{
    u32 tag;

    for (tag = 0; tag < 2; tag++)
    {
        FreeSpriteTilesByTag(typeIconTags[tag]);
        FreeSpritePaletteByTag(typeIconTags[tag]);
    }
}

static void (*const sShowTypesControllerFuncs[])(enum BattlerId battler) =
{
    PlayerHandleChooseMove,
    HandleChooseMoveAfterDma3,
    HandleInputChooseTarget,
    HandleInputShowTargets,
    HandleInputShowEntireFieldTargets,
    HandleMoveSwitching,
    HandleInputChooseMove,
};


static bool32 ShouldHideTypeIcon(enum BattlerId battlerId)
{
    u32 funcIndex;

    for (funcIndex = 0; funcIndex < ARRAY_COUNT(sShowTypesControllerFuncs); funcIndex++)
        if (gBattlerControllerFuncs[battlerId] == sShowTypesControllerFuncs[funcIndex])
            return FALSE;

    return TRUE;
}

static s32 GetTypeIconHideMovement(bool32 useDoubleBattleCoords, u32 position)
{
    if (useDoubleBattleCoords)
    {
        if (position == B_POSITION_PLAYER_LEFT || position == B_POSITION_PLAYER_RIGHT)
            return 1;
        else
            return -1;
    }

    // Singles is the mirror of Soulgold's because the icon is on the other side
    // of the box here: it retracts to the right, back under the healthbox.
    if (position == B_POSITION_PLAYER_LEFT)
        return -1;
    else
        return 1;
}

static s32 GetTypeIconSlideMovement(bool32 useDoubleBattleCoords, u32 position, s32 xPos, s32 originalX)
{
    if (useDoubleBattleCoords)
    {
        switch (position)
        {
        case B_POSITION_PLAYER_LEFT:
        case B_POSITION_PLAYER_RIGHT:
            if (xPos > originalX - 10)
                return -1;
            break;
        default:
        case B_POSITION_OPPONENT_LEFT:
        case B_POSITION_OPPONENT_RIGHT:
            if (xPos < originalX + 10)
                return 1;
            break;
        }
        return 0;
    }

    // Same mirror as in GetTypeIconHideMovement: in singles the opposing icon
    // slides out to the LEFT of its stored x, away from the healthbox, so the
    // resting position is stored x - 10 and the retract above walks it back.
    if (position == B_POSITION_PLAYER_LEFT)
    {
        if (xPos < originalX + 10)
            return 1;
    }
    else
    {
        if (xPos > originalX - 10)
            return -1;
    }
    return 0;
}

static s32 GetTypeIconBounceMovement(s32 originalY, u32 position)
{
    struct Sprite *healthbox = &gSprites[gHealthboxSpriteIds[GetBattlerAtPosition(position)]];
    return originalY + healthbox->y2;
}
