# pdf-converter Charter

Stable intent only — this document changes rarely, via dedicated design
commits. If a release appears to invalidate it, addw-release flags it; the
charter is never silently edited.

## Purpose

pdf-converter exists to turn PDF files into Markdown-compatible text that
downstream tools can consume. Its one consumer today is adventure-library,
which imports the extraction API directly; the CLI and batch script serve
manual, one-off conversions.

## Product Principles

- **Contract stability.** The public extraction API is frozen; changes
  coordinate with the consumer in the same change.
- **Demand-driven scope.** Work arrives as filed issues plus repo hygiene —
  no independent roadmap.
- **Pluggable by registry.** Backends and providers extend through
  registries, never special cases.
- **Offline-testable.** No real PDFs, no real LLM calls in tests.
- **Privacy by default.** Documents are treated as private; nothing
  extracted lands in the repository.

## Scope

- PDF-to-Markdown text extraction (pypdf, mupdf, docling backends) with
  page-offset and quality metadata.
- A small CLI and batch script for manual conversions.
- Serving adventure-library's extraction needs as they are filed.

## Non-Goals

- **PyPI publishing** — the one consumer pins by git tag.
- **An independent feature roadmap** — scope is demand-driven only.
- **A general-purpose document pipeline** — one-off extractions are served
  by raw docling CLI or an agent's native PDF reading.
- **Downstream responsibilities** — e.g. the stale-span guard belongs to
  adventure-library.

## Success Criteria

- adventure-library's extraction needs are met without breaking the frozen
  API contract.
- Extraction quality is observable through the quality signals rather than
  discovered downstream.
- The repo stays healthy with minimal attention: CI green, docs building
  strictly, no accumulated private documents.
- The ADDW workflow demonstrably carries changes from issue to release.
