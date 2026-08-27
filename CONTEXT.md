# PDF Extraction

Standalone library that turns PDFs into Markdown with metadata and quality
signals, consumed by adventure-library; it also serves as the dependency-side
testbed of the ADDW cross-repo pair.

## Language

**Extraction**:
Turning a PDF into Markdown text plus metadata and quality signals. The
repo's sole capability.
_Avoid_: conversion, summarization, mode

**Strategy**:
A named, selectable extraction backend (`pypdf`, `docling`).
_Avoid_: mode, engine, library

**Quality signals**:
Per-extraction measurements attached to the result (e.g. the garble verdict)
that let a consumer judge whether the extracted text is trustworthy.
_Avoid_: confidence, score
