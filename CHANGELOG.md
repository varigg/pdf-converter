# Changelog

Release history, newest first. Maintained by the ADDW release skills; humans
read it, agents don't.

## v1.1.0 — 2026-11-10

### Features
- feat: add docling-ocr forced full-page OCR strategy (#16)

### Fixes
- fix: keep the install hint when the OCR engine is missing (#16)
- fix: pin RapidOCR so docling-ocr fails loudly without an engine (#16)

## v1.0.0 — 2026-11-02

### Breaking
- feat!: remove the mupdf extraction strategy (#13)
- feat!: retire the summarizer stack (#12)

### Other
- docs: describe the extraction-only, two-backend system (#13)
- docs: drop provider mention from error-handling section (#12)
- docs: drop LLM mocking conventions from the testing guide (#12)
- docs: rewrite ARCHITECTURE for the extraction-only system (#12)
- docs: rewrite ADR 0001 in the authoritative ADDW template (#5)
- docs: record the summarizer retirement (ADR 0001) and seed CONTEXT.md (#5)
- chore: ignore Claude Code local settings and worktrees
- docs: retire TASKS.md to the tracker (#7)

## v0.1.1 — 26-08-2026

chore: initialize the ADDW workflow

- Initialized ADDW — architecture, charter, testing guide, ADR declaration, and
  project config.
