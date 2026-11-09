// Pokémon Mutagen (SG-09): species parts a Pokémon wears. docs/pokerom/design/items.md.
//
// A part is one index per Pokémon (PokemonSubstruct0.relic, 6 bits). Put on from the bag
// (party_menu.c, ItemUseCB_Relic), it grants its ability whatever the species (pokemon.c,
// GetMonAbility) and is drawn over the Pokémon's sprite in battle and in the summary: a 32x32 cell
// that follows the Pokémon's sprite, placed by the shape of its first frame. MUTAGEN → RELICS
// (zero = Heart & Soul) gates every effect; the field itself is kept either way.
//
// Cost: twelve bytes of ROM a part plus its compressed art (about half a kilobyte); no palette of
// its own, the donor species' palette colours it. Two bytes of EWRAM a battler. One sprite, one
// 512-byte tile block and one palette slot per part on screen; the part's other view stays in ROM.
// Placing a part reads the wearer's frame once, two pixels a step, skipping blank bytes.
#include "global.h"
#include "battle.h"
#include "battle_anim.h"
#include "battle_util.h"
#include "decompress.h"
#include "graphics.h"
#include "malloc.h"
#include "mutagen.h"
#include "pokemon.h"
#include "relic.h"
#include "sprite.h"
#include "constants/abilities.h"
#include "constants/items.h"

#include "data/relics.h"

STATIC_ASSERT(RELICS_COUNT <= 64, RelicIndexMustFitSixBits);

#define TAG_RELIC_GFX 0x5E1C   // plus twice the part's index, plus one for the back view: one tile block per view on screen
#define TAG_RELIC_PAL 0x5E1C   // plus the part's index: one palette per kind of part on screen
#define RELIC_CELL 32          // the overlay cell, in pixels
#define RELIC_CELL_SIZE (RELIC_CELL * RELIC_CELL / 2)   // 512 bytes of 4bpp tiles a view
#define RELIC_SHEET_SIZE (2 * RELIC_CELL_SIZE)          // both views, decompressed
#define RELIC_SINK 6           // HEAD: the cell's bottom sits this far below the head line, so the part sits on the head
#define RELIC_FACE_DROP 10     // FACE: the cell's centre sits this far below the head line
#define RELIC_BACK_DROP_FRONT 4    // BACK, facing us: the cell's centre a little under the head line, so the part rises over the shoulders behind the body
#define RELIC_BACK_DROP_BACK 14    // BACK, facing away: the cell's centre on the back itself

// sprite->data
#define sBattler   data[0]     // MAX_BATTLERS_COUNT outside a battle (the summary screen)
#define sMonSprite data[1]
#define sOffsetX   data[2]
#define sOffsetY   data[3]
#define sBehind    data[4]     // drawn behind the wearer's sprite

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

u32 RelicOfDonor(u16 species)
{
    u32 i;

    if (species == SPECIES_NONE)
        return RELIC_NONE;
    for (i = RELIC_NONE + 1; i < RELICS_COUNT; i++)
    {
        if (gRelicsInfo[i].donor == species)
            return i;
    }
    return RELIC_NONE;
}

enum Ability GetRelicAbility(u32 relic)
{
    return relic < RELICS_COUNT ? gRelicsInfo[relic].ability : ABILITY_NONE;
}

u32 GetRelicType(u32 relic)
{
    if (relic == RELIC_NONE || relic >= RELICS_COUNT || gRelicsInfo[relic].donor == SPECIES_NONE)
        return TYPE_NONE;
    return gSpeciesInfo[gRelicsInfo[relic].donor].types[0];
}

// Read while worn, never written: the part's type shows as the wearer's third type (MUTAGEN →
// THIRD TYPE on) unless the player chose to keep the Pokémon's own third type under it, which is
// the one bit the choice costs. Take the part off and the own type is back, untouched.
u32 GetMonRelicType(struct Pokemon *mon)
{
    u32 relic = GetMonRelic(mon);

    if (relic == RELIC_NONE || !IsThirdTypeOn() || GetMonData(mon, MON_DATA_RELIC_TYPE_OFF))
        return TYPE_NONE;
    return GetRelicType(relic);
}

// One read of the Pokémon: an egg's field is zero (the bag refuses to dress one), so no egg check.
u32 GetMonRelic(struct Pokemon *mon)
{
    u32 relic;

    if (!AreRelicsOn() || mon == NULL)
        return RELIC_NONE;
    relic = GetMonData(mon, MON_DATA_RELIC);
    return relic < RELICS_COUNT ? relic : RELIC_NONE;
}

// Where the part sits on this frame, as the cell's bottom centre. One pass over the 64x64 4bpp
// frame, a byte (two pixels) a step, blank bytes (most of a sprite's edge) costing one test: the
// drawn width of every row and the sprite's bounds. The head line is the first row from the top
// whose drawn width is a fair share (7/20, at least 6 px) of the sprite's, so ears, horns and
// antennae are passed over. FALSE for a blank frame.
static bool32 FindAnchor(const u8 *frame, u32 anchor, bool32 back, s32 *outX, s32 *outY)
{
    u8 count[MON_PIC_HEIGHT], first[MON_PIC_HEIGHT], last[MON_PIC_HEIGHT];
    s32 x, y, minX = MON_PIC_WIDTH, maxX = -1, top = -1, bottom = -1, threshold;
    u32 tx, ty, py, bx;

    for (y = 0; y < MON_PIC_HEIGHT; y++)
        count[y] = 0;
    for (ty = 0; ty < MON_PIC_HEIGHT / 8; ty++)
    {
        for (tx = 0; tx < MON_PIC_WIDTH / 8; tx++)
        {
            const u8 *tile = frame + (ty * (MON_PIC_WIDTH / 8) + tx) * TILE_SIZE_4BPP;

            for (py = 0; py < 8; py++)
            {
                const u8 *row = tile + py * 4;

                y = ty * 8 + py;
                for (bx = 0; bx < 4; bx++)
                {
                    u32 pair = row[bx];

                    if (pair == 0)
                        continue;
                    x = tx * 8 + bx * 2;
                    if (!(pair & 0x0F))
                        x++;
                    if (count[y] == 0)
                        first[y] = x;
                    count[y] += ((pair & 0x0F) != 0) + ((pair & 0xF0) != 0);
                    if (pair & 0xF0)
                        x = tx * 8 + bx * 2 + 1;
                    last[y] = x;
                    if (first[y] < minX)
                        minX = first[y];
                    if (x > maxX)
                        maxX = x;
                    if (top < 0 || y < top)
                        top = y;
                    if (y > bottom)
                        bottom = y;
                }
            }
        }
    }
    if (maxX < 0)
        return FALSE;
    threshold = (maxX - minX + 1) * 7 / 20;
    if (threshold < 6)
        threshold = 6;
    for (y = top; y <= bottom; y++)
    {
        if (count[y] >= threshold)
            break;
    }
    if (y > bottom)
        y = top;
    *outX = (first[y] + last[y]) / 2;
    switch (anchor)
    {
    case RELIC_ANCHOR_FACE:
        *outY = y + RELIC_FACE_DROP + RELIC_CELL / 2;
        break;
    case RELIC_ANCHOR_BACK:
        *outY = y + (back ? RELIC_BACK_DROP_BACK : RELIC_BACK_DROP_FRONT) + RELIC_CELL / 2;
        break;
    case RELIC_ANCHOR_BODY:
        *outX = (minX + maxX) / 2;
        *outY = (top + bottom) / 2 + RELIC_CELL / 2;
        break;
    default: // RELIC_ANCHOR_HEAD
        *outY = y + RELIC_SINK;
        break;
    }
    return TRUE;
}

// The view's 512 bytes of tiles into VRAM, once per part and view on screen: the sheet is
// decompressed into a scratch buffer only when its tiles are not loaded yet.
static bool32 LoadRelicView(u32 relic, bool32 back, u16 tag)
{
    struct SpriteSheet sheet = { .size = RELIC_CELL_SIZE, .tag = tag };
    void *buffer;
    bool32 ok;

    if (GetSpriteTileStartByTag(tag) != 0xFFFF)
        return TRUE;
    buffer = Alloc(RELIC_SHEET_SIZE);
    if (buffer == NULL)
        return FALSE;
    DecompressDataWithHeaderWram(gRelicsInfo[relic].gfx, buffer);
    sheet.data = (const u8 *)buffer + (back ? RELIC_CELL_SIZE : 0);
    ok = LoadSpriteSheet(&sheet) != 0xFFFF;
    Free(buffer);
    return ok;
}

u8 Relic_CreateOverlay(u32 relic, u8 monSpriteId, const u8 *frame, bool32 back, u8 subpriority)
{
    struct SpriteTemplate template = sSpriteTemplate_Relic;
    struct SpritePalette palette;
    struct Sprite *sprite;
    s32 anchorX, anchorY;
    u8 spriteId;
    bool32 behind;

    if (relic == RELIC_NONE || relic >= RELICS_COUNT || gRelicsInfo[relic].gfx == NULL
     || monSpriteId >= MAX_SPRITES || frame == NULL || !FindAnchor(frame, gRelicsInfo[relic].anchor, back, &anchorX, &anchorY))
        return SPRITE_NONE;

    template.tileTag = TAG_RELIC_GFX + relic * 2 + (back ? 1 : 0);
    template.paletteTag = TAG_RELIC_PAL + relic;
    if (!LoadRelicView(relic, back, template.tileTag))
        return SPRITE_NONE;
    palette = (struct SpritePalette){ .data = gSpeciesInfo[gRelicsInfo[relic].donor].palette, .tag = template.paletteTag };
    if (IndexOfSpritePaletteTag(palette.tag) == 0xFF && LoadSpritePalette(&palette) == 0xFF)
        return SPRITE_NONE;

    // A part on the back is behind the Pokémon when we face it, in front when it faces away from us.
    behind = (gRelicsInfo[relic].anchor == RELIC_ANCHOR_BACK && !back);
    spriteId = CreateSprite(&template, 0, 0, behind ? subpriority + 1 : (subpriority > 0 ? subpriority - 1 : 0));
    if (spriteId == MAX_SPRITES)
        return SPRITE_NONE;
    sprite = &gSprites[spriteId];
    sprite->sBattler = MAX_BATTLERS_COUNT;
    sprite->sMonSprite = monSpriteId;
    sprite->sOffsetX = anchorX - MON_PIC_WIDTH / 2;
    sprite->sOffsetY = anchorY + gRelicsInfo[relic].dy - MON_PIC_HEIGHT / 2 - RELIC_CELL / 2;
    sprite->sBehind = behind;
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
    if (sprite->sBehind)
        sprite->subpriority = mon->subpriority + 1;
    else
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
