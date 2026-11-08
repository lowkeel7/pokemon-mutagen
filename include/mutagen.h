#ifndef GUARD_MUTAGEN_H
#define GUARD_MUTAGEN_H

// Pokémon Mutagen's options (struct MutagenSettings, global.h) read at their gameplay sites.
// Every accessor returns Heart & Soul's behaviour for a zeroed block or a NULL save pointer.

struct ScriptContext;

u32 GetPokerusInfectionOdds(void);     // out of 65536 per battle (QW-20)
bool32 ShouldAnnouncePokerus(void);    // a post-battle notice when POKÉRUS is above RARE
u64 GetMutagenTrainerAiFlags(void);    // added to every trainer's AI flags (QW-31)
bool32 AreShinyTokensSold(void);       // SHINY TOKEN in every Poké Mart (QW-14)

extern u8 gPokerusNoticeSlot;          // party slot + 1 of the Pokémon that just caught Pokérus, 0 none
void FieldCB_ReturnToFieldPokerusNotice(void);
void Mutagen_BufferPokerusNoticeMon(struct ScriptContext *ctx);

#endif // GUARD_MUTAGEN_H
