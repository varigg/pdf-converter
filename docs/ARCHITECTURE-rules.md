# Maintaining ARCHITECTURE.md

`ARCHITECTURE.md` is an as-built document. Keep it true by these rules:

- **Update it after any change to** project structure, the technology stack,
  data flow, component interactions (the extraction registries, the CLI
  orchestration), or the build system and toolchain.
- **Rewrite, never append.** Restate the affected passage as the system now
  stands and delete descriptions of machinery that no longer exists — the
  document has no "history" sections. When a component is retired, its
  sections are rewritten or removed, not annotated.
- **Be factual and concise.** Describe what is, not what is planned; plans
  live on the issue tracker.
- **Keep the tables current.** The extraction-backend table and the public
  API section must match the registries in `extractor.py` — those registries
  are the authority.
- **Reference real paths** (`src/pdf_converter/...`), so a reader can jump
  from prose to code.
- **Version numbers stay out** unless they are live facts a reader must act
  on (such as a dependency pin). Release history belongs in `CHANGELOG.md`.
