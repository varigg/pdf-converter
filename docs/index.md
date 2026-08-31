# pdf-converter

[![Release](https://img.shields.io/github/v/release/varigg/pdf-converter)](https://img.shields.io/github/v/release/varigg/pdf-converter)
[![Build status](https://img.shields.io/github/actions/workflow/status/varigg/pdf-converter/main.yml?branch=main)](https://github.com/varigg/pdf-converter/actions/workflows/main.yml?query=branch%3Amain)
[![Commit activity](https://img.shields.io/github/commit-activity/m/varigg/pdf-converter)](https://img.shields.io/github/commit-activity/m/varigg/pdf-converter)
[![License](https://img.shields.io/github/license/varigg/pdf-converter)](https://img.shields.io/github/license/varigg/pdf-converter)

`pdf-converter` extracts PDF text to Markdown-compatible output. It supports
the `pypdf`, MuPDF, and optional Docling extraction backends, plus a Python
metadata API for page offsets and extraction-quality signals.

## Quick start

Extract a PDF:

```sh
uv run pdf-converter report.pdf --extractor pypdf
```

The command writes `<filename>_extracted.md` in the working directory.
Supplying an optional second positional argument moves the source PDF there
after processing.

## Installation

Install the standard package with your preferred package manager. For a local
development checkout, use [uv](https://docs.astral.sh/uv/):

```sh
uv sync
```

Docling is optional because its local OCR and layout-model stack is large:

```sh
pip install 'pdf-converter[docling]'
```

## Extraction backends

| Backend | Intended use | Page provenance |
| --- | --- | --- |
| `pypdf` | Fast, lightweight plain-text extraction; the default. | One offset per source page. |
| `mupdf` | Markdown-oriented extraction. | Not preserved by this API. |
| `docling` | Structured Markdown, tables, multi-column documents, and scans with OCR. | `<!-- page N -->` marker and offset for every page, including empty pages. |

Use an extractor from the command line with `--extractor`; `pypdf` remains the
default. Docling also includes OCR text nested in picture-classified regions.

## Python API

Use `extract_text_from_pdf` when only the extracted string is needed:

```python
from pdf_converter.extractor import extract_text_from_pdf

text = extract_text_from_pdf("report.pdf", extractor_type="pypdf")
```

Use `extract_pdf_with_metadata` when a pipeline needs page attribution or
quality signals:

```python
from pdf_converter.extractor import extract_pdf_with_metadata

result = extract_pdf_with_metadata("report.pdf", extractor_type="docling")
first_page_offset = result.page_offsets[0]
```

`ExtractionResult.quality` includes character count, alphabetic-character
ratio, suspicious-token count, and a conservative garble signal. These are
review aids, not a guarantee that the source document is readable.

## Development

```sh
make test
make check
make docs-test
```

The [module reference](modules.md) documents the public modules. The
repository [README](https://github.com/varigg/pdf-converter#readme) is the
compact command-line and library guide.
