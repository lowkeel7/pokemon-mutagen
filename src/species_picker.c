#include "global.h"
#include "event_data.h"
#include "list_menu.h"
#include "main.h"
#include "malloc.h"
#include "menu.h"
#include "pokemon.h"
#include "script.h"
#include "script_menu.h"
#include "sound.h"
#include "string_util.h"
#include "task.h"
#include "text.h"
#include "window.h"
#include "battle_main.h"
#include "constants/pokedex.h"
#include "constants/songs.h"
#include "species_picker.h"

// Layout, in tiles. The picture box (script_menu.c) draws at tilemap (x + 1, y + 1) with tiles
// from block 100, so our windows take blocks above it.
#define LIST_ROWS 8
#define PIC_X 19
#define PIC_Y 1
#define PAGE_STEP 50

enum { PIC_NONE, PIC_SHOWN, PIC_HIDING };

struct SpeciesPicker
{
    struct ListMenuTemplate template;
    struct ListMenuItem *items;
    u16 count;
    u16 curSpecies;
    u16 picSpecies;
    u16 result;
    u8 windowId;
    u8 infoWindowId;
    u8 listTaskId;
    u8 picState;
    u8 rest;
    bool8 closing;
    bool8 (*hideWait)(void);
};

static EWRAM_DATA struct SpeciesPicker *sPicker = NULL;

static const struct WindowTemplate sListWindow = {
    .bg = 0, .tilemapLeft = 1, .tilemapTop = 1, .width = 14, .height = 2 * LIST_ROWS, .paletteNum = 15, .baseBlock = 170,
};
static const struct WindowTemplate sInfoWindow = {
    .bg = 0, .tilemapLeft = PIC_X + 1, .tilemapTop = 11, .width = 8, .height = 4, .paletteNum = 15, .baseBlock = 170 + 14 * 2 * LIST_ROWS,
};

static const u8 sText_No[] = _("No.");
static const u8 sText_Slash[] = _("/");

static void Task_SpeciesPicker(u8 taskId);

static void BuildList(u16 initialSpecies, u16 *initialIndex)
{
    u32 n = 0;

    *initialIndex = 0;
    for (u32 nat = 1; nat <= NATIONAL_DEX_COUNT; nat++)
    {
        u16 species = NationalPokedexNumToSpecies(nat);

        if (species == SPECIES_NONE || !IsSpeciesEnabled(species))
            continue;
        if (species == initialSpecies)
            *initialIndex = n;
        sPicker->items[n].name = GetSpeciesName(species);
        sPicker->items[n].id = species;
        n++;
    }
    sPicker->count = n;
}

static void DrawInfo(u16 species)
{
    u8 text[32];
    enum Type type1 = GetSpeciesType(species, 0);
    enum Type type2 = GetSpeciesType(species, 1);

    FillWindowPixelBuffer(sPicker->infoWindowId, PIXEL_FILL(1));
    StringCopy(text, sText_No);
    ConvertIntToDecimalStringN(text + 3, SpeciesToNationalPokedexNum(species), STR_CONV_MODE_LEADING_ZEROS, 4);
    AddTextPrinterParameterized(sPicker->infoWindowId, FONT_SMALL, text, 2, 1, TEXT_SKIP_DRAW, NULL);
    StringCopy(text, gTypesInfo[type1].name);
    if (type2 != type1)
    {
        StringAppend(text, sText_Slash);
        StringAppend(text, gTypesInfo[type2].name);
    }
    AddTextPrinterParameterized(sPicker->infoWindowId, FONT_SMALL, text, 2, 15, TEXT_SKIP_DRAW, NULL);
    CopyWindowToVram(sPicker->infoWindowId, COPYWIN_GFX);
}

static void InitList(u16 scroll, u16 row)
{
    sPicker->listTaskId = ListMenuInit(&sPicker->template, scroll, row);
    CopyWindowToVram(sPicker->windowId, COPYWIN_GFX);
}

static void Page(s32 delta)
{
    u16 scroll, row;
    s32 pos, newScroll;

    DestroyListMenuTask(sPicker->listTaskId, &scroll, &row);
    pos = scroll + row + delta;
    if (pos < 0)
        pos = 0;
    if (pos > sPicker->count - 1)
        pos = sPicker->count - 1;
    newScroll = pos - row;
    if (newScroll > (s32)sPicker->count - LIST_ROWS)
        newScroll = sPicker->count - LIST_ROWS;
    if (newScroll < 0)
        newScroll = 0;
    InitList(newScroll, pos - newScroll);
}

void SpeciesPicker_Open(u16 initialSpecies)
{
    u16 index, scroll, row;

    sPicker = AllocZeroed(sizeof(*sPicker));
    sPicker->items = AllocZeroed(sizeof(struct ListMenuItem) * (NATIONAL_DEX_COUNT + 1));
    BuildList(initialSpecies, &index);

    LoadMessageBoxAndBorderGfx();
    sPicker->windowId = AddWindow(&sListWindow);
    DrawStdWindowFrame(sPicker->windowId, FALSE);
    sPicker->infoWindowId = AddWindow(&sInfoWindow);
    DrawStdWindowFrame(sPicker->infoWindowId, FALSE);

    sPicker->template.items = sPicker->items;
    sPicker->template.moveCursorFunc = ListMenuDefaultCursorMoveFunc;
    sPicker->template.totalItems = sPicker->count;
    sPicker->template.maxShowed = LIST_ROWS;
    sPicker->template.windowId = sPicker->windowId;
    sPicker->template.header_X = 0;
    sPicker->template.item_X = 8;
    sPicker->template.cursor_X = 0;
    sPicker->template.upText_Y = 1;
    sPicker->template.cursorPal = 2;
    sPicker->template.fillValue = 1;
    sPicker->template.cursorShadowPal = 3;
    sPicker->template.lettersSpacing = 0;
    sPicker->template.itemVerticalPadding = 0;
    sPicker->template.scrollMultiple = LIST_NO_MULTIPLE_SCROLL;
    sPicker->template.fontId = FONT_NORMAL;
    sPicker->template.cursorKind = 0;

    scroll = index > LIST_ROWS / 2 ? index - LIST_ROWS / 2 : 0;
    if (scroll > sPicker->count - LIST_ROWS)
        scroll = sPicker->count - LIST_ROWS;
    row = index - scroll;
    InitList(scroll, row);
    CopyWindowToVram(sPicker->windowId, COPYWIN_FULL);
    CopyWindowToVram(sPicker->infoWindowId, COPYWIN_FULL);
    sPicker->picState = PIC_NONE;
    sPicker->curSpecies = SPECIES_NONE;
    CreateTask(Task_SpeciesPicker, 3);
}

static void BeginClose(u16 result)
{
    sPicker->result = result;
    sPicker->closing = TRUE;
    if (sPicker->picState == PIC_SHOWN)
    {
        sPicker->hideWait = ScriptMenu_HidePokemonPic();
        sPicker->picState = sPicker->hideWait != NULL ? PIC_HIDING : PIC_NONE;
    }
}

static void Close(u8 taskId)
{
    u16 result = sPicker->result;

    DestroyListMenuTask(sPicker->listTaskId, NULL, NULL);
    ClearStdWindowAndFrame(sPicker->windowId, TRUE);
    RemoveWindow(sPicker->windowId);
    ClearStdWindowAndFrame(sPicker->infoWindowId, TRUE);
    RemoveWindow(sPicker->infoWindowId);
    Free(sPicker->items);
    Free(sPicker);
    sPicker = NULL;
    DestroyTask(taskId);
    gSpecialVar_Result = result;
    ScriptContext_Enable();
}

static void Task_SpeciesPicker(u8 taskId)
{
    struct SpeciesPicker *p = sPicker;
    u16 scroll, row, cur;
    s32 input;

    if (p->closing)
    {
        if (p->picState == PIC_HIDING)
        {
            if (!p->hideWait())
                return;
            p->picState = PIC_NONE;
        }
        Close(taskId);
        return;
    }

    ListMenuGetScrollAndRow(p->listTaskId, &scroll, &row);
    cur = p->items[scroll + row].id;
    if (cur != p->curSpecies)
    {
        p->curSpecies = cur;
        p->rest = 0;
        DrawInfo(cur);
    }
    else if (p->rest < 60)
    {
        p->rest++;
    }

    // The picture box follows the cursor once it rests; one box at a time, hidden before the next.
    switch (p->picState)
    {
    case PIC_SHOWN:
        if (p->picSpecies != p->curSpecies)
        {
            p->hideWait = ScriptMenu_HidePokemonPic();
            p->picState = p->hideWait != NULL ? PIC_HIDING : PIC_NONE;
        }
        break;
    case PIC_HIDING:
        if (p->hideWait())
            p->picState = PIC_NONE;
        break;
    default:
        if (p->rest >= 4 && ScriptMenu_ShowPokemonPic(p->curSpecies, PIC_X, PIC_Y))
        {
            p->picSpecies = p->curSpecies;
            p->picState = PIC_SHOWN;
        }
        break;
    }

    if (JOY_NEW(R_BUTTON))
    {
        PlaySE(SE_SELECT);
        Page(PAGE_STEP);
        return;
    }
    if (JOY_NEW(L_BUTTON))
    {
        PlaySE(SE_SELECT);
        Page(-PAGE_STEP);
        return;
    }

    input = ListMenu_ProcessInput(p->listTaskId);
    if (input == LIST_CANCEL)
    {
        PlaySE(SE_SELECT);
        BeginClose(0);
    }
    else if (input != LIST_NOTHING_CHOSEN)
    {
        PlaySE(SE_SELECT);
        BeginClose(input);
    }
}
