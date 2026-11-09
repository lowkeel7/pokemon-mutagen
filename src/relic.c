// Pokémon Mutagen (SG-09): species parts a Pokémon wears. docs/pokerom/design/items.md.
//
// A part is one index per Pokémon (PokemonSubstruct0.relic, 6 bits). Put on from the bag
// (party_menu.c, ItemUseCB_Relic), it grants its ability whatever the species (pokemon.c,
// GetMonAbility) and is drawn over the Pokémon's sprite in battle and in the summary: a 32x32 cell
// that follows the Pokémon's sprite, sitting on the head line of its first frame. MUTAGEN → RELICS
// (zero = Heart & Soul) gates every effect; the field itself is kept either way.
#include "global.h"
#include "battle.h"
#include "battle_anim.h"
#include "battle_util.h"
#include "graphics.h"
#include "mutagen.h"
#include "pokemon.h"
#include "relic.h"
#include "sprite.h"
#include "constants/abilities.h"
#include "constants/items.h"

#include "data/relics.h"

#define TAG_RELIC_GFX 0x5E1C   // plus the part's index: one sheet and one palette per kind of part
#define TAG_RELIC_PAL 0x5E1C
#define RELIC_CELL 32          // the overlay cell; the art is bottom-aligned in it
#define RELIC_SINK 6           // the cell's bottom sits this far below the head line, so the part sits on the head

// sprite->data
#define sBattler   data[0]     // MAX_BATTLERS_COUNT outside a battle (the summary screen)
#define sMonSprite data[1]
#define sOffsetX   data[2]
#define sOffsetY   data[3]

static u8 sBattlerOverlay[MAX_BATTLERS_COUNT];

static void SpriteCB_Relic(struct Sprite *sprite);

static const struct OamData sOamData_Relic =
{
    .affineMode = ST_OAM_AFFINE_OFF,
    .objMode = ST_OAM_OBJ_NORMAL,
    .bpp = ST_OAM_4BPP,
    .shape = SPRITE_SHAPE(32x32),
    .size = SPRITE_SIZE(32x32),
    .priority = 2,
};

static const struct SpriteTemplate sSpriteTemplate_Relic =
{
    .tileTag = TAG_RELIC_GFX,
    .paletteTag = TAG_RELIC_PAL,
    .oam = &sOamData_Relic,
    .anims = gDummySpriteAnimTable,
    .images = NULL,
    .affineAnims = gDummySpriteAffineAnimTable,
    .callback = SpriteCB_Relic,
};

u32 RelicFromItem(u16 item)
{
    u32 i;

    for (i = RELIC_NONE + 1; i < RELICS_COUNT; i++)
    {
        if (gRelicsInfo[i].item == item)
            return i;
    }
    return RELIC_NONE;
}

enum Ability GetRelicAbility(u32 relic)
{
    return relic < RELICS_COUNT ? gRelicsInfo[relic].ability : ABILITY_NONE;
}

u32 GetMonRelic(struct Pokemon *mon)
{
    u32 relic;

    if (!AreRelicsOn() || mon == NULL || GetMonData(mon, MON_DATA_IS_EGG))
        return RELIC_NONE;
    relic = GetMonData(mon, MON_DATA_RELIC);
    return relic < RELICS_COUNT ? relic : RELIC_NONE;
}

// 4bpp, 8x8 tiles, 8 tiles a row: the pixel at (x, y) of a 64x64 frame.
static u32 FramePixel(const u8 *frame, u32 x, u32 y)
{
    const u8 *tile = frame + ((y >> 3) * 8 + (x >> 3)) * TILE_SIZE_4BPP;
    u8 pair = tile[(y & 7) * 4 + ((x & 7) >> 1)];

    return (x & 1) ? pair >> 4 : pair & 0xF;
}

// The head line: the first row from the top whose drawn width is a fair share of the sprite's, so
// ears, horns and antennae are passed over; returns its centre. FALSE for a blank frame.
static bool32 FindHeadLine(const u8 *frame, s32 *outX, s32 *outY)
{
    u8 count[MON_PIC_HEIGHT], first[MON_PIC_HEIGHT], last[MON_PIC_HEIGHT];
    s32 x, y, minX = MON_PIC_WIDTH, maxX = -1, threshold, top = -1;

    for (y = 0; y < MON_PIC_HEIGHT; y++)
    {
        count[y] = first[y] = last[y] = 0;
        for (x = 0; x < MON_PIC_WIDTH; x++)
        {
            if (FramePixel(frame, x, y) == 0)
                continue;
            if (count[y] == 0)
                first[y] = x;
            last[y] = x;
            count[y]++;
            if (x < minX)
                minX = x;
            if (x > maxX)
                maxX = x;
            if (top < 0)
                top = y;
        }
    }
    if (maxX < 0)
        return FALSE;
    threshold = (maxX - minX + 1) * 7 / 20;
    if (threshold < 6)
        threshold = 6;
    for (y = top; y < MON_PIC_HEIGHT; y++)
    {
        if (count[y] >= threshold)
        {
            *outX = (first[y] + last[y]) / 2;
            *outY = y;
            return TRUE;
        }
    }
    *outX = (first[top] + last[top]) / 2;
    *outY = top;
    return TRUE;
}

u8 Relic_CreateOverlay(u32 relic, u8 monSpriteId, const u8 *frame, bool32 back, u8 subpriority)
{
    struct SpriteTemplate template = sSpriteTemplate_Relic;
    struct SpriteSheet sheet;
    struct SpritePalette palette;
    struct Sprite *sprite;
    s32 headX, headY;
    u8 spriteId;

    if (relic == RELIC_NONE || relic >= RELICS_COUNT || gRelicsInfo[relic].gfx == NULL
     || monSpriteId >= MAX_SPRITES || frame == NULL || !FindHeadLine(frame, &headX, &headY))
        return SPRITE_NONE;

    sheet = (struct SpriteSheet){ .data = gRelicsInfo[relic].gfx, .size = RELIC_CELL * RELIC_CELL, .tag = TAG_RELIC_GFX + relic };
    palette = (struct SpritePalette){ .data = gRelicsInfo[relic].palette, .tag = TAG_RELIC_PAL + relic };
    if (GetSpriteTileStartByTag(sheet.tag) == 0xFFFF && LoadSpriteSheet(&sheet) == 0xFFFF)
        return SPRITE_NONE;
    if (IndexOfSpritePaletteTag(palette.tag) == 0xFF && LoadSpritePalette(&palette) == 0xFF)
        return SPRITE_NONE;

    template.tileTag = sheet.tag;
    template.paletteTag = palette.tag;
    spriteId = CreateSprite(&template, 0, 0, subpriority > 0 ? subpriority - 1 : 0);
    if (spriteId == MAX_SPRITES)
        return SPRITE_NONE;
    sprite = &gSprites[spriteId];
    sprite->sBattler = MAX_BATTLERS_COUNT;
    sprite->sMonSprite = monSpriteId;
    sprite->sOffsetX = headX - MON_PIC_WIDTH / 2;
    sprite->sOffsetY = headY - MON_PIC_HEIGHT / 2 + RELIC_SINK - RELIC_CELL / 2;
    if (back)
        sprite->oam.tileNum += (RELIC_CELL / 8) * (RELIC_CELL / 8);   // the lower cell of the sheet
    SpriteCB_Relic(sprite);
    return spriteId;
}

static void SpriteCB_Relic(struct Sprite *sprite)
{
    struct Sprite *mon;
    bool32 invisible;

    if (sprite->sMonSprite >= MAX_SPRITES || !gSprites[sprite->sMonSprite].inUse)
    {
        if (sprite->sBattler < MAX_BATTLERS_COUNT)
            sBattlerOverlay[sprite->sBattler] = SPRITE_NONE;
        DestroySprite(sprite);
        return;
    }
    mon = &gSprites[sprite->sMonSprite];
    invisible = mon->invisible;
    if (sprite->sBattler < MAX_BATTLERS_COUNT)
    {
        u32 battler = sprite->sBattler;

        if (gBattleSpritesDataPtr == NULL || !IsBattlerSpritePresent(battler)
         || gBattleSpritesDataPtr->battlerData[battler].behindSubstitute)
            invisible = TRUE;
        // Hidden while the sprite is scaled (the ball's emerge, Minimize…): the part would float off it.
        if (mon->oam.affineMode != ST_OAM_AFFINE_OFF
         && (gOamMatrices[mon->oam.matrixNum].a != 0x100 || gOamMatrices[mon->oam.matrixNum].d != 0x100))
            invisible = TRUE;
    }
    sprite->x = mon->x + sprite->sOffsetX;
    sprite->y = mon->y + sprite->sOffsetY;
    sprite->x2 = mon->x2;
    sprite->y2 = mon->y2;
    sprite->oam.priority = mon->oam.priority;
    sprite->subpriority = mon->subpriority > 0 ? mon->subpriority - 1 : 0;
    sprite->invisible = invisible;
}

void Relic_BattleInit(void)
{
    u32 i;

    for (i = 0; i < MAX_BATTLERS_COUNT; i++)
        sBattlerOverlay[i] = SPRITE_NONE;
}

void Relic_DetachFromBattler(u32 battler)
{
    if (battler >= MAX_BATTLERS_COUNT)
        return;
    if (sBattlerOverlay[battler] < MAX_SPRITES && gSprites[sBattlerOverlay[battler]].inUse
     && gSprites[sBattlerOverlay[battler]].callback == SpriteCB_Relic)
        DestroySprite(&gSprites[sBattlerOverlay[battler]]);
    sBattlerOverlay[battler] = SPRITE_NONE;
}

void Relic_AttachToBattler(u32 battler)
{
    struct Pokemon *party;
    const u8 *frame;
    u32 relic;
    u8 spriteId;

    Relic_DetachFromBattler(battler);
    if (battler >= MAX_BATTLERS_COUNT || gBattlerSpriteIds[battler] >= MAX_SPRITES || gMonSpritesGfxPtr == NULL)
        return;
    if ((gBattleTypeFlags & BATTLE_TYPE_GHOST) && !IsOnPlayerSide(battler))
        return;
    party = IsOnPlayerSide(battler) ? gPlayerParty : gEnemyParty;
    relic = GetMonRelic(&party[gBattlerPartyIndexes[battler]]);
    if (relic == RELIC_NONE)
        return;
    frame = gMonSpritesGfxPtr->spritesGfx[GetBattlerPosition(battler)];
    spriteId = Relic_CreateOverlay(relic, gBattlerSpriteIds[battler], frame, IsOnPlayerSide(battler),
                                   gSprites[gBattlerSpriteIds[battler]].subpriority);
    if (spriteId != SPRITE_NONE)
    {
        gSprites[spriteId].sBattler = battler;
        sBattlerOverlay[battler] = spriteId;
        SpriteCB_Relic(&gSprites[spriteId]);
    }
}
