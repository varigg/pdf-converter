# pdf-converter

[![Release](https://img.shields.io/github/v/release/varigg/pdf-converter)](https://img.shields.io/github/v/release/varigg/pdf-converter)
[![Build status](https://img.shields.io/github/actions/workflow/status/varigg/pdf-converter/main.yml?branch=main)](https://github.com/varigg/pdf-converter/actions/workflows/main.yml?query=branch%3Amain)
[![Commit activity](https://img.shields.io/github/commit-activity/m/varigg/pdf-converter)](https://img.shields.io/github/commit-activity/m/varigg/pdf-converter)
[![License](https://img.shields.io/github/license/varigg/pdf-converter)](https://img.shields.io/github/license/varigg/pdf-converter)

`pdf-converter` extracts PDF text to Markdown-compatible output and can
optionally summarize that text with a supported LLM provider. It supports the
`pypdf` and MuPDF extraction backends, plus a Python metadata API for page
offsets and extraction-quality signals.

## Quick start

Extract a PDF without calling an LLM:

```sh
uv run pdf-converter report.pdf --mode extract --extractor pypdf
```

To summarize with Gemini, configure `GOOGLE_API_KEY` and omit `--mode extract`:

```sh
export GOOGLE_API_KEY=...
uv run pdf-converter report.pdf --provider gemini
```

See the repository [README](https://github.com/varigg/pdf-converter#readme)
for installation, all CLI options, Python API examples, and development
commands. The [module reference](modules.md) documents the public modules.
