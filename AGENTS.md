# Contributor guide for agents

## Project purpose

`pdf-converter` is a Python 3.10+ command-line package for turning PDFs into
Markdown-compatible text and, optionally, producing LLM summaries. The
installed entry point is `pdf-converter`, which calls
`pdf_converter.converter:main`.

This repository is newly initialized. `TASKS.md` is the authoritative
handoff for outstanding product and publishing work; read it before taking on
feature work. In particular, `adventure-library` consumes
`pdf_converter.extractor.extract_text_from_pdf`, so preserve that callable's
signature and plain-string return contract unless the downstream consumer is
updated in the same coordinated change.

## Layout

- `src/pdf_converter/extractor.py` — extraction strategies and the public
  extraction convenience function.
- `src/pdf_converter/converter.py` — CLI argument parsing, output writing,
  and optional movement of source PDFs.
- `src/pdf_converter/summarizer.py` — prompt construction and LLM service
  orchestration.
- `src/pdf_converter/services/` — provider clients, retries, and local usage
  accounting. Keep provider-specific HTTP/SDK details here rather than in the
  CLI or summarizer.
- `tests/` — pytest unit tests; use mocks for filesystem, PDF backends, and
  all networked LLM calls.
- `docs/` and `mkdocs.yml` — MkDocs site.
- `TASKS.md` — current handoff, known dependencies, and safety context.

## Setup and common commands

Use `uv`; `uv.lock` is committed and should stay synchronized with
`pyproject.toml`.

```bash
uv sync
make test                 # pytest with branch coverage
make check                # lock check, pre-commit, ty, and deptry
make docs-test            # strict MkDocs build
make build                # create a wheel in dist/
```

For a fast targeted test, run:

```bash
uv run python -m pytest tests/test_extractor.py -q
```

`pre-commit` runs Ruff linting and formatting and may modify files. Inspect
the resulting diff before including it in a change. Tox defines the Python
3.10–3.13 matrix; use it when changing compatibility-sensitive code.

## Implementation conventions

- Use the `src/` package layout and keep imports package-relative inside the
  package where appropriate.
- Add type annotations to new or changed public functions. Target Python 3.10;
  use built-in generics such as `list[str]` and unions such as `T | None`.
- Ruff is configured for a 120-character line length and a broad lint rule
  set. Follow existing formatting and let Ruff format Python files.
- Keep extraction backends behind an `ExtractionStrategy` and select them in
  `get_extractor`; add matching CLI choices, dependencies, tests, and user
  documentation together.
- Keep API keys out of source, test fixtures, command output, and committed
  files. Providers obtain keys from environment variables. Never perform real
  LLM requests in tests.
- `UsageTracker` writes `usage_stats.json` to the platform user-state
  directory. Do not redirect it into the repository or add usage data to
  commits.
- Treat PDFs and generated Markdown as potentially private. Do not add real
  personal PDFs or their extracted contents as fixtures. Prefer synthetic
  data and write ad-hoc outputs outside the repository.
- `run_conversion` can move an input PDF when given `storage_dir`. Tests and
  manual checks should avoid passing real files or use a temporary directory.

## Change hygiene

The supported extraction backends are `pypdf` and `mupdf`. Keep the Python
registry, CLI, batch script, dependencies, tests, and documentation aligned
when adding or removing a backend. The supported providers are defined by the
registry in `services/llm_client_factory.py`; derive Python-facing choices
from that registry rather than copying the list.

Keep changes narrow and avoid unrelated cleanup. After changes, run the
smallest relevant tests, then the broader checks that can run in the current
baseline. Report any pre-existing failures separately. Check `git status`
before staging: this project has previously accumulated generated output from
real documents.

## Documentation and releases

Update `README.md` and `docs/` when a user-visible CLI option, extractor,
provider, output format, or public API changes. The repository and GitHub
Pages URLs in metadata are aspirational until publishing work in `TASKS.md`
is completed; do not assume remote CI or releases exist.
