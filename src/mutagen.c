#include "global.h"
#include "mutagen.h"
#include "event_data.h"
#include "event_object_lock.h"
#include "field_player_avatar.h"
#include "field_screen_effect.h"
#include "field_weather.h"
#include "fieldmap.h"
#include "overworld.h"
#include "palette.h"
#include "party_menu.h"
#include "pokemon.h"
#include "script.h"
#include "string_util.h"
#include "task.h"
#include "species_picker.h"
#include "coins.h"
#include "item.h"
#include "load_save.h"
#include "malloc.h"
#include "money.h"
#include "pokemon_storage_system.h"
#include "constants/pokedex.h"
#include "constants/battle_ai.h"
#include "constants/flags.h"
#include "constants/vars.h"
#include "constants/region_map_sections.h"
#include "constants/abilities.h"

// POKÉRUS odds (QW-20). Index 0 is Heart & Soul's and the main games' 3/65536.
u32 GetPokerusInfectionOdds(void)
{
    static const u16 sOdds[] = {3, 64, 512, 4096};

    if (gSaveBlock3Ptr == NULL)
        return sOdds[0];
    return sOdds[gSaveBlock3Ptr->mutagenSettings.pokerusOdds];
}

bool32 ShouldAnnouncePokerus(void)
{
    return gSaveBlock3Ptr != NULL && gSaveBlock3Ptr->mutagenSettings.pokerusOdds != 0;
}

// TRAINER AI (QW-31). OFF keeps each trainer's own flags from trainers_hns.party; SMART adds the
// boss set every Emerald Imperium boss carries; EXPERT adds switch and move prediction.
u64 GetMutagenTrainerAiFlags(void)
{
    if (gSaveBlock3Ptr == NULL)
        return 0;
    switch (gSaveBlock3Ptr->mutagenSettings.trainerAi)
    {
    case 1:
        return AI_FLAG_SMART_TRAINER;
    case 2:
        return AI_FLAG_SMART_TRAINER | AI_FLAG_PREDICTION | AI_FLAG_ASSUMPTIONS;
    default:
        return 0;
    }
}

bool32 AreShinyTokensSold(void)
{
    return gSaveBlock3Ptr != NULL && gSaveBlock3Ptr->mutagenSettings.shinyTokens;
}

// DISCOVERY (QW-32), after Emerald Enhanced: one wild Pokémon in 128 is a boss (five levels up,
// perfect IVs, its hidden ability, announced), and more of the lead's abilities pull encounters of
// their type, the way Static and Magnet Pull always have.
bool32 IsDiscoveryOn(void)
{
    return gSaveBlock3Ptr != NULL && gSaveBlock3Ptr->mutagenSettings.discovery;
}

EWRAM_DATA bool8 gWildBossPending = FALSE;

// STARTER and SHINY STARTER (SG-16), read by Elm's lab script.
bool32 IsStarterPickAny(void)
{
    return gSaveBlock3Ptr != NULL && gSaveBlock3Ptr->mutagenSettings.starterPick;
}

u32 GetShinyStarterMode(void)
{
    return gSaveBlock3Ptr != NULL ? gSaveBlock3Ptr->mutagenSettings.shinyStarter : 0;
}

// callnative, right after the lab sets PLAYER_STARTER_SPECIES (VAR_TEMP_2) for the ball touched.
// With STARTER at Elm's three: VAR_RESULT 0 and nothing happens. With ANY: the species list opens,
// the script must waitstate, and on return VAR_RESULT is the chosen species or 0 for backing out.
void Mutagen_StarterPicker(struct ScriptContext *ctx)
{
    if (!IsStarterPickAny())
    {
        gSpecialVar_Result = 0;
        return;
    }
    gSpecialVar_Result = 1;
    SpeciesPicker_Open(VarGet(VAR_TEMP_2));
}

void Mutagen_StarterShinyMode(struct ScriptContext *ctx)
{
    gSpecialVar_Result = GetShinyStarterMode();
}

// VAR_RESULT (YES/NO, or 1 for ALWAYS) decides the shiny flag of the ball in VAR_STARTER_MON; the
// lab's give scripts read those flags, as they do for HnS's own preview roll.
void Mutagen_SetStarterShiny(struct ScriptContext *ctx)
{
    static const u16 sShinyStarterFlags[] = {FLAG_SHINY_STARTER_1, FLAG_SHINY_STARTER_2, FLAG_SHINY_STARTER_3};
    u32 ball = VarGet(VAR_STARTER_MON);

    if (ball >= ARRAY_COUNT(sShinyStarterFlags))
        ball = 0;
    if (gSpecialVar_Result)
        FlagSet(sShinyStarterFlags[ball]);
    else
        FlagClear(sShinyStarterFlags[ball]);
}

// MUTAGEN (SG-17). ON: the mutant strain can be caught in Johto's and Kanto's irradiated places;
// RAMPANT: anywhere. Caught at 8 × the POKÉRUS odds, it spreads like Pokérus, lasts 4 days, and
// when it ends the Pokémon awakens its hidden ability and may evolve into its Ancient or Future
// form on its next level up (IF_MUTAGEN* evolution conditions, species data).
static const u8 sMutatedMapSections[] = {
    MAPSEC_LAKE_OF_RAGE, MAPSEC_ROCKET_HIDEOUT_HNS, MAPSEC_ROCKET_HIDEOUT,
    MAPSEC_CERULEAN_CAVE, MAPSEC_POWER_PLANT, MAPSEC_BURNED_TOWER,
};

bool32 MutagenRollsHere(void)
{
    u32 mode = gSaveBlock3Ptr != NULL ? gSaveBlock3Ptr->mutagenSettings.mutagen : 0;

    if (mode == 0)
        return FALSE;
    if (mode >= 2)
        return TRUE;
    for (u32 i = 0; i < ARRAY_COUNT(sMutatedMapSections); i++)
    {
        if (gMapHeader.regionMapSectionId == sMutatedMapSections[i])
            return TRUE;
    }
    return FALSE;
}

bool32 MutagenHasRunItsCourse(struct Pokemon *mon)
{
    return GetMonData(mon, MON_DATA_IS_MUTAGEN) && GetMonData(mon, MON_DATA_POKERUS_DAYS_LEFT) == 0;
}

void MutagenOnStrainEnd(struct Pokemon *mon)
{
    u32 species = GetMonData(mon, MON_DATA_SPECIES);
    u32 abilityNum = 2;

    if (GetSpeciesAbility(species, abilityNum) != ABILITY_NONE)
        SetMonData(mon, MON_DATA_ABILITY_NUM, &abilityNum);
}

// NEW GAME+ (SG-15), after R.O.W.E.: NEW GAME on the title menu becomes NEW GAME+ once the game
// is cleared and the option is on. The new game then keeps the party and every box (as they are, or
// reset to Lv 1 with fresh movesets), the bag but its key items, the PC items, money, coins and
// the Pokédex; everything else starts over, the trainer ID included among what stays (so the
// carried Pokémon still obey).
static EWRAM_DATA u8 sNewGamePlusPending = 0; // loop number of the coming new game, 0 for a plain one
static EWRAM_DATA u8 sNewGamePlusMode = 0;    // 1 keep levels, 2 reset to Lv 1

struct NewGamePlusCarry
{
    u32 money;
    u16 coins;
    u16 bagCount;
    u16 pcCount;
    struct Pokedex pokedex;
    u8 dexSeen[NUM_DEX_FLAG_BYTES];
    u8 dexCaught[NUM_DEX_FLAG_BYTES];
    struct ItemSlot pc[PC_ITEMS_COUNT];
    struct ItemSlot bag[]; // every non-key-item slot in use
};

bool32 IsNewGamePlusOffered(void)
{
    return gSaveBlock3Ptr != NULL && gSaveBlock3Ptr->mutagenSettings.newGamePlus != 0 && FlagGet(FLAG_SYS_GAME_CLEAR);
}

void NewGamePlus_ChooseAtTitle(void)
{
    if (IsNewGamePlusOffered())
    {
        sNewGamePlusPending = gSaveBlock3Ptr->mutagenSettings.newGamePlusCount + 1;
        sNewGamePlusMode = gSaveBlock3Ptr->mutagenSettings.newGamePlus;
    }
    else
    {
        sNewGamePlusPending = 0;
        sNewGamePlusMode = 0;
    }
}

bool32 NewGamePlus_IsPending(void)
{
    return sNewGamePlusPending != 0;
}

void *NewGamePlus_Snapshot(void)
{
    struct NewGamePlusCarry *carry;
    struct BagPocket pcPocket = {.itemSlots = gSaveBlock1Ptr->pcItems, .capacity = PC_ITEMS_COUNT, .id = POCKET_DUMMY};
    u32 slots = 0, n = 0;

    for (u32 p = 0; p < POCKETS_COUNT; p++)
        if (p != POCKET_KEY_ITEMS)
            slots += gBagPockets[p].capacity;
    carry = AllocZeroed(sizeof(*carry) + slots * sizeof(struct ItemSlot));
    if (carry == NULL)
        return NULL;
    // From the title screen the party is only in the save block (a continued game copies it out
    // on its way in); pull it into the working party now, before the save block is cleared.
    LoadPlayerParty();
    carry->money = GetMoney(&gSaveBlock1Ptr->money);
    carry->coins = GetCoins();
    carry->pokedex = gSaveBlock2Ptr->pokedex;
    memcpy(carry->dexSeen, gSaveBlock1Ptr->dexSeen, sizeof(carry->dexSeen));
    memcpy(carry->dexCaught, gSaveBlock1Ptr->dexCaught, sizeof(carry->dexCaught));
    for (u32 p = 0; p < POCKETS_COUNT; p++)
    {
        if (p == POCKET_KEY_ITEMS)
            continue;
        for (u32 i = 0; i < gBagPockets[p].capacity; i++)
        {
            struct ItemSlot slot = BagPocket_GetSlotData(&gBagPockets[p], i);

            if (slot.itemId != ITEM_NONE && slot.quantity != 0)
                carry->bag[n++] = slot;
        }
    }
    carry->bagCount = n;
    n = 0;
    for (u32 i = 0; i < PC_ITEMS_COUNT; i++)
    {
        struct ItemSlot slot = BagPocket_GetSlotData(&pcPocket, i);

        if (slot.itemId != ITEM_NONE && slot.quantity != 0)
            carry->pc[n++] = slot;
    }
    carry->pcCount = n;
    return carry;
}

void NewGamePlus_RestoreDex(const void *carryPtr)
{
    const struct NewGamePlusCarry *carry = carryPtr;

    if (carry == NULL)
        return;
    gSaveBlock2Ptr->pokedex = carry->pokedex;
    memcpy(gSaveBlock1Ptr->dexSeen, carry->dexSeen, sizeof(carry->dexSeen));
    memcpy(gSaveBlock1Ptr->dexCaught, carry->dexCaught, sizeof(carry->dexCaught));
}

void NewGamePlus_RestoreItemsAndMoney(const void *carryPtr)
{
    const struct NewGamePlusCarry *carry = carryPtr;

    if (carry == NULL)
        return;
    SetMoney(&gSaveBlock1Ptr->money, carry->money);
    SetCoins(carry->coins);
    for (u32 i = 0; i < carry->bagCount; i++)
        AddBagItem(carry->bag[i].itemId, carry->bag[i].quantity);
    for (u32 i = 0; i < carry->pcCount; i++)
        AddPCItem(carry->pc[i].itemId, carry->pc[i].quantity);
}

static void ResetBoxMonToLevelOne(struct BoxPokemon *boxMon)
{
    u32 species = GetBoxMonData(boxMon, MON_DATA_SPECIES);
    u32 exp, none = MOVE_NONE, zero = 0;

    if (species == SPECIES_NONE || GetBoxMonData(boxMon, MON_DATA_IS_EGG))
        return;
    exp = gExperienceTables[gSpeciesInfo[species].growthRate][1];
    SetBoxMonData(boxMon, MON_DATA_EXP, &exp);
    for (u32 i = 0; i < MAX_MON_MOVES; i++)
    {
        SetBoxMonData(boxMon, MON_DATA_MOVE1 + i, &none);
        SetBoxMonData(boxMon, MON_DATA_PP1 + i, &zero);
    }
    GiveBoxMonInitialMoveset(boxMon);
}

// Every wild and trainer Pokémon is one level higher per New Game+ loop (R.O.W.E.'s ramp).
u32 ApplyNewGamePlusRamp(u32 level)
{
    u32 loop = gSaveBlock3Ptr != NULL ? gSaveBlock3Ptr->mutagenSettings.newGamePlusCount : 0;

    if (loop == 0 || level == 0)
        return level;
    level += loop;
    return level > MAX_LEVEL ? MAX_LEVEL : level;
}

void NewGamePlus_Finish(void *carry)
{
    if (sNewGamePlusMode == 2)
    {
        for (u32 i = 0; i < PARTY_SIZE; i++)
        {
            if (GetMonData(&gPlayerParty[i], MON_DATA_SPECIES) == SPECIES_NONE)
                continue;
            ResetBoxMonToLevelOne(&gPlayerParty[i].box);
            CalculateMonStats(&gPlayerParty[i]);
        }
        for (u32 box = 0; box < TOTAL_BOXES_COUNT; box++)
            for (u32 i = 0; i < IN_BOX_COUNT; i++)
                ResetBoxMonToLevelOne(&gPokemonStoragePtr->boxes[box][i]);
    }
    gSaveBlock3Ptr->mutagenSettings.newGamePlusCount = sNewGamePlusPending;
    if (carry != NULL)
        Free(carry);
    sNewGamePlusPending = 0;
    sNewGamePlusMode = 0;
}

// The post-battle "caught Pokérus" notice. pokerus.c sets gPokerusNoticeSlot when a wild battle
// infects a party member and the option is above RARE; CB2_EndWildBattle then returns to the field
// through this callback, which runs the notice script once the fade-in is done.
EWRAM_DATA u8 gPokerusNoticeSlot = 0;
EWRAM_DATA bool8 gPokerusNoticeMutant = FALSE;

extern const u8 Mutagen_EventScript_PokerusNotice[];
extern const u8 Mutagen_EventScript_MutagenNotice[];

static void Task_ReturnToFieldPokerusNotice(u8 taskId)
{
    if (IsWeatherNotFadingIn() == TRUE)
    {
        DestroyTask(taskId);
        ScriptUnfreezeObjectEvents();
        UnlockPlayerFieldControls();
        ScriptContext_SetupScript(gPokerusNoticeMutant ? Mutagen_EventScript_MutagenNotice : Mutagen_EventScript_PokerusNotice);
    }
}

void FieldCB_ReturnToFieldPokerusNotice(void)
{
    LockPlayerFieldControls();
    Overworld_PlaySpecialMapMusic();
    FadeInFromBlack();
    CreateTask(Task_ReturnToFieldPokerusNotice, 10);
}

void Mutagen_BufferPokerusNoticeMon(struct ScriptContext *ctx)
{
    u32 slot = gPokerusNoticeSlot ? gPokerusNoticeSlot - 1 : 0;

    gPokerusNoticeSlot = 0;
    gPokerusNoticeMutant = FALSE;
    GetMonNickname(&gPlayerParty[slot], gStringVar1);
}
