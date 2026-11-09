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
#include "constants/characters.h"
#include "text.h"
#include "battle_main.h"
#include "species_picker.h"
#include "coins.h"
#include "item.h"
#include "pokedex.h"
#include "config/overworld.h"
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

// CHEATS tab (QW-16). The toggles that are read at their sites:
bool32 CheatShelfOn(void)
{
    return gSaveBlock3Ptr != NULL && gSaveBlock3Ptr->mutagenSettings.cheatShelf;
}

// CHEAT SHELF → ALL (QW-07): every Poké Mart sells every item in the game but the key items.
bool32 CheatShopEverything(void)
{
    return gSaveBlock3Ptr != NULL && gSaveBlock3Ptr->mutagenSettings.shopEverything;
}

bool32 CheatInfinitePp(void)
{
    return gSaveBlock3Ptr != NULL && gSaveBlock3Ptr->mutagenSettings.infinitePp;
}

bool32 CheatCatchAlways(void)
{
    return gSaveBlock3Ptr != NULL && gSaveBlock3Ptr->mutagenSettings.catchAlways;
}

// ... and the ones that are state: the engine's own flags, the Box Link key item and the Pokédex.
// Called when the options are saved and at the end of a new game's set-up (the flags live in
// SaveBlock1, which a new game clears).
void Mutagen_ApplyCheats(void)
{
    struct MutagenSettings *ms = &gSaveBlock3Ptr->mutagenSettings;

    if (ms->walkThroughWalls)
        FlagSet(OW_FLAG_NO_COLLISION);
    else
        FlagClear(OW_FLAG_NO_COLLISION);
    if (ms->noWildBattles)
        FlagSet(OW_FLAG_NO_ENCOUNTER);
    else
        FlagClear(OW_FLAG_NO_ENCOUNTER);
    if (ms->trainersDontSee)
        FlagSet(OW_FLAG_NO_TRAINER_SEE);
    else
        FlagClear(OW_FLAG_NO_TRAINER_SEE);
    if (ms->mobilePc)
    {
        if (!CheckBagHasItem(ITEM_POKEMON_BOX_LINK, 1))
            AddBagItem(ITEM_POKEMON_BOX_LINK, 1);
    }
    else if (CheckBagHasItem(ITEM_POKEMON_BOX_LINK, 1))
    {
        RemoveBagItem(ITEM_POKEMON_BOX_LINK, 1);
    }
    if (ms->dexComplete)
    {
        for (u32 nat = 1; nat <= NATIONAL_DEX_COUNT; nat++)
        {
            GetSetPokedexFlag(nat, FLAG_SET_SEEN);
            GetSetPokedexFlag(nat, FLAG_SET_CAUGHT);
        }
        EnableNationalPokedex();
        FlagSet(FLAG_SYS_POKEDEX_GET);
    }
}

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
    u32 abilityNum = 2, zero = 0;

    if (GetSpeciesAbility(species, abilityNum) != ABILITY_NONE)
        SetMonData(mon, MON_DATA_ABILITY_NUM, &abilityNum);
    SetMonData(mon, MON_DATA_THIRD_TYPE_PENDING, &zero); // the graft sets (SG-01)
    // Told after the next wild battle, unless another notice is already waiting.
    if (gPokerusNoticeSlot == 0 && mon >= gPlayerParty && mon < gPlayerParty + PARTY_SIZE)
    {
        gPokerusNoticeSlot = (mon - gPlayerParty) + 1;
        gPokerusNoticeKind = 3;
    }
}

// THIRD TYPE (SG-01): the Mutagen grafts the first type of the Pokémon that passed the strain on;
// it counts once the strain has run its course, and only while the option is on.
bool32 IsThirdTypeOn(void)
{
    return gSaveBlock3Ptr != NULL && gSaveBlock3Ptr->mutagenSettings.thirdType;
}

u32 GetMonThirdType(struct Pokemon *mon)
{
    u32 third;

    if (!IsThirdTypeOn() || GetMonData(mon, MON_DATA_THIRD_TYPE_PENDING))
        return TYPE_NONE;
    third = GetMonData(mon, MON_DATA_THIRD_TYPE);
    if (third >= NUMBER_OF_MON_TYPES || third == TYPE_MYSTERY || third == TYPE_STELLAR)
        return TYPE_NONE;
    return third;
}

// NEW GAME+ (SG-15), after R.O.W.E.: NEW GAME on the title menu becomes NEW GAME+ once the game
// is cleared and the option is on. The new game then keeps the party and every box (as they are, or
// reset to Lv 1 with fresh movesets), the whole bag, key items included, the PC items, money, coins and
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
    // Every pocket, key items included (the owner's call: a story script that hands over a key
    // item you already hold is the thing to watch for).
    for (u32 p = 0; p < POCKETS_COUNT; p++)
    {
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
    // The system flags the story would set on the way: with a team and a Pokédex in hand, the
    // START menu shows POKéMON and POKéDEX from the first step (the story reset cleared them).
    if (gPlayerPartyCount > 0)
        FlagSet(FLAG_SYS_POKEMON_GET);
    for (u32 i = 0; i < NUM_DEX_FLAG_BYTES; i++)
    {
        if (gSaveBlock1Ptr->dexSeen[i] != 0)
        {
            FlagSet(FLAG_SYS_POKEDEX_GET);
            break;
        }
    }
    if (gSaveBlock2Ptr->pokedex.nationalMagic == 0xDA)
        FlagSet(FLAG_SYS_NATIONAL_DEX);
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
EWRAM_DATA u8 gPokerusNoticeKind = 0;

extern const u8 Mutagen_EventScript_PokerusNotice[];
extern const u8 Mutagen_EventScript_MutagenNotice[];
extern const u8 Mutagen_EventScript_MutagenEnded[];

static void Task_ReturnToFieldPokerusNotice(u8 taskId)
{
    if (IsWeatherNotFadingIn() == TRUE)
    {
        DestroyTask(taskId);
        ScriptUnfreezeObjectEvents();
        UnlockPlayerFieldControls();
        if (gPokerusNoticeKind == 3)
            ScriptContext_SetupScript(Mutagen_EventScript_MutagenEnded);
        else if (gPokerusNoticeKind == 2)
            ScriptContext_SetupScript(Mutagen_EventScript_MutagenNotice);
        else
            ScriptContext_SetupScript(Mutagen_EventScript_PokerusNotice);
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

    static const u8 sText_AbilityAwakened[] = _("\pIts hidden ability awakened.");
    static const u8 sText_TookOnType[] = _("\pIt took on the ");
    static const u8 sText_TypeSuffix[] = _(" type!");
    struct Pokemon *mon = &gPlayerParty[slot];
    u32 species = GetMonData(mon, MON_DATA_SPECIES);
    u32 third = GetMonThirdType(mon);

    gPokerusNoticeSlot = 0;
    gPokerusNoticeKind = 0;
    GetMonNickname(mon, gStringVar1);
    // The strain-end notice: what the mutation gave (STR_VAR_2).
    gStringVar2[0] = EOS;
    if (GetSpeciesAbility(species, 2) != ABILITY_NONE)
        StringAppend(gStringVar2, sText_AbilityAwakened);
    if (third != TYPE_NONE)
    {
        StringAppend(gStringVar2, sText_TookOnType);
        StringAppend(gStringVar2, gTypesInfo[third].name);
        StringAppend(gStringVar2, sText_TypeSuffix);
    }
}
