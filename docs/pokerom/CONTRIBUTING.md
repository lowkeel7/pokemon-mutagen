# Contributing to Pokémon Mutagen

Anyone can contribute, and every merged contribution earns **Steak**: credit on the
project's public stake record, sized by a maintainer. Steak is credit, never money.
Pokémon Mutagen is a fan-made hack of a game it doesn't own, so it takes no money at all.
The rules are in `STAKE.md` in the stake repository.

(The `CONTRIBUTING.md` at the top of this repository is pokeemerald-expansion's, for
changes sent upstream.)

## What Mutagen is

Pokémon Heart & Soul 2.0.6 on pokeemerald-expansion 1.15, made configurable from end to end.
That is the promise: every system is an in-game option, and its zero value is plain Heart &
Soul, so an old save reads "off" and the expansion's battle tests still pass (`CLAUDE.md`
section 2). The plan, row by row, is in [BACKLOG.md](BACKLOG.md).

## Before you start

- Pick a BACKLOG row or open an issue. Agree anything that would size at 5 Steak or more in the
  issue first.
- Read `CLAUDE.md`: how to build, the targets (real hardware and RetroArch's mGBA core on a
  phone), and the rules for each area in `.claude/rules/`.

## Your change

- Build with `make hns`, and `make release BUILD=hns` for what ships.
- Run the gates that cover it: `tools/testgate/testgate.py` for battle, item and engine code,
  `tools/spritecheck/spritecheck.py --strict` for anything that touches Pokémon graphics, and
  the smoke test in `tools/playtest/` for anything a player sees.
- Play what you changed, and say in the pull request how you checked it.
- Art, music, maps and writing must be your own work, never AI-generated. Record where each
  asset comes from in [PROVENANCE.md](PROVENANCE.md).
- Code written with an agent is fine: say so in the pull request. You answer for every line.
- Never use leaked Game Freak material. Share BPS patches only, never a ROM or a link to one.

## Steak

| Steak | Looks like |
|---|---|
| 1 | A typo, a wrong label, a one-line default |
| 2 | A small fix with a check; a docs section |
| 3 | A bug that took real investigation |
| 5 | One option, working, with its zero value as plain Heart & Soul |
| 8 | A whole system behind its options, with tests |
| 13 | A milestone, such as the engine upgrade, or a region's worth of content |
| 21 | Architecture-level work; needs two maintainers |

A maintainer vouches for you after your first merged change, then sizes each merged change.
Nobody sizes their own work. Reviews, bug reports with a save or the steps, playtesting and
triage earn Steak too.
