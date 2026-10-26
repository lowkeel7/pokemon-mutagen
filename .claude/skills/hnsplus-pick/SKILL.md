---
name: hnsplus-pick
description: Port one feature from HnS+ (Marcogn/pokehns-expansion-plus) into Pokerom by reviewed cherry-pick. Use for "take X from HnS+", "cherry-pick the type icons / TcloneR / quest book", or when feature step 2 finds HnS+ prior art.
---

# hnsplus-pick: one HnS+ feature, reviewed

HnS+ forks the same HnS 2.0.6 commit (`167aa6d`), so its commits mostly apply cleanly. Its code is
AI-written and reviewed by nobody else: **read every hunk** before keeping it. Its notes are in Italian.

```sh
git fetch hnsplus
git log --oneline 167aa6d..hnsplus/master -- <paths>            # the feature's commits
git log --oneline 167aa6d..hnsplus/master --grep='<feature>'
git show hnsplus/master:.claude/rules/<area>.md                 # its traps for that area
git switch -c pick/<feature> pokerom/dev
git cherry-pick -x <sha>...                                     # oldest first; -x records the origin
```

## Checklist
1. **Find every commit.** HnS+ lands features as numbered phases plus review-fix commits ("phase 8:
   review fixes"). Take the fixes too, or you import known bugs.
2. **Dependencies.** Shared infrastructure (save migrations with `SAVE_VERSION`, the Dark UI accessor
   `IsDarkUiEnabled()`, the strip menu) comes first or gets stubbed. List what it needs before picking.
3. **Save layout.** HnS+ appends SaveBlock3 fields with migrations. Taking its fields in a different
   order gives a different layout: once Pokerom has its own fields, port the logic and re-lay out the
   save; don't cherry-pick save structs blindly.
4. **Toggle.** HnS+ ships some features always-on. Pokerom needs an option where the zero value is HnS.
5. **Strip the rest.** Drop the HnS+ branding (the "+" title, version strings), its `CHANGELOG.md` and
   README edits, `Claude-Session:` trailers, and anything Soulgold-content rather than code.
6. **Credit.** Add the feature to `docs/pokerom/PROVENANCE.md`: HnS+ commit SHAs, and the original
   source HnS+ credits (Soulgold/Eemeliri, PokemonSanFran, pollythadon…).
7. Then `feature` steps 7-10 (build, test, mGBA, BACKLOG row, `TZ=UTC git commit`).

## HnS+ → BACKLOG map (at `hnsplus/master` 6f1e2bf, 2026-10-26)
| HnS+ feature | BACKLOG |
|---|---|
| Types shown in battle (`src/type_icons.c`) | QW-01 |
| Shiny Genome item | QW-14 (make it a toggle, not one-way) |
| TcloneR trainer catch | QW-23 |
| Easy Catch, Force Shiny, full party editor (debug) | QW-16/18, SG-14 |
| Quest book, pause strip, box sort/search, DexNav, overworld wild Pokémon, level scaling | QW-24 |
| Move relearner from the summary | UP-03 |
| Mega with type stones (`claude/mega-type-stones`, unmerged) | SG-10 |
| CI that builds `hns` and reports ROM fill | phase 0 |
