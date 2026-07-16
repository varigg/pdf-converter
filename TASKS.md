# Task list — remaining work

Written 2026-07-14, for whoever (agent or human) picks this project up next.
This checkout was just moved from `~/projects/python/pdf-converter` (a
Windows-mounted filesystem, git-hostile under WSL) to `~/code/pdf-converter`
and given its first `git init` (root commit `68c2ed5`, branch `main`). It had
no prior history — treat anything here as day-one state, not as a
regression from some earlier "working" version.

It is a tag-pinned Git dependency of `adventure-library`'s optional
`pdf-extraction` extra. Changes to the public API of
`pdf_converter.extractor` (`extract_text_from_pdf` and the additive
`extract_pdf_with_metadata`) should preserve the documented plain-text and
metadata contracts.

## 0. NEW (2026-07-16): Docling backend — read the rationale first

`adventure-library` measured this package's strategies head-to-head and its
design now calls for a `docling` extraction strategy (structured markdown,
`<!-- page N -->` markers, built-in OCR) behind an optional `[docling]` extra,
tagged `v0.1.0`. **Read `docs/docling-backend-rationale.md` before any
analysis or refactoring** — it records what was measured about the existing
strategies (including that `pymupdf4llm` dropped 92% of a clean document and
that `summarizer.py` has no consumer), which contracts must hold, and where
refactoring latitude exists.

- [x] Read `docs/docling-backend-rationale.md`
- [x] Add `docling` strategy with page-marker markdown export
- [x] `[docling]` optional extra; base install stays light. The extra pins
      `docling[rapidocr]` — RapidOCR is itself an optional extra of docling,
      and plain `docling` would not reproduce the OCR behaviour measured in
      the rationale.
- [ ] Tag `v0.1.0`; verified 2026-07-16 against synthetic fixtures (clean
      3-pager with an empty middle page; rasterized zero-text scan of the
      same content) **and** the two real corpus PDFs from the rationale's
      measurements: Bad Light (29,117 chars vs the RFC's 28,987 — the delta
      is the 8 page markers — 19 headings, 49s) and The Twilight Tomb pure
      scan (147,578 chars vs ~147k, all seven named entities OCR-recovered,
      178s). Markers and offsets held on all four documents.

## 1. Decide on publishing, then act on it

`pyproject.toml` declares the repository URL:

```
[project.urls]
Repository = "https://github.com/varigg/pdf-converter"
```

The repository is published. Documentation is maintained in-repo rather than
being deployed as a GitHub Pages site:

- [x] Create the `varigg/pdf-converter` GitHub repo.
- [x] Push `main`.
- [x] Keep MkDocs source documentation in the repository; do not deploy a
      GitHub Pages site or declare a Pages homepage URL.
- [x] Tag `v0.0.1` and move `adventure-library`'s optional
      `pdf-extraction` dependency from its absolute editable path to the
      public Git source. Its lockfile pins tag `v0.0.1` to commit
      `f27b5fe`, and its handoff now records the resolved portability gap.

## 2. Upstream feature work adventure-library is waiting on

Both of these are named, specific blockers in
`adventure-library/docs/6-memo/handoff.md` — read that file's "Hard
dependencies" and "Known errata" sections for the consumer-side context
before starting.

- [x] **Page markers.** `extract_pdf_with_metadata` preserves the plain-string
      return contract of `extract_text_from_pdf` while exposing `pypdf`
      character offsets for every PDF page, including empty pages. Consumers
      can use `page_number - 1` to look up a one-based PDF page in
      `page_offsets` when attributing a character span.
- [x] **Coverage / garble quality metrics.**
      `extract_pdf_with_metadata` also returns `ExtractionQuality`, including
      text length, alphabetic-character ratio, suspicious-token count, and a
      consonant-run garble score. `is_likely_garbled` is a conservative review
      signal; consumers retain control over OCR and rejection policy.
- [ ] **Once either lands**, adventure-library has its own follow-up: a
      "stale-span guard" must ship *before* any corpus is re-extracted with
      the new extractor, because re-extraction rewrites markdown in place
      and silently invalidates existing component provenance spans. That
      guard is adventure-library's responsibility, not this repo's — just
      don't be surprised if the consumer isn't ready to re-extract the
      moment this lands. Coordinate before triggering a real re-extraction
      of the 85-document corpus.

## 3. Housekeeping noticed during the move

- [x] Expand `README.md` with installation, CLI, library API, and development
      guidance.
- [x] `requires-python` now targets `>=3.10,<4.0`; adventure-library itself
      requires `>=3.12`.
- [x] Verify CI configuration. `Main` and `validate-codecov-config` now run
      successfully on pushes to `main`; the obsolete GitHub Pages release
      workflow was removed because documentation stays in the repository. The
      Codecov config validates successfully.
- [x] Verify `.pre-commit-config.yaml` against the current toolchain. Its
      Ruff hooks run successfully alongside `ty`; `make check` is the
      project-level verification command.
- [ ] A stray extracted personal document (a tax return, ~711KB markdown
      file) was found sitting uncommitted at the checkout root during the
      move to `~/code`. It was relocated to `~/private-scratch/` and never
      entered git history, but it's a signal that ad-hoc test runs have
      dropped real personal files into this working directory before —
      double-check for similar artifacts before any bulk `git add`, and
      never point a test fixture at real personal documents.
