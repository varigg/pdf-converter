# Contributor guide for agents

## Project purpose

`pdf-converter` is a Python 3.10+ command-line package for turning PDFs into
Markdown-compatible text. The installed entry point is `pdf-converter`, which calls
`pdf_converter.converter:main`.

Work state lives on the issue tracker (see "Agent skills" below), never in
tree files; check the tracker before taking on feature work. In particular,
`adventure-library` consumes
`pdf_converter.extractor.extract_text_from_pdf`, so preserve that callable's
signature and plain-string return contract unless the downstream consumer is
updated in the same coordinated change.

## Layout

- `src/pdf_converter/extractor.py` — extraction strategies and the public
  extraction convenience function.
- `src/pdf_converter/converter.py` — CLI argument parsing, output writing,
  and optional movement of source PDFs.
- `tests/` — pytest unit tests; use mocks for filesystem and PDF backends.
- `docs/` and `mkdocs.yml` — MkDocs site.

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
- Treat PDFs and generated Markdown as potentially private. Do not add real
  personal PDFs or their extracted contents as fixtures. Prefer synthetic
  data and write ad-hoc outputs outside the repository.
- `run_conversion` can move an input PDF when given `storage_dir`. Tests and
  manual checks should avoid passing real files or use a temporary directory.

## Change hygiene

The supported extraction backends are `pypdf`, `docling`, and `docling-ocr`. Keep the Python
registry, CLI, batch script, dependencies, tests, and documentation aligned
when adding or removing a backend.

Keep changes narrow and avoid unrelated cleanup. After changes, run the
smallest relevant tests, then the broader checks that can run in the current
baseline. Report any pre-existing failures separately. Check `git status`
before staging: this project has previously accumulated generated output from
real documents.

## Agent skills

### Issue tracker

Issues live in this repo's GitHub Issues (`varigg/pdf-converter`), operated
via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage labels are used verbatim: `needs-triage`,
`needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See
`docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` and `docs/adr/` at the repo root (created
lazily by `/domain-modeling`). See `docs/agents/domain.md`.

### ADR format

`.claude/skills/lib/templates/adr.md` is the authoritative ADR format for this project.

## Documentation and releases

Update `README.md` and `docs/` when a user-visible CLI option, extractor,
output format, or public API changes. The repository and GitHub
release tag are live; documentation remains in the repository rather than
being deployed to GitHub Pages. Verify CI for every pushed change and create a
new tag only for an intentional release.
