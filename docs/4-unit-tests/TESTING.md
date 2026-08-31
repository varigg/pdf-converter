# Testing Guide

## Framework and layout

Tests are **pytest** unit tests under `tests/`, one `test_<module>.py` per
source module (`tests/test_extractor.py` covers
`src/pdf_converter/extractor.py`, and so on). There is no integration or E2E
suite; the tox matrix (Python 3.10–3.13, via `tox-uv`) stands in for
environment coverage on compatibility-sensitive changes.

## Writing conventions

- **Everything external is mocked**: filesystem effects and PDF backend
  libraries. No real personal PDF (or its extracted text) is committed as a
  fixture — use synthetic data.
- Exercise the seams the code exposes for testing: inject strategies into
  `PDFExtractor` and drive the CLI through `main(argv)`.
- Assertions on error paths expect the typed `PDFConverterError` subclasses,
  not bare exceptions.
- `assert` statements are fine (ruff's S101 is ignored for `tests/*`).

## Coverage expectations

Coverage runs with **branch measurement** over `src` (configured in
`pyproject.toml`) and uploads to Codecov from CI. New or changed code ships
with tests for its behavior and its error paths; a change that lowers
coverage needs a stated reason.

## Verification Recipes

The single source of truth for verification commands — skills and agents
point here and carry none themselves.

| Purpose | Command |
| --- | --- |
| Lint + format check | `uv run ruff check . && uv run ruff format --check .` |
| Type check | `uv run ty check` |
| All tests | `uv run python -m pytest` |
| Affected tests | `uv run pytest {paths}` |
| Single test | `uv run pytest tests/test_<module>.py -q` |
| Coverage | `make test` (pytest with branch coverage + XML report) |
| Full local gate | `make check` (lock check, pre-commit, ty, deptry) |
| Docs build | `make docs-test` (strict MkDocs build) |
| Version matrix | `uv run tox` (Python 3.10–3.13) |

`make check` is broader than the three-rung ADDW gate (it adds the lock-file
check, pre-commit hooks, and deptry); it remains the pre-push bar for humans
and agents alike.

## Integration / E2E Impact Rules

There is no heavier suite today, so these rules name when the *matrix* and
*docs* checks must run beyond the default gate:

- **Run `uv run tox`** when a change touches Python-version-sensitive code:
  syntax or typing features, dependency version bounds, or anything in
  `pyproject.toml`'s `requires-python` neighborhood.
- **Run `make docs-test`** when a change adds or renames documentation pages,
  changes public docstrings surfaced by mkdocstrings, or edits `mkdocs.yml`.
- **Docs-only changes** (Markdown outside `src/`) skip the test gate but
  still run `make docs-test`.
- **Contract changes** to `extract_text_from_pdf`, `ExtractionResult`, or
  `ExtractionQuality` require a coordinated adventure-library update — flag
  them; no local suite can cover the consumer.
