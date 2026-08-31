# pdf-converter

`pdf-converter` extracts text from PDF files. It is useful both as a
command-line tool and as a small Python library.

## Requirements

- Python 3.10 or newer
- The `docling` backend downloads its layout models from Hugging Face on first
  use; afterwards it runs fully offline.

## Installation

Install the package with your preferred Python package manager. For local
development, [uv](https://docs.astral.sh/uv/) will create the environment and
install the project dependencies:

```sh
uv sync
```

Install the optional Docling backend, including its OCR engine, when you need
structured Markdown or extraction from scans:

```sh
pip install 'pdf-converter[docling]'
```

## Command-line usage

Extract text to Markdown:

```sh
uv run pdf-converter report.pdf --extractor pypdf
```

The optional second positional argument moves the source PDF to that directory
after it has been processed:

```sh
uv run pdf-converter report.pdf archive/
```

Output is written beside the command's working directory as
`<filename>_extracted.md`.

### Options

- `--extractor` / `-e`: `pypdf` (the default), `mupdf`, or `docling`.

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
MuPDF extraction remains useful for Markdown-oriented output, but currently
returns an empty page map because that backend does not preserve page
boundaries through this API.

The optional `docling` backend produces structured Markdown — heading hierarchy,
reconstructed tables, correct multi-column reading order — with a
`<!-- page N -->` comment marker at the start of every page, and recovers
scanned pages through built-in OCR. Its `page_offsets` point at each page's
marker, including empty pages. It is substantially heavier than the default
backends because it includes local models.

## Development

Run the local checks with:

```sh
make test
make check
make docs-test
```

Additional project documentation is maintained in the repository's
[`docs/`](docs/) directory.

## License

This project is distributed under the [MIT License](LICENSE).
