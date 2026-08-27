# Retire the summarizer

Status: accepted (2026-08-27, [#5](https://github.com/varigg/pdf-converter/issues/5))

pdf-converter's role is locked as a standalone, extraction-focused library on a
demand-driven scope policy ([#4](https://github.com/varigg/pdf-converter/issues/4)).
The summarize path had no callers — the only consumer, adventure-library,
imports `pdf_converter.extractor` and nothing else — so we retire it entirely
rather than keep or rework it: `summarizer.py`, the whole `services/` provider
stack (factory, Gemini/Perplexity/OpenAI/Anthropic clients, retry/backoff,
UsageTracker), the `--mode` and `--provider` CLI flags, the four provider
API-key env vars plus `LLM_PROVIDER`, and the dependencies used only by that
stack (`requests`, `google-genai`, `platformdirs`). The unreliable `mupdf`
extraction strategy (dropped 92% of a clean document; see
`docs/docling-backend-rationale.md`) and its `pymupdf4llm` dependency are
bundled into the same removal, leaving `pypdf` (default) and `docling`
(optional extra) as the two strategies.

## Considered Options

- **Keep as-is** — rejected: pays maintenance tax on speculation, which the
  demand-driven scope policy exists to refuse. The implementation was also
  known-flawed (whole document into one prompt, no chunking or cap) and its
  provider stack had diverged from how the maintainer runs LLMs today.
- **Rework as a thin prompt-level feature** — rejected for the same reason,
  and because the capability is now trivially available outside the repo:
  feed the extracted Markdown to any LLM.

## Consequences

- The removal is one breaking release (`v0.2.0`). The consumer pins `v0.1.0`
  by git tag and is unaffected until it chooses to bump.
- If summarization ever regains value, it returns only on demand (a real
  issue filed from a consumer) and is built fresh against the then-current
  LLM stack with chunking and input caps — nothing from the retired
  implementation is worth resurrecting beyond this record.
