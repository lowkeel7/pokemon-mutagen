#ifndef GUARD_MUTAGEN_H
#define GUARD_MUTAGEN_H

// Pokémon Mutagen's options (struct MutagenSettings, global.h) read at their gameplay sites.
// Every accessor returns Heart & Soul's behaviour for a zeroed block or a NULL save pointer.

struct ScriptContext;

u32 GetPokerusInfectionOdds(void);     // out of 65536 per battle (QW-20)
bool32 ShouldAnnouncePokerus(void);    // a post-battle notice when POKÉRUS is above RARE
u64 GetMutagenTrainerAiFlags(void);    // added to every trainer's AI flags (QW-31)
bool32 AreShinyTokensSold(void);       // SHINY TOKEN in every Poké Mart (QW-14)
bool32 IsStarterPickAny(void);         // the lab's balls open a species list (SG-16)
bool32 IsDiscoveryOn(void);            // wild bosses, lead-ability encounter pulls (QW-32)
bool32 IsThirdTypeOn(void);            // the grafted third type is live (SG-01)
bool32 AreRelicsOn(void);              // species parts can be worn (SG-09)
bool32 CheatShelfOn(void);             // CHEATS tab (QW-16/17/18/26/13)
bool32 CheatShopEverything(void);      // CHEAT SHELF → ALL: every item but the key items in every mart (QW-07)
bool32 CheatInfinitePp(void);
bool32 CheatCatchAlways(void);
void Mutagen_ApplyCheats(void);        // flags, the Box Link and the Pokédex follow the CHEATS rows
u32 GetMonThirdType(struct Pokemon *mon); // the live third type, TYPE_NONE when off, pending or unset; a worn part's type first (SG-09)
u32 GetMonOwnThirdType(struct Pokemon *mon); // the Pokémon's own grafted type under any worn part, TYPE_NONE when off, pending or unset
extern bool8 gWildBossPending;         // the wild Pokémon just created is a boss (QW-32)
u32 GetShinyStarterMode(void);         // 0 chance, 1 ask, 2 always (SG-16)
void Mutagen_StarterPicker(struct ScriptContext *ctx);
void Mutagen_StarterShinyMode(struct ScriptContext *ctx);
void Mutagen_SetStarterShiny(struct ScriptContext *ctx);

bool32 MutagenRollsHere(void);         // the mutant strain can be caught on this map (SG-17)
bool32 MutagenHasRunItsCourse(struct Pokemon *mon); // mutant strain, days down to 0: mutations may set
void MutagenOnStrainEnd(struct Pokemon *mon);       // the day the mutant strain ends: hidden ability

// NEW GAME+ (SG-15): offered on the title menu once the game is cleared; the title sets the pending
// loop number, NewGameInitData carries the team, boxes, bag, money and Pokédex across the reset.
bool32 IsNewGamePlusOffered(void);
void NewGamePlus_ChooseAtTitle(void);       // sets or clears the pending loop for the coming new game
bool32 NewGamePlus_IsPending(void);
void *NewGamePlus_Snapshot(void);           // before the bag's encryption key is reset
void NewGamePlus_RestoreDex(const void *carry);
void NewGamePlus_RestoreItemsAndMoney(const void *carry);
void NewGamePlus_Finish(void *carry);       // level reset, the loop count, frees the snapshot
u32 ApplyNewGamePlusRamp(u32 level);        // +1 level per New Game+ loop for wild and trainer Pokémon

extern u8 gPokerusNoticeSlot;          // party slot + 1 of the Pokémon that just caught Pokérus, 0 none
extern u8 gPokerusNoticeKind;          // 1 caught Pokérus, 2 caught the mutant strain, 3 the mutant strain ran its course
void FieldCB_ReturnToFieldPokerusNotice(void);
void Mutagen_BufferPokerusNoticeMon(struct ScriptContext *ctx);

#endif // GUARD_MUTAGEN_H
