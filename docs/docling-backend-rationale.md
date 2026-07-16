# Why pdf-converter is gaining a Docling backend

**Date:** 2026-07-16. **Audience:** the agent (or human) analysing/refactoring
this repo. **Requested change:** add a `docling` extraction strategy, publish
it behind an optional `[docling]` extra, and tag `v0.1.0`. This document is the
*why*, with the measurements that motivate it, so refactoring decisions can be
made against evidence rather than guesses. Full measurement detail lives in the
consumer repo: `adventure-library/docs/rfc-tool-driven-reuse-index.md`
(and its design decision 27 in `docs/design.md` §15).

## The consumer context

`adventure-library` (this package's only known consumer, via its optional
`pdf-extraction` extra) extracts tabletop RPG adventure PDFs to markdown, then
runs LLM analysis over the artifact. Its corpus of 84 PDFs was extracted with
this package's **pypdf default strategy**, and on 2026-07-15/16 that output was
measured systematically. The findings below are about *this repo's current
behavior*; they are what the refactor should act on.

## Measured findings about the current strategies

1. **`pypdf` (the default): complete but structureless.** On a clean digital
   PDF it recovers the full text (~28.6k of ~28.6k chars) but linearises it —
   no heading hierarchy, no tables, and naive reading order that **interleaves
   two-column pages sentence-by-sentence**. A reference table in one corpus
   document came out scrambled beyond use; this is a general multi-column
   property, not a scan artifact.
2. **`pymupdf4llm` (the alternative strategy): unreliable — dropped 92% of a
   clean document** (2,239 of 28,607 chars, "Bad Light.pdf", 8 pages, full
   text layer). It is not the default and nothing depends on it; it is a
   candidate for removal rather than repair.
3. **No OCR stage exists.** Two corpus PDFs are pure scans (0 text chars/page).
   One extracted to 1,431 bytes of garbage — a whole adventure lost. The
   package silently emits the garbage; nothing flags it.
4. **`calculate_extraction_quality`'s `garble_score` does not detect the
   failure it names**: 0.000 on the garbage extraction above (corpus max
   0.011). `alphabetic_character_ratio` *does* separate extraction failures
   (0.47 for the broken doc vs 0.83–0.95 corpus-wide) — but note it measures
   the *text layer*, not the document: a pristine scan with no text layer
   scores catastrophically while the document itself is perfectly legible.
5. **`summarizer.py` does not handle large inputs** (drops the whole text into
   one prompt — no chunking, no cap) **and runs on a different provider stack**
   (`LLMClientFactory`, API keys via env, Gemini default) than the consumer
   uses (subscription `claude -p`). The consumer does not call it. Candidate
   for removal or a clearly-scoped rework.

## What Docling was measured to do (2026-07-16, evaluated head-to-head)

- **Clean digital PDF:** full text (28,987 vs pypdf's 28,607 chars) **plus**
  19 headings and 18 reconstructed tables in correct reading order.
- **Text-layer scan:** rebuilt the exact two-column reference table that pypdf
  scrambled, in correct row order.
- **Pure scan (0 text/page):** built-in OCR (RapidOCR) recovered ~19k words
  and every named entity — same recall as OCRmyPDF/Tesseract, but with correct
  column reading order and cleaner proper nouns, where Tesseract interleaved
  columns into incoherence.
- **Page provenance:** Docling's document model carries `page_no` per element
  (`iterate_items()`); the consumer needs these emitted as `<!-- page N -->`
  markers in the markdown, which `export_to_markdown` alone drops.
- Local, deterministic, free; ~200s/doc on CPU (CUDA optional). Heavy
  dependency (~5GB torch stack) — hence the **optional `[docling]` extra**, so
  the base package stays light.

In short: Docling collapses this package's whole problem space — structure,
reading order, tables, OCR, page numbers — into one strategy, and does so
better than the existing strategies on every axis measured.

## Contracts the refactor must preserve

- `extract_text_from_pdf(pdf_path, extractor_type=...)` and the additive
  `extract_pdf_with_metadata(...)` keep their documented plain-text and
  metadata contracts — the consumer pins by git tag and imports lazily.
- The `docling` strategy slots into `EXTRACTION_STRATEGIES` like the others;
  selecting it must not be required (default stays as-is until the consumer
  bumps its pin and opts in explicitly).
- Quality metrics stay additive: the consumer now derives its authoritative
  quality signal downstream (an LLM analysis-time verdict), so
  `calculate_extraction_quality` needs no rework here — but if touched, note
  finding 4 above.

## Latitude the refactoring agent has

Findings 2 and 5 are removal candidates (verify no external consumers first —
the GitHub repo is public). Finding 4 is documentation-level (docstring should
say what each metric actually detects). The docling backend itself is the one
*addition*: strategy + page markers + `[docling]` extra + `v0.1.0` tag.
