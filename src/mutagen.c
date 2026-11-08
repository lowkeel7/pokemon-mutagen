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
