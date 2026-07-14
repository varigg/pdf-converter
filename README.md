# pdf-converter

`pdf-converter` extracts text from PDF files and can optionally summarize that
text with a supported LLM provider. It is useful both as a command-line tool
and as a small Python library.

## Requirements

- Python 3.10 or newer
- An API key for the selected LLM provider when using summary mode

## Installation

Install the package with your preferred Python package manager. For local
development, [uv](https://docs.astral.sh/uv/) will create the environment and
install the project dependencies:

```sh
uv sync
```

## Command-line usage

Extract text to Markdown without calling an LLM:

```sh
uv run pdf-converter report.pdf --mode extract --extractor pypdf
```

Summarize a PDF with the default Gemini provider:

```sh
export GOOGLE_API_KEY=...
uv run pdf-converter report.pdf --provider gemini
```

The optional second positional argument moves the source PDF to that directory
after it has been processed:

```sh
uv run pdf-converter report.pdf archive/ --mode extract
```

Output is written beside the command's working directory as either
`<filename>_extracted.md` or `<filename>_summary.md`.

### Options

- `--mode` / `-m`: `summarize` (the default) or `extract`.
- `--extractor` / `-e`: `pypdf` (the default) or `mupdf`.
- `--provider` / `-p`: LLM provider for summary mode. If omitted, the value of
  `LLM_PROVIDER` is used, falling back to `gemini`.

## Python API

Use `extract_text_from_pdf` for a compact library interface:

```python
from pdf_converter.extractor import extract_text_from_pdf

text = extract_text_from_pdf("report.pdf", extractor_type="pypdf")
```

The function raises `pdf_converter.exceptions.ExtractionError` when the chosen
backend cannot read the PDF.

For ingestion pipelines that need provenance and quality signals, use
`extract_pdf_with_metadata`. With the `pypdf` backend, its `page_offsets`
maps each one-based PDF page number to the character offset where that page
starts. Its `quality` includes a garble score and related metrics; callers can
use `quality.is_likely_garbled` to route suspect documents for review or OCR.

## Development

Run the local checks with:

```sh
uv run pytest
uv run ty check
uv run ruff check .
uv run mkdocs build -s
```

Additional project documentation is maintained in the repository's
[`docs/`](docs/) directory.

## License

This project is distributed under the [MIT License](LICENSE).
