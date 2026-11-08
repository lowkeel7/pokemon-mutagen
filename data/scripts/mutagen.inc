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
