@ Pokémon Mutagen's shared scripts.

@ After a wild battle in which a party member caught Pokérus, with POKÉRUS above RARE (QW-20).
Mutagen_EventScript_PokerusNotice::
	lockall
	callnative Mutagen_BufferPokerusNoticeMon
	msgbox Mutagen_Text_CaughtPokerus, MSGBOX_DEFAULT
	releaseall
	end

Mutagen_Text_CaughtPokerus:
	.string "{STR_VAR_1} caught POKéRUS!$"

@ The same, for the mutant strain (SG-17).
Mutagen_EventScript_MutagenNotice::
	lockall
	callnative Mutagen_BufferPokerusNoticeMon
	msgbox Mutagen_Text_CaughtMutagen, MSGBOX_DEFAULT
	releaseall
	end

Mutagen_Text_CaughtMutagen:
	.string "{STR_VAR_1} caught the MUTAGEN strain\nof POKéRUS!$"

@ After the next wild battle once the mutant strain has run its course (SG-17).
Mutagen_EventScript_MutagenEnded::
	lockall
	callnative Mutagen_BufferPokerusNoticeMon
	msgbox Mutagen_Text_MutagenEnded, MSGBOX_DEFAULT
	releaseall
	end

Mutagen_Text_MutagenEnded:
	.string "{STR_VAR_1}'s MUTAGEN strain ran its\ncourse!{STR_VAR_2}$"

@ SHINY STARTER (SG-16), called from Elm's lab once the starter is confirmed.
Mutagen_EventScript_AskShinyStarter::
	msgbox Mutagen_Text_ShinyStarter, MSGBOX_YESNO
	callnative Mutagen_SetStarterShiny
	return

Mutagen_EventScript_ForceShinyStarter::
	setvar VAR_RESULT, 1
	callnative Mutagen_SetStarterShiny
	return

Mutagen_Text_ShinyStarter:
	.string "Would you like it to be SHINY?$"
