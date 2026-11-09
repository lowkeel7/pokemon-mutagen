---
paths:
  - "docs/pokerom/brand/**"
  - "docs/pokerom/design/brand.md"
  - "docs/theme/**"
  - "docs/index.md"
  - "docs/book.toml"
  - "docs/SUMMARY.md"
  - "tools/brand/**"
  - "tools/video/**"
  - "tools/site/**"
---

# Brand, cover art and the documentation site

The rules themselves (colours, type, the mark, layouts, don'ts) are `docs/pokerom/design/brand.md`;
this file is the working notes.

- **Everything in `docs/pokerom/brand/` is generated.** Change `tools/brand/brand.py` and rerun it
  (no arguments) rather than editing a PNG or SVG; it also writes `docs/theme/favicon.*`. The
  fonts come from `tools/brand/fonts.py` (pinned google/fonts commit, SHA-256 checked, Latin
  subsets); rerun it only to change the subset or the families, and add a PROVENANCE row.
- **No generated imagery, ever.** The wordmark is the title banner's pixels, the sprites are the
  game's, the mark and layouts are squares placed by code. A new letter in the banner font needs a
  line in the README's AI disclosure.
- **The site** is the mdbook in `docs/` (`cd docs && mdbook build`, mdbook 0.5.4 locally and in
  `.github/workflows/docs.yml`; keep the two equal). The theme is only `additional-css`/`js` in
  `docs/book.toml` plus `docs/theme/head.hbs` and the favicons: no `index.hbs` override, so mdbook
  upgrades stay cheap. mdbook renders any `README.md` chapter as `index.html`: the landing page is
  `docs/index.md`, the root README is wrapped by `docs/project-readme.md`, and `docs/fix_links.py`
  points `](README.md)` there.
- **Preview**: serve `docs/book` with `python3 -m http.server 8777 --bind 127.0.0.1` and take
  screenshots with a headless browser (its `--headless=new --screenshot=out.png
  --window-size=1280,1000 URL` flags; never a window). To see the dark look, copy a page and
  prepend `<script>localStorage.setItem("mdbook-theme","navy")</script>` to its head.
- **The evolution tree** (`docs/pokerom/evolutions.md`, `sprites/`) is written by
  `tools/site/evolutions.py`; its styles live in `mutagen.css` (`.evo`), the Mutagen arrow is the
  mark. Rerun it after any `IF_MUTAGEN*` change.
- **Videos**: `tools/video/stitch.py` (GBA clips + captions → one branded video with the title
  card) and `tools/voxel/record.py` (the voxel walk, title card first). Both read the TTFs in
  `docs/pokerom/brand/fonts/`; ffmpeg's drawtext cannot read woff2.
- **The social preview** has no API: upload `docs/pokerom/brand/cover.png` by hand (repository
  Settings → Social preview) when the cover changes.
