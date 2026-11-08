#include "global.h"
#include "new_game.h"
#include "random.h"
#include "config/randomizer.h"
#include "pokemon.h"
#include "roamer.h"
#include "pokemon_size_record.h"
#include "script.h"
#include "lottery_corner.h"
#include "play_time.h"
#include "mauville_old_man.h"
#include "match_call.h"
#include "lilycove_lady.h"
#include "load_save.h"
#include "pokeblock.h"
#include "dewford_trend.h"
#include "berry.h"
#include "rtc.h"
#include "easy_chat.h"
#include "event_data.h"
#include "money.h"
#include "mom_savings.h"
#include "trainer_hill.h"
#include "trainer_tower.h"
#include "tv.h"
#include "coins.h"
#include "text.h"
#include "overworld.h"
#include "mail.h"
#include "battle_records.h"
#include "item.h"
#include "pokedex.h"
#include "apprentice.h"
#include "frontier_util.h"
#include "pokedex.h"
#include "save.h"
#include "link_rfu.h"
#include "main.h"
#include "contest.h"
#include "item_menu.h"
#include "pokemon_storage_system.h"
#include "pokemon_jump.h"
#include "decoration_inventory.h"
#include "secret_base.h"
#include "string_util.h"
#include "strings.h"
#include "player_pc.h"
#include "field_specials.h"
#include "berry_powder.h"
#include "mystery_gift.h"
#include "union_room_chat.h"
#include "constants/map_groups.h"
#include "constants/items.h"
#include "difficulty.h"
#include "follower_npc.h"

// 1 in sandbox dev builds (make hns SANDBOX=1): new games start with Mutagen's options on, every
// item and full PC boxes. 0 everywhere else, which compiles to the same code as before.
#ifndef MUTAGEN_SANDBOX
#define MUTAGEN_SANDBOX 0
#endif
#if MUTAGEN_SANDBOX
#include "party_menu.h"
static void Sandbox_StockNewGame(void);
#endif

extern const u8 EventScript_ResetAllMapFlags[];
#if IS_FRLG
extern const u8 EventScript_ResetAllMapFlagsFrlg[];
#endif
#if IS_HNS
extern const u8 EventScript_ResetAllMapFlagsHnS[];
#endif

static void ClearFrontierRecord(void);
static void WarpToTruck(void);
static void ResetMiniGamesRecords(void);
static void ResetItemFlags(void);
static void ResetDexNav(void);

EWRAM_DATA bool8 gDifferentSaveFile = FALSE;
EWRAM_DATA bool8 gEnableContestDebugging = FALSE;

static const struct ContestWinner sContestWinnerPicDummy =
{
    .monName = _(""),
    .trainerName = _("")
};

void SetTrainerId(u32 trainerId, u8 *dst)
{
    dst[0] = trainerId;
    dst[1] = trainerId >> 8;
    dst[2] = trainerId >> 16;
    dst[3] = trainerId >> 24;
}

u32 GetTrainerId(u8 *trainerId)
{
    return (trainerId[3] << 24) | (trainerId[2] << 16) | (trainerId[1] << 8) | (trainerId[0]);
}

void CopyTrainerId(u8 *dst, u8 *src)
{
    s32 i;
    for (i = 0; i < TRAINER_ID_LENGTH; i++)
        dst[i] = src[i];
}

static void InitPlayerTrainerId(void)
{
    u32 trainerId = (Random() << 16) | GetGeneratedTrainerIdLower();
    SetTrainerId(trainerId, gSaveBlock2Ptr->playerTrainerId);
}

// L=A isnt set here for some reason.
static void SetDefaultOptions(void)
{
    gSaveBlock2Ptr->optionsTextSpeed = OPTIONS_TEXT_SPEED_FAST;
    gSaveBlock2Ptr->optionsWindowFrameType = 0;
    gSaveBlock2Ptr->optionsSound = OPTIONS_SOUND_MONO;
    gSaveBlock2Ptr->optionsBattleStyle = OPTIONS_BATTLE_STYLE_SHIFT;
    gSaveBlock2Ptr->optionsBattleSceneOff = FALSE;
    gSaveBlock2Ptr->regionMapZoom = FALSE;
}

void SetDefaultChallengeSettings(void)
{
    gSaveblock3.challengeSettings.followerEnable = 0;
    gSaveblock3.challengeSettings.followerLargeEnable = 0;
    gSaveblock3.challengeSettings.autoRun = 1;
    gSaveblock3.challengeSettings.autorunSurf = 1;
    gSaveblock3.challengeSettings.autorunDive = 1;
    gSaveblock3.challengeSettings.fishing = 0;
    gSaveblock3.challengeSettings.evenFasterJoy = 1;
    gSaveblock3.challengeSettings.fastIntro = 1;
    gSaveblock3.challengeSettings.fastBattle = 0;
    gSaveblock3.challengeSettings.optionStyle = 0;
    gSaveblock3.challengeSettings.genOneRecharge = 0;
    gSaveblock3.challengeSettings.unitSystem = 0;
    gSaveblock3.challengeSettings.disableMatchCall = 0;
    gSaveblock3.challengeSettings.bikeMusic = 0;
    gSaveblock3.challengeSettings.surfMusic = 0;
    gSaveblock3.challengeSettings.lrToRun = 0;
    gSaveblock3.challengeSettings.ballPrompt = 0;
    gSaveblock3.challengeSettings.newBackgrounds = 1;
    gSaveblock3.challengeSettings.newBattleUI = 0;
    gSaveblock3.challengeSettings.musicOnOff = 0;
    gSaveblock3.challengeSettings.runType = 0;

    // Challenge menu — "RECOMMENDED" defaults
    gSaveblock3.challengeSettings.tx_Mode_Modern_Moves       = 1;
    gSaveblock3.challengeSettings.tx_Mode_Synchronize        = 1;
    gSaveblock3.challengeSettings.tx_Mode_Sturdy             = 1;
    gSaveblock3.challengeSettings.tx_Mode_New_Citrus         = 1;
    gSaveblock3.challengeSettings.tx_Mode_Fairy_Types        = 1;
    gSaveblock3.challengeSettings.tx_Mode_Legendary_Abilities = 1;
    gSaveblock3.challengeSettings.tx_Mode_InfiniteTMs        = 1;
    gSaveblock3.challengeSettings.tx_Mode_Mints              = 1;
    gSaveblock3.challengeSettings.tx_Mode_PoisonSurvive      = 1;

    // Randomizer defaults (shown when Randomizer is ON)
    gSaveblock3.challengeSettings.tx_Random_Similar          = 1;
    gSaveblock3.challengeSettings.tx_Random_MapBased         = 1;
    gSaveblock3.challengeSettings.tx_Random_GenScope         = RANDOMIZER_DEFAULT_GEN_SCOPE_1_3;

    // Nuzlocke clause defaults (shown when Nuzlocke is NORMAL/HARD)
    gSaveblock3.challengeSettings.tx_Nuzlocke_SpeciesClause  = 1;
    gSaveblock3.challengeSettings.tx_Nuzlocke_ShinyClause    = 1;
    gSaveblock3.challengeSettings.tx_Nuzlocke_Nicknaming     = 1;

#if MUTAGEN_SANDBOX
    // Mutagen's options start on. The new-game menu can still set SPRITES back to GBA (FEATURES
    // tab), and OPTION → BATTLE OPTIONS changes TYPE ICONS.
    gSaveblock3.challengeSettings.typeIcons               = 3; // ALL
    gSaveblock3.challengeSettings.tx_Features_SpriteStyle = 1; // DS
#endif
}

static void ClearPokedexFlags(void)
{
    gUnusedPokedexU8 = 0;
    memset(&gSaveBlock1Ptr->dexCaught, 0, sizeof(gSaveBlock1Ptr->dexCaught));
    memset(&gSaveBlock1Ptr->dexSeen, 0, sizeof(gSaveBlock1Ptr->dexSeen));
}

void ClearAllContestWinnerPics(void)
{
    s32 i;

    ClearContestWinnerPicsInContestHall();

    // Clear Museum paintings
    for (i = MUSEUM_CONTEST_WINNERS_START; i < NUM_CONTEST_WINNERS; i++)
        gSaveBlock1Ptr->contestWinners[i] = sContestWinnerPicDummy;
}

static void ClearFrontierRecord(void)
{
    CpuFill32(0, &gSaveBlock2Ptr->frontier, sizeof(gSaveBlock2Ptr->frontier));

    gSaveBlock2Ptr->frontier.opponentNames[0][0] = EOS;
    gSaveBlock2Ptr->frontier.opponentNames[1][0] = EOS;
}

static void WarpToTruck(void)
{
    if (IS_FRLG)
        SetWarpDestination(MAP_GROUP(MAP_PALLET_TOWN_PLAYERS_HOUSE_2F), MAP_NUM(MAP_PALLET_TOWN_PLAYERS_HOUSE_2F), WARP_ID_NONE, 6, 6);
    else if (IS_HNS)
        SetWarpDestination(MAP_GROUP(MAP_NEW_BARK_TOWN_PLAYERS_HOUSE_2F_HNS), MAP_NUM(MAP_NEW_BARK_TOWN_PLAYERS_HOUSE_2F_HNS), 1, 0, 0);
    else
        SetWarpDestination(MAP_GROUP(MAP_INSIDE_OF_TRUCK), MAP_NUM(MAP_INSIDE_OF_TRUCK), WARP_ID_NONE, -1, -1);
    WarpIntoMap();
}

void Sav2_ClearSetDefault(void)
{
    ClearSav2();
    SetDefaultOptions();
}

void ResetMenuAndMonGlobals(void)
{
    gDifferentSaveFile = FALSE;
    ResetPokedexScrollPositions();
    ZeroPlayerPartyMons();
    ZeroEnemyPartyMons();
    ResetBagScrollPositions();
    ResetPokeblockScrollPositions();
}

void NewGameInitData(void)
{
#if IS_FRLG
    u8 rivalName[PLAYER_NAME_LENGTH + 1];
#endif
    struct ChallengeSettings savedChallenge = gSaveBlock3Ptr->challengeSettings;
    struct MutagenSettings savedMutagen = gSaveBlock3Ptr->mutagenSettings; // chosen in the new-game menu (QW-29)
    if (gSaveFileStatus == SAVE_STATUS_EMPTY || gSaveFileStatus == SAVE_STATUS_CORRUPT)
        RtcReset();

#if IS_FRLG
    StringCopy(rivalName, gSaveBlock1Ptr->rivalName);
#endif
    gDifferentSaveFile = TRUE;
    gSaveBlock2Ptr->encryptionKey = 0;
    ZeroPlayerPartyMons();
    ZeroEnemyPartyMons();
    ResetPokedex();
    ClearFrontierRecord();
    ClearSav1();
    ClearSav3();
    gSaveBlock1Ptr->saveVersionMagic = SAVE_VERSION_MAGIC;
    gSaveBlock1Ptr->saveVersion = SAVE_VERSION;
    SetDefaultChallengeSettings();
    gSaveBlock3Ptr->challengeSettings = savedChallenge;
    gSaveBlock3Ptr->mutagenSettings = savedMutagen;
    ClearAllMail();
    gSaveBlock2Ptr->specialSaveWarpFlags = 0;
    gSaveBlock2Ptr->gcnLinkFlags = 0;
    InitPlayerTrainerId();
    PlayTimeCounter_Reset();
    ClearPokedexFlags();
    InitEventData();
    ClearTVShowData();
    ResetGabbyAndTy();
    ClearSecretBases();
    ClearBerryTrees();
    SetMoney(&gSaveBlock1Ptr->money, 3000);
    SetCoins(0);
    ResetLinkContestBoolean();
    ResetGameStats();
    ClearAllContestWinnerPics();
    ClearPlayerLinkBattleRecords();
    InitSeedotSizeRecord();
    InitLotadSizeRecord();
    gPlayerPartyCount = 0;
    ZeroPlayerPartyMons();
    ResetPokemonStorageSystem();
    DeactivateAllRoamers();
    gSaveBlock1Ptr->registeredItem = ITEM_NONE;
    gSaveBlock3Ptr->registeredItemHold = ITEM_NONE;
    ClearBag();
    NewGameInitPCItems();
    ClearPokeblocks();
    ClearDecorationInventories();
    InitEasyChatPhrases();
    SetMauvilleOldMan();
    InitDewfordTrend();
    ResetFanClub();
    ResetLotteryCorner();
    WarpToTruck();
#if IS_FRLG
    RunScriptImmediately(EventScript_ResetAllMapFlagsFrlg);
#elif IS_HNS
    RunScriptImmediately(EventScript_ResetAllMapFlagsHnS);
#else
    RunScriptImmediately(EventScript_ResetAllMapFlags);
#endif
#if IS_FRLG
        StringCopy(gSaveBlock1Ptr->rivalName, rivalName);
#endif
    ResetMiniGamesRecords();
    InitUnionRoomChatRegisteredTexts();
    InitLilycoveLady();
    ResetAllApprenticeData();
    ClearRankingHallRecords();
    InitMatchCallCounters();
    ClearMysteryGift();
    WipeTrainerNameRecords();
    ResetTrainerHillResults();
    ResetTrainerTowerResults();
    ResetContestLinkResults();
    SetCurrentDifficultyLevel(DIFFICULTY_NORMAL);
    ResetItemFlags();
    ResetDexNav();
    ClearFollowerNPCData();

    // Sync engine flags from restored challenge settings
    if (!gSaveBlock3Ptr->challengeSettings.tx_Mode_Mints)
        FlagSet(FLAG_MINTS_DISABLED);
    if (gSaveBlock3Ptr->challengeSettings.evenFasterJoy == 0)
        FlagSet(FLAG_EVEN_FASTER_JOY);

#if IS_HNS
    StringCopy(gSaveBlock2Ptr->rivalName, gText_ExpandedPlaceholder_Silver);
    InitMomSavings();
#endif
#if MUTAGEN_SANDBOX
    Sandbox_StockNewGame();
#endif
}

static void ResetMiniGamesRecords(void)
{
    CpuFill16(0, &gSaveBlock2Ptr->berryCrush, sizeof(struct BerryCrush));
    SetBerryPowder(&gSaveBlock2Ptr->berryCrush.berryPowderAmount, 0);
    ResetPokemonJumpRecords();
    CpuFill16(0, &gSaveBlock2Ptr->berryPick, sizeof(struct BerryPickingResults));
}

static void ResetItemFlags(void)
{
#if OW_SHOW_ITEM_DESCRIPTIONS == OW_ITEM_DESCRIPTIONS_FIRST_TIME
    memset(&gSaveBlock3Ptr->itemFlags, 0, sizeof(gSaveBlock3Ptr->itemFlags));
#endif
}

static void ResetDexNav(void)
{
#if USE_DEXNAV_SEARCH_LEVELS == TRUE
    memset(gSaveBlock3Ptr->dexNavSearchLevels, 0, sizeof(gSaveBlock3Ptr->dexNavSearchLevels));
#endif
    gSaveBlock3Ptr->dexNavChain = 0;
}

#if MUTAGEN_SANDBOX
// The bag's Items pocket holds 236 kinds of item and the PC's item storage 50, out of about 530,
// so these groups go in last: they end up held by the Pokémon in the PC boxes.
static const u16 sSandboxLaterItems[][2] =
{
    {ITEM_HELIX_FOSSIL, ITEM_FOSSILIZED_DINO},
    {ITEM_RED_APRICORN, ITEM_DYNITE_ORE},
    {ITEM_FLAME_PLATE, ITEM_PIXIE_PLATE},
    {ITEM_NORMAL_GEM, ITEM_FAIRY_GEM},
    {ITEM_RED_NECTAR, ITEM_PURPLE_NECTAR},
    {ITEM_DOUSE_DRIVE, ITEM_RUSTED_SHIELD},
    {ITEM_NORMALIUM_Z, ITEM_ULTRANECROZIUM_Z},
    {ITEM_BUG_TERA_SHARD, ITEM_WATER_TERA_SHARD},
    {ITEM_STELLAR_TERA_SHARD, ITEM_STELLAR_TERA_SHARD},
    {ITEM_BOTTLE_CAP, ITEM_STRANGE_SOUVENIR},
    {ITEM_GROWTH_MULCH, ITEM_AMAZE_MULCH},
    {ITEM_RED_SCARF, ITEM_YELLOW_SCARF},
    {ITEM_HARBOR_MAIL, ITEM_RETRO_MAIL},
};

// Key items stay out: a story script that gives one you already hold can stop at "bag full". The
// debug menu's PC/Bag → Fill Key Items gives them all.
static bool32 Sandbox_SkipItem(enum Item itemId)
{
    return GetItemPocket(itemId) == POCKET_KEY_ITEMS
        || (itemId >= ITEM_UNUSED_BERRY_1 && itemId <= ITEM_UNUSED_BERRY_3);
}

static bool32 Sandbox_IsLaterItem(enum Item itemId)
{
    u32 i;

    for (i = 0; i < ARRAY_COUNT(sSandboxLaterItems); i++)
    {
        if (itemId >= sSandboxLaterItems[i][0] && itemId <= sSandboxLaterItems[i][1])
            return TRUE;
    }
    return FALSE;
}

// Into the bag, else the PC's item storage, else held by the next PC Pokémon without an item.
// Mail is never held: a held letter needs its own mail data.
static void Sandbox_GiveItem(enum Item itemId, u32 *holder, u32 monCount)
{
    u16 count = MAX_BAG_ITEM_CAPACITY;
    u16 heldItem = itemId;

    if (GetItemPocket(itemId) == POCKET_TM_HM)
    {
        if (ItemIdToBattleMoveId(itemId) == MOVE_NONE)
            return;
        count = 1;
    }
    if (CheckBagHasSpace(itemId, count))
        AddBagItem(itemId, count);
    else if (AddPCItem(itemId, MAX_PC_ITEM_CAPACITY))
        return;
    else if (*holder < monCount && !(itemId >= ITEM_HARBOR_MAIL && itemId <= ITEM_RETRO_MAIL))
    {
        SetBoxMonData(&gPokemonStoragePtr->boxes[*holder / IN_BOX_COUNT][*holder % IN_BOX_COUNT],
                      MON_DATA_HELD_ITEM, &heldItem);
        (*holder)++;
    }
}

static void Sandbox_StockNewGame(void)
{
    enum Item itemId;
    u32 i, monCount = 0, holder = 0;
    u16 species;
    struct BoxPokemon boxMon;

    // PC boxes 1-13: every species in National Dex order from Bulbasaur, at level 50 with random
    // natures and IVs. Box 14 stays empty so catching still works.
    for (species = SPECIES_BULBASAUR; species < NUM_SPECIES && monCount < (TOTAL_BOXES_COUNT - 1) * IN_BOX_COUNT; species++)
    {
        if (!IsSpeciesEnabled(species))
            continue;
        CreateBoxMon(&boxMon, species, 50, Random32(), OTID_STRUCT_PLAYER_ID);
        SetBoxMonIVs(&boxMon, USE_RANDOM_IVS);
        GiveBoxMonInitialMoveset(&boxMon);
        gPokemonStoragePtr->boxes[monCount / IN_BOX_COUNT][monCount % IN_BOX_COUNT] = boxMon;
        // Seen and caught, so the Pokédex, the type icons' CAUGHT mode and dex-gated NPCs know them.
        HandleSetPokedexFlag(SpeciesToNationalPokedexNum(species), FLAG_SET_CAUGHT, GetBoxMonData(&boxMon, MON_DATA_PERSONALITY));
        monCount++;
    }

    // Every item but key items: the useful ones first, so they land in the bag.
    for (itemId = ITEM_NONE + 1; itemId < ITEMS_COUNT; itemId++)
    {
        if (!Sandbox_SkipItem(itemId) && !Sandbox_IsLaterItem(itemId))
            Sandbox_GiveItem(itemId, &holder, monCount);
    }
    for (i = 0; i < ARRAY_COUNT(sSandboxLaterItems); i++)
    {
        for (itemId = sSandboxLaterItems[i][0]; itemId <= sSandboxLaterItems[i][1]; itemId++)
        {
            if (!Sandbox_SkipItem(itemId))
                Sandbox_GiveItem(itemId, &holder, monCount);
        }
    }
    SetMoney(&gSaveBlock1Ptr->money, MAX_MONEY);
}
#endif // MUTAGEN_SANDBOX
