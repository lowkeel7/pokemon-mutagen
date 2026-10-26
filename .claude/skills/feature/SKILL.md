---
name: feature
description: Take one Pokerom backlog row from idea to a shipped, toggled, tested feature. Use for "build QW-07", "add <feature>", "implement the next backlog item", or starting work on any BACKLOG ID. Porting from HnS+: hnsplus-pick.
---

# feature: one BACKLOG row → merged

```
BACKLOG row → exists? → design gate → branch → toggle → code → build → test → mGBA → BACKLOG + commit
```

| Step | Do | Done when |
|---|---|---|
| 1. Row | Find the ID in `docs/pokerom/BACKLOG.md`. No row → add one first. | the row exists |
| 2. Exists? | CLAUDE.md §3, in order: the codebase (`grep -rn` for the config switch, `#if IS_HNS`), `git log hnsplus/master -S<symbol>`, `git log rhh/master -S<symbol>`. If HnS+ has it → stop, use `hnsplus-pick`. | prior art named in the row |
| 3. Design gate | Status `design` or a ❓ → ask the user the open questions (batch ≤4) and write the answers into the row. Never guess a design choice. | row status `todo` |
| 4. Branch | `git switch -c feat/<id>-<slug> pokerom/dev` | |
| 5. Toggle | `.claude/rules/options.md`. Zero = HnS behaviour. Claims of save bits, flags or vars go in the row and in `save.md`'s plan. | old save loads with it off |
| 6. Code | Open the area's rule first (index in CLAUDE.md §6). Match the surrounding code's style. | |
| 7. Build | `make hns -j$(sysctl -n hw.ncpu)`. Art or audio → note the ROM bytes before and after. | clean build |
| 8. Test | Battle logic → a test in `test/battle/...` with the toggle on; run `make check BUILD=hns TESTS="<name>"`. | test fails without the change, passes with it |
| 9. mGBA | Play the feature with the toggle on and off. Screenshot each menu step; for menus, count the pixels. | seen working, both polarities |
| 10. Land | Set the row's status to `done` in the same commit. `TZ=UTC git commit`. Merge into `pokerom/dev`. | |

## Rules
- One feature per branch. Several small QW rows may share a branch only if they share a toggle tab.
- A feature that needs art waits for the space plan (BACKLOG "Space and save budgets").
- No AI-generated art, music or story text. Placeholder art is a solid-colour box, never generated.
- If the build or a test fails for a reason outside the feature, check `pokerom/dev` itself first.
  HnS+ reported `make check` and `test/save.c` broken upstream; confirm and record that on the baseline.
