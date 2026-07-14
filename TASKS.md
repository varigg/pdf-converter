# Task list — remaining work

Written 2026-07-14, for whoever (agent or human) picks this project up next.
This checkout was just moved from `~/projects/python/pdf-converter` (a
Windows-mounted filesystem, git-hostile under WSL) to `~/code/pdf-converter`
and given its first `git init` (root commit `68c2ed5`, branch `main`). It had
no prior history — treat anything here as day-one state, not as a
regression from some earlier "working" version.

It's an editable path dependency of `~/code/adventure-library`'s optional
`pdf-extraction` extra (`[tool.uv.sources]` in that repo's `pyproject.toml`
points here). Changes to the public API of `pdf_converter.extractor`
(currently just `extract_text_from_pdf`) are consumed by
`adventure-library/src/adventure_library/extraction.py`.

## 1. Decide on publishing, then act on it

`pyproject.toml` already declares:

```
[project.urls]
Homepage = "https://varigg.github.io/pdf-converter/"
Repository = "https://github.com/varigg/pdf-converter"
```

Neither exists yet. Either the metadata is aspirational and should be
removed/commented until true, or the intent is to publish — in which case:

- [ ] Create the `varigg/pdf-converter` GitHub repo (see adventure-library's
      recent onboarding for the pattern: `gh repo create`, then
      `git remote set-url origin https://github.com/...` + `gh auth
      setup-git` rather than plain SSH — this box's `~/.ssh/config` aliases
      GitHub as `github.com-personal`, so a bare `git@github.com:` remote
      fails).
- [ ] Push `main`.
- [ ] Decide whether to actually stand up the `mkdocs.yml`-based docs site at
      the declared GitHub Pages URL, or drop the `Homepage` URL for now.
- [ ] Once pushed, `adventure-library`'s `[tool.uv.sources]` editable path
      pin can eventually move to a git or PyPI source instead of an
      absolute local path — closes out that project's last portability gap
      for this dependency. Don't do this until pdf-converter has at least
      one tagged version; update `adventure-library/docs/6-memo/handoff.md`
      hard dependency #3 when it happens.

## 2. Upstream feature work adventure-library is waiting on

Both of these are named, specific blockers in
`adventure-library/docs/6-memo/handoff.md` — read that file's "Hard
dependencies" and "Known errata" sections for the consumer-side context
before starting.

- [ ] **Page markers.** `extract_text_from_pdf` currently returns plain
      text/markdown with no page-boundary information. adventure-library's
      design (`docs/design.md`) wants page numbers in component provenance
      "when available" — right now it's never available. Emit page
      markers (e.g. inline sentinel comments, or a parallel offset→page
      map) that a downstream caller can use to attribute a character span
      to a page.
- [ ] **Coverage / garble quality metrics.** adventure-library has one
      corpus document (out of 85) where extraction produced a heavily
      garbled body under clean-looking headings — heading-based quality
      heuristics on the consumer side can't detect this class of failure.
      Add a quality signal here (e.g. a garble-consonant-ratio check, or a
      dictionary-coverage score) that downstream code can use to flag
      likely-bad extractions before they're segmented and sent to an LLM.
- [ ] **Once either lands**, adventure-library has its own follow-up: a
      "stale-span guard" must ship *before* any corpus is re-extracted with
      the new extractor, because re-extraction rewrites markdown in place
      and silently invalidates existing component provenance spans. That
      guard is adventure-library's responsibility, not this repo's — just
      don't be surprised if the consumer isn't ready to re-extract the
      moment this lands. Coordinate before triggering a real re-extraction
      of the 85-document corpus.

## 3. Housekeeping noticed during the move

- [ ] `README.md` is a 3-line stub — expand it to actually describe the
      tool (it currently only exists to satisfy hatchling's `readme =
      "README.md"` requirement in `pyproject.toml`).
- [ ] `requires-python = ">=3.9,<4.0"` — confirm this floor is still
      intentional; adventure-library itself requires `>=3.12`.
- [ ] `.github/workflows/` (`main.yml`, `on-release-main.yml`,
      `validate-codecov-config.yml`) and `codecov.yaml` exist but have never
      run (no remote, no CI history). Verify they're not stale
      copier/cookiecutter template output before relying on them.
- [ ] `.pre-commit-config.yaml` exists — confirm hooks still match the
      current toolchain (ruff version, mypy config) before assuming it's
      wired up correctly.
- [ ] A stray extracted personal document (a tax return, ~711KB markdown
      file) was found sitting uncommitted at the checkout root during the
      move to `~/code`. It was relocated to `~/private-scratch/` and never
      entered git history, but it's a signal that ad-hoc test runs have
      dropped real personal files into this working directory before —
      double-check for similar artifacts before any bulk `git add`, and
      never point a test fixture at real personal documents.
