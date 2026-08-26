# Architecture

## How to read this document

This is an **as-built** description of `pdf-converter` as it currently stands.
It is maintained by rewriting, never appending (see
`ARCHITECTURE-rules.md`): every section describes the system as it is today,
and machinery that no longer exists is deleted rather than marked historical.
Version history lives in `CHANGELOG.md`.

## Overview

`pdf-converter` is a Python library for turning PDF files into
Markdown-compatible text, with an optional LLM summarization path and a small
CLI wrapper. Its primary consumer is the `adventure-library` project, which
imports the extraction API directly; the CLI and batch script serve manual,
one-off use.

The system has three layers:

1. **Extraction** (`extractor.py`) — pluggable backends that turn a PDF path
   into text, optionally with page-offset and quality metadata.
2. **Summarization** (`summarizer.py` + `services/`) — prompt construction and
   a provider-abstracted LLM service with retries and local usage accounting.
3. **CLI** (`converter.py`) — argument parsing, orchestration, Markdown output
   writing, and optional archival of the source PDF.

## Technology stack

- **Language**: Python ≥ 3.10 (CI matrix runs 3.10–3.13), `src/` package
  layout, built with hatchling.
- **Package management**: uv, with a committed `uv.lock`.
- **PDF backends**: `pypdf` (plain text), `pymupdf4llm` (Markdown), and
  `docling` as an optional extra (`pdf-converter[docling]`, structured
  Markdown with per-page markers and OCR for scans).
- **LLM providers**: Gemini (via `google-genai`), Perplexity, OpenAI, and
  Anthropic (via `requests`).
- **Quality tooling**: ruff (lint + format), ty (type checking), pytest with
  branch coverage, deptry, pre-commit, tox-uv for the version matrix.
- **Docs**: MkDocs Material with mkdocstrings, built strictly
  (`mkdocs build -s`).
- **CI**: GitHub Actions — `make check` plus the pytest/ty matrix and a
  Codecov upload.

## Project structure

```
src/pdf_converter/
├── converter.py        # CLI entry point (pdf-converter = converter:main)
├── extractor.py        # extraction strategies, registries, public API
├── summarizer.py       # prompt construction, LLM orchestration entry
├── exceptions.py       # PDFConverterError hierarchy
└── services/
    ├── llm_client_factory.py  # authoritative provider registry
    ├── llm_providers.py       # per-provider HTTP/SDK clients
    ├── llm_service.py         # retries, usage tracking, response handling
    └── usage_tracker.py       # local monthly usage/cost accounting
tests/                  # pytest unit tests, all I/O and network mocked
docs/                   # MkDocs source tree (this file lives in it)
convert-folder.sh       # batch wrapper around the CLI
```

## Core architecture principles

- **Strategy + registry for extensibility.** Extraction backends implement the
  `ExtractionStrategy` protocol and are selected from
  `EXTRACTION_STRATEGIES` / `EXTRACTION_RESULT_STRATEGIES`; LLM providers are
  selected from `PROVIDER_FACTORIES` in `llm_client_factory.py`. CLI choices
  are **derived from these registries** (`SUPPORTED_EXTRACTORS`,
  `SUPPORTED_PROVIDERS`), never duplicated.
- **Dependency injection at the boundaries.** `PDFExtractor` receives its
  strategy; `LLMService` receives its provider, tracker, and sleep function —
  which is what keeps the retry logic and the CLI testable without real PDFs
  or network calls.
- **Additive API evolution.** `extract_pdf_with_metadata` was added beside
  `extract_text_from_pdf` rather than changing it; the plain-string contract
  of the original is preserved for downstream consumers.
- **Typed exception hierarchy.** All failure modes raise a subclass of
  `PDFConverterError` (`ExtractionError`, `SummarizationError`,
  `OutputWriteError`, `PDFMoveError`, …); the CLI catches the base class and
  exits with a message, so tracebacks never reach end users.
- **Lazy backend imports.** PDF backends are imported inside their strategy
  functions, so the heavy optional dependency (`docling`) costs nothing
  unless selected and produces a clear install hint when missing.

## Public API surface and compatibility

The load-bearing public contract, consumed by `adventure-library`:

- `extract_text_from_pdf(pdf_path, extractor_type="pypdf") -> str` — **the
  signature and plain-string return are frozen** unless the consumer is
  updated in the same coordinated change.
- `extract_pdf_with_metadata(pdf_path, extractor_type="pypdf") ->
  ExtractionResult` — text plus `page_offsets` (one character offset per
  source page; empty tuple when the backend does not preserve pages) and an
  `ExtractionQuality` record (`garble_score` and friends — signals for
  callers, deliberately not rejection rules).

The consumer pins this repo by git tag; there is no PyPI release. Changes to
these functions, `ExtractionResult`, or `ExtractionQuality` are
contract changes and need a coordinated downstream update.

## Extraction backends

| Backend | Output | Pages | Notes |
| --- | --- | --- | --- |
| `pypdf` | plain text | offsets preserved | default |
| `mupdf` | Markdown (`pymupdf4llm`) | not preserved (`()`) | |
| `docling` | Markdown with `<!-- page N -->` markers | offsets preserved | optional extra; OCR for scans, including picture-classified regions |

Adding a backend means: a strategy pair (plain + result), registry entries,
matching CLI choice (derived automatically), optional dependency wiring,
tests, and user documentation — in one change.

## Summarization and the services layer

`summarize_text_with_llm` builds the prompts and delegates to an `LLMService`
obtained from `LLMClientFactory`. `LLMService.summarize_text` retries
transient HTTP failures (429/503 with exponential backoff, other transport
errors with a flat delay), tracks token usage and estimated cost through
`UsageTracker`, and returns the response content. Provider-specific HTTP/SDK
detail stays inside `services/llm_providers.py` — never in the CLI or
summarizer.

`UsageTracker` writes `usage_stats.json` to the platform user-state directory
(via `platformdirs`) — never into the repository.

Provider API keys come from environment variables only; the provider is
chosen by CLI flag, then `LLM_PROVIDER` env var, then the `gemini` default.

## CLI

`pdf-converter <pdf_path> [storage_dir] [--mode summarize|extract]
[--extractor ...] [--provider ...]`. The CLI extracts, optionally summarizes,
writes `<name>_summary.md` or `<name>_extracted.md` to the working directory,
and — when `storage_dir` is given — moves the source PDF there.
`convert-folder.sh` batches the CLI over a folder.

## Configuration

There is no config file. Configuration is CLI flags plus environment
variables (`LLM_PROVIDER`, per-provider API key variables). Usage accounting
state lives in the platform user-state directory.

## Build system and toolchain

`make` targets are the canonical developer interface:

- `make check` — lock-file consistency, pre-commit (ruff lint + format), ty,
  deptry.
- `make test` — pytest with branch coverage.
- `make docs-test` — strict MkDocs build.
- `make build` — wheel via `pyproject-build`.

CI runs `make check` and the test/typing matrix on every push.

## Error-handling strategy

Backend and provider errors are caught at the layer boundary and re-raised as
the appropriate `PDFConverterError` subclass with a human-readable message,
chaining the original (`raise ... from error`). The CLI is the only place
that terminates the process.

## Testing strategy

Unit tests only, one test module per source module. Filesystem, PDF backends,
and all LLM network calls are mocked — **no real LLM requests in tests,
ever**. Coverage runs with branch measurement over `src`; tox exercises the
3.10–3.13 matrix for compatibility-sensitive changes. See
`4-unit-tests/TESTING.md` for recipes and conventions.

## Security and privacy

- API keys live in environment variables only — never in source, fixtures,
  output, or commits.
- PDFs and generated Markdown are treated as potentially private: no real
  personal documents as fixtures, ad-hoc outputs written outside the
  repository, and `git status` checked before staging (the repo has
  previously accumulated extracted personal documents).

## Conclusion

The codebase is small and deliberately layered: registries and protocols make
the two variable axes (extraction backend, LLM provider) pluggable, DI keeps
everything testable offline, and the one frozen contract —
`extract_text_from_pdf` — anchors the cross-repo relationship with
`adventure-library`. New work should extend the registries and preserve that
contract.
