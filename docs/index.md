<div class="m-hero">
<div>
<div class="m-eyebrow">Pokémon</div>
{{#include pokerom/brand/wordmark-inline.svg}}
<p class="m-tagline">A second line of evolution.</p>
<p class="m-lede">A Game Boy Advance game, forked from Pokémon Heart & Soul. The Mutagen, a mutant strain of Pokérus, lets a Pokémon evolve along a second line, into its Paradox or regional twin, and grafts a third type onto it. Everything new is an option; switched off, the game plays like Heart & Soul.</p>
<div class="m-actions"><a class="m-btn primary" href="project-readme.html#play">Play it</a><a class="m-btn ghost" href="pokerom/evolutions.html">The evolutions</a><a class="m-btn ghost" href="https://github.com/lowkeel7/pokemon-mutagen">GitHub</a></div>
<div class="m-chips"><span class="m-chip">GBA · flash cart · mGBA</span><span class="m-chip">Patch, never a ROM</span><span class="m-chip">v0.1.0</span></div>
</div>
<div class="m-tree">
<figure><img class="m-sprite" style="--s:2" src="pokerom/sprites/wooper.png" alt="Wooper"><figcaption>Wooper</figcaption></figure>
{{#include pokerom/brand/fork-inline.svg}}
<div class="lines">
<figure class="usual"><img class="m-sprite" style="--s:2" src="pokerom/sprites/quagsire.png" alt="Quagsire"><figcaption>Quagsire</figcaption></figure>
<figure class="twin"><img class="m-sprite" style="--s:2" src="pokerom/sprites/clodsire.png" alt="Clodsire"><figcaption>Clodsire</figcaption><div class="types"><span class="m-type" style="--c:#a441a4">Poison</span><span class="m-type" style="--c:#e6c56a">Ground</span><span class="m-type" style="--c:#7339ff">Dragon</span></div></figure>
</div>
</div>
</div>

## What the Mutagen does

<div class="m-cards">
<div class="m-card"><div class="m-eyebrow">The strain</div><h3>Pokérus, mutated</h3><p>Where the strain has taken hold (Lake of Rage, the Rocket hideouts, Cerulean Cave, the Power Plant, the Burned Tower, or anywhere on RAMPANT) a Pokémon can catch the Mutagen after a battle. It spreads through the party and doubles effort values like Pokérus, and it burns out in four days.</p></div>
<div class="m-card"><div class="m-eyebrow">The second line</div><h3>Twenty-six twins</h3><p>A Pokémon that outlives the strain wakes its hidden ability, and its next level-up may take the other road: Wooper to Clodsire, Scyther to Kleavor, Donphan to Great Tusk or Iron Treads by the strain's parity. The usual line stays open.</p></div>
<div class="m-card"><div class="m-eyebrow">The graft</div><h3>A third type</h3><p>The Mutagen's evolution grafts a third type onto the Pokémon. It shows in the summary beside the other two and counts in battle.</p></div>
<div class="m-card"><div class="m-eyebrow">The rule</div><h3>Everything is an option</h3><p>Every Mutagen mechanic sits behind an in-game toggle whose off position is Heart & Soul, so old saves read off and the base game stays reachable. Cheats have a tab of their own.</p></div>
</div>

## Play it

1. Get a Pokémon Emerald (USA) ROM with SHA-1 `f3ae088181bf583e55daf962a92bb46f4f1d07b7`. We don't provide ROMs or links to them.
2. Apply `pokemon-mutagen-0.1.0.bps` from the [release page](https://github.com/lowkeel7/pokemon-mutagen/releases) to a copy of it, with [Flips](https://github.com/Alcaro/Flips) on a computer or UniPatcher on Android. RetroArch also patches on the fly when the `.bps` sits next to the ROM under the same name.
3. Play it in mGBA, in RetroArch with the mGBA core, or on a flash cart. The save type is FLASH 1M; on a cart or emulator without a clock choose FAKE RTC in the new-game options. Saves from Heart & Soul 2.0.6 carry over.

The full notes, the bug-report address and the credits are in [the project README](project-readme.html).

## In this book

<ul class="m-links">
<li><a href="pokerom/evolutions.html"><b>Mutagen evolutions</b><span>Every family with a second line, with the game's own sprites.</span></a></li>
<li><a href="pokerom/CHANGELOG.html"><b>Changelog</b><span>What changed against Heart & Soul 2.0.6, release by release.</span></a></li>
<li><a href="pokerom/BACKLOG.html"><b>Backlog</b><span>Every feature: its tier, its hook in the code and where it stands.</span></a></li>
<li><a href="pokerom/design/brand.html"><b>Design notes</b><span>The brand, the type roots, status escalation, species items.</span></a></li>
<li><a href="pokerom/VOXEL.html"><b>Voxel view</b><span>The desktop companion that draws the overworld as blocks.</span></a></li>
<li><a href="pokerom/CONTRIBUTING.html"><b>Contributing and Steak</b><span>How to send a change and how credit works.</span></a></li>
<li><a href="pokerom/PROVENANCE.html"><b>Provenance</b><span>Where every imported piece comes from, and its terms.</span></a></li>
<li><a href="hns/README.html"><b>Heart &amp; Soul</b><span>The base game's own README, features and engine documentation.</span></a></li>
</ul>

<p class="m-foot">Pokémon is © Nintendo, Creatures Inc. and GAME FREAK inc. Pokémon Mutagen is a free fan project, not affiliated with them; it ships only a patch, never a ROM. It is built on Pokémon Heart &amp; Soul 2.0.6 and pokeemerald-expansion. Most of the code was written with an AI coding assistant, as <a href="project-readme.html#ai-disclosure">the README's disclosure</a> says; none of the art, music or story text is generated. Made with <a href="https://github.com/irie-people/irie">Irie</a>.</p>
