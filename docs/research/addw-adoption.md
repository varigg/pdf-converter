# Research: What does adopting ADDW in this repo entail?

- **Ticket**: [#6](https://github.com/varigg/pdf-converter/issues/6) (part of map [#4](https://github.com/varigg/pdf-converter/issues/4))
- **Date**: 2026-08-26
- **Sources**: [varigg/agent-driven-development](https://github.com/varigg/agent-driven-development) at HEAD `2943b4f` (v0.2.0, schema 7) — README, `CLAUDE.md`, `CONTEXT.md`, `UPGRADING.md`, `docs/cycle-walkthrough.md`, all 9 ADRs, every `SKILL.md` and lib script; the existing adopter `adventure-library` (local checkout, schema 6 install); this repo's `AGENTS.md` and `docs/agents/*`.

## 1. What ADDW is

**ADDW ("agent-driven development workflow") is an overlay on mattpocock/skills, not a standalone tool** (ADDW `README.md`). Matt's skills own the front of the flow — alignment (`grill-with-docs`), spec (`to-spec`), decomposition (`to-tickets`) — and ADDW owns getting a change safely onto `main`: cross-model review, a deterministic gate, one PR per ticket, mechanical release. The cycle:

```
grill-with-docs → to-spec → /codex-spec-review → to-tickets
  → /addw-implement (one ticket → one open PR; human merges) → /addw-release
```

Satellites: `/addw-maintain` (periodic audit), `/addw-hotfix`, `/addw-compact`, `/codex-ask`.

Three governing principles (ADDW's ADRs 0004–0006):

- **The PR boundary** (ADR 0005): the PR merge is the flow's single irreversibility boundary and only approval gate. Upstream of it agents own the work; past it a human gates every landing — no direct-push path to `main`, emergencies included. Notably for the cross-repo pair: *"no agent filing carries `ready-for-agent` unless a human act explicitly named that work."*
- **One Deliverable per ticket** (ADR 0006): a bundled ticket found at pickup is not started — reported for rescoping.
- **Determinism where scriptable** (ADR 0004): shared shell scripts under `.claude/skills/lib/` replace agent judgment for tracker queries, the test gate, release derivation, doc archival. Explicitly **no git hooks and no CI are installed by ADDW**.

Work state lives on the GitHub tracker, never in the tree — no plan documents, no backlog file (`docs/backlog.md` present is a doctor **FAIL**). "What's next" is answered deterministically by `bash .claude/skills/lib/tracker/tracker.sh frontier`: open issues labeled `ready-for-agent`, not labeled `spec`/`backlog`, with every `## Blocked by` blocker closed **as completed**.

The ADDW repo *is* the product: adoption means copying its `skills/` directory wholesale into the consumer's `.claude/skills/`. Skills are byte-identical in every install; all project-specific values live in one config file, `docs/addw.env`. `.claude/skills/addw-init/scripts/doctor.sh` is the machine-readable adoption contract — it ends `HEALTHY` or `UNHEALTHY`.

## 2. What adoption mechanically requires (the doctor contract)

### Prerequisites

- mattpocock/skills installed with `setup-matt-pocock-skills` already run — **done here** (this is the just-completed configuration).
- Authenticated `gh`, GitHub repo with issues enabled — done.
- **Codex CLI** on the machine, *if* the default `codex-implement`/`codex-code-review` role adapters are kept. The reserved value `ADDW_IMPLEMENT_SKILL=inline` lets the main agent drive `tdd` itself instead — an adoption-time decision.
- bash ≥ 4, `jq`, `sha256sum`, `base64` for the lib scripts.

### Files and directories (exact paths, doctor-checked unless noted)

| Artifact | Status in pdf-converter |
|---|---|
| `.claude/skills/` = wholesale copy of ADDW `skills/` (six `addw-*` skills, four `codex-*` adapters, `lib/` script layer, `lib/templates/adr.md`) | **Missing** |
| `docs/addw.env` (schema 7) | **Missing** |
| `docs/ARCHITECTURE.md` (as-built, authoritative) + `docs/ARCHITECTURE-rules.md` | **Missing** |
| `docs/charter.md` (fixed headings: Purpose / Product Principles / Scope / Non-Goals / Success Criteria) | **Missing** |
| `docs/4-unit-tests/TESTING.md` — must contain a `Verification Recipes` section and an Integration/E2E `Impact Rules` section | **Missing** |
| `CHANGELOG.md` (write-only; release script prepends) | **Missing** |
| ADR directory (`ADDW_ADR_DIR`, conventionally `docs/adr/`) | **Missing** (declared lazily-created in `docs/agents/domain.md`, doesn't exist yet) |
| One line in `AGENTS.md`: `` `.claude/skills/lib/templates/adr.md` is the authoritative ADR format for this project. `` — backticked path + the word "authoritative" on one line; goes in whichever file Matt's setup chose (here **AGENTS.md**), never the other one | **Missing** |
| `docs/agents/issue-tracker.md` with first heading exactly `# Issue tracker: GitHub` | **Present** ✓ |
| `docs/agents/domain.md` (skills resolve ADR/glossary paths from it, never hardcode) | **Present** ✓ |
| `docs/agents/triage-labels.md` | **Present** ✓ |
| `docs/glossary.md` (named by adventure-library's `domain.md` as the glossary; here `CONTEXT.md` fills that role lazily) | Not required by doctor; decide at init |

`addw-init` generates the missing docs interactively (it interviews for charter/architecture content) and ends by running `doctor.sh` to `HEALTHY`, committing `chore: initialize the ADDW workflow`.

### GitHub labels

Doctor requires exactly three: `ready-for-agent`, `spec`, `backlog`.

- `ready-for-agent` — **already exists** ✓ (Matt's label; ADDW never creates, modifies, or renames it — the frontier query keys on the exact string).
- `spec`, `backlog` — **missing**; created via `bash .claude/skills/lib/tracker/tracker.sh create-label <label>`.
- `archived` (+ `adr`/`proposal`) are created lazily by `archive-doc.sh` on first doc retirement — nothing to do now.
- Side observation: this repo has `wayfinder:map/research/grilling/task` but **not `wayfinder:prototype`** (adventure-library has all five). Unrelated to ADDW but worth one `gh label create`.

### `docs/addw.env` — concrete values for this repo

The file is data, never sourced (strict `KEY=value` grammar, one shared reader). Proposed values, derived from the Makefile and adventure-library's working install:

```
ADDW_SCHEMA=7
ADDW_PROJECT_NAME="pdf-converter"
ADDW_VERSION_FILE="pyproject.toml"
ADDW_MAIN_BRANCH="main"
ADDW_AUDIT_NUDGE_N=5
ADDW_ADR_DIR="docs/adr"
ADDW_ADR_TEMPLATE=".claude/skills/lib/templates/adr.md"
ADDW_RECIPE_LINT="uv run ruff check . && uv run ruff format --check ."
ADDW_RECIPE_TYPECHECK="uv run ty check"
ADDW_RECIPE_TESTS_AFFECTED="uv run pytest {paths}"
ADDW_RECIPE_LOCKFILE_SYNC="uv lock"
ADDW_LOCKFILE="uv.lock"
# ADDW_IMPLEMENT_SKILL / ADDW_CODE_REVIEW_SKILL: default codex-*; "inline" is the no-Codex option
```

Notes: the gate has exactly three rungs (lint, typecheck, tests) emitting one verbatim summary line for the PR body; this repo actually has a richer `make check` (lock check, pre-commit, ty, deptry) and `make docs-test` — those stay available to agents but only the three recipes gate. `ADDW_RECIPE_TYPECHECK="uv run ty check"` is a genuine improvement over adventure-library, which leaves typecheck empty. `ADDW_MAIN_BRANCH` must be the bare name (`main`), not remote-qualified.

### Conventions the repo inherits

- Branch names `<type>/<issue-number>-<slug>`; **PR titles must parse as conventional-commit subjects** (the squash subject is what the changelog derives from); staging always by explicit path, never `git add -A`.
- Issue-body encoding is the tracker contract: `## Parent` and `## Blocked by` level-2 sections with `#N` refs in list items; close reason is load-bearing (*completed* unlocks dependents, *not planned* never does). No `.github/ISSUE_TEMPLATE/` files — the "template" is `to-tickets` output.
- PR body contract (7 elements): `Closes #N`, verbatim gate line, codex verdict + SHA + ticket-body hash, disclosures, doc-impact note, what changed, merge recommendation (squash by default).
- ADRs are write-once from the merge boundary, per the ADDW template: mandatory **Status**/**Date**/**Origin**, Status exactly `active | superseded by ADR-NNNN`, `## Gate` section for guardrail decisions.

## 3. What already exists here

The `setup-matt-pocock-skills` layer — ADDW's declared prerequisite — is fully in place and doctor-compatible as-is:

- `docs/agents/issue-tracker.md` with the exact `# Issue tracker: GitHub` heading, `gh` conventions, PRs-as-request-surface flag (`no`), and the full Wayfinding operations section (map/child/blocking/frontier/claim/resolve) — near-identical to adventure-library's, including the native-issue-dependencies blocking mechanic.
- `docs/agents/triage-labels.md` with all five roles mapped identity (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`) — same choice adventure-library made.
- `docs/agents/domain.md` declaring single-context, lazy `CONTEXT.md` + `docs/adr/`.
- All five triage labels plus four `wayfinder:*` labels live on GitHub.
- `AGENTS.md` (this repo's chosen agent-instructions file — adventure-library chose `CLAUDE.md`; ADDW supports either).
- Toolchain that maps cleanly onto the gate: uv, ruff, ty, pytest, committed `uv.lock`.

## 4. What's missing

Everything ADDW-specific: the `.claude/skills/` copy, `docs/addw.env`, the doctor-checked doc set (`ARCHITECTURE.md`, `ARCHITECTURE-rules.md`, `charter.md`, `docs/4-unit-tests/TESTING.md`, `CHANGELOG.md`), `docs/adr/` with the ADR-template declaration line in `AGENTS.md`, and the `spec` + `backlog` labels. See the checklist in §7.

## 5. Conflicts and frictions

1. **ADR format: ADDW template vs `/domain-modeling`.** `docs/agents/domain.md` expects ADRs created lazily by `/domain-modeling` (whose statuses are proposed/accepted/deprecated). ADDW's `lib/templates/adr.md` mandates a two-state `active | superseded by ADR-NNNN` status plus Origin and Gate fields, and doctor greps for the "authoritative" declaration line. adventure-library resolved this by declaring the ADDW template authoritative in its CLAUDE.md; the same one-line resolution works here (in `AGENTS.md`), and `docs/agents/domain.md` needs no edit — it only points at the directory.
2. **`TASKS.md` vs "work state lives on the tracker".** `AGENTS.md` names `TASKS.md` "the authoritative handoff for outstanding product and publishing work." ADDW's posture is that work state never lives in the tree (`docs/backlog.md` by that exact name is a doctor FAIL; `TASKS.md` isn't name-checked, so it won't fail doctor, but it is the same anti-pattern). Adoption should migrate its open items to tracker issues and demote or retire the file — `archive-doc.sh` exists for exactly this once the skills are installed.
3. **`docs/` doubles as the MkDocs source tree with a strict build** (`make docs-test` = `mkdocs build -s`). ADDW's doc set lands inside it. Pages absent from `nav` are only INFO-level (precedent: `docs/docling-backend-rationale.md`, `docs/agents/*` already pass), but any broken relative link in the new docs will fail the strict build. Low risk, worth a `make docs-test` run at init.
4. **Schema drift against the existing adopter.** adventure-library runs `ADDW_SCHEMA=6`; ADDW HEAD expects `=7`. Adopt by copying from the **ADDW repo at HEAD**, not from adventure-library's `.claude/skills/` — pdf-converter would then briefly be the newer install of the pair. (Upgrading adventure-library is its own repo's business.)
5. **Codex CLI dependency.** The default role adapters shell out to Codex in a sandbox. Decision at init: keep the cross-model review posture (install/verify Codex CLI on this machine) or set `ADDW_IMPLEMENT_SKILL=inline`.
6. **No conflict on labels or tracker conventions.** The just-configured mattpocock conventions are exactly what ADDW builds on: `ready-for-agent` is shared and untouched, `wayfinder:*` never enters ADDW's frontier, unparented tickets are workable. The two systems were designed to share one tracker.

## 6. The cross-repo pair: what "dependency-side" actually means

ADDW has **no formal dependency-side/consumer-side role model** — every skill operates on the cwd repo, and nothing files issues across repos programmatically. The cross-repo relationship is carried entirely by the shared tracker conventions:

- adventure-library agents (or humans) file issues against `varigg/pdf-converter` with ordinary `gh -R varigg/pdf-converter issue create`. Per ADDW's ADR 0005 gate, an agent filing must **not** carry `ready-for-agent` — incoming filings land as `needs-triage` or `backlog` and a human graduates them into this repo's frontier.
- This repo's `/addw-implement` sessions then pick them up from the frontier like any local ticket; the existing API contract note in `AGENTS.md` (preserve `extract_text_from_pdf`'s signature) is exactly the kind of constraint the spec/ADR layer is for.
- Provenance flows back via ADR `Origin:` lines using GitHub's `owner/repo#N` cross-repo reference form (adventure-library's ADRs already cite `varigg/agent-driven-development#83` this way).
- Process findings (a skill itself is wrong) are filed against varigg/agent-driven-development, per `addw-maintain`.

So "adopting as the dependency-side half" = plain ADDW adoption + a triage discipline for externally-filed issues; no extra scaffolding exists to install.

## 7. Setup checklist (cut the task ticket from this)

1. Copy `skills/` from varigg/agent-driven-development @ HEAD (v0.2.0, schema 7) into `.claude/skills/` wholesale (includes `lib/` and `lib/templates/adr.md`).
2. Run `/addw-init` (its Step 0 verifies the Matt-setup artifacts — already present). It will:
   - resolve `ADDW_ADR_DIR=docs/adr` from `docs/agents/domain.md` and create `docs/adr/` and `docs/4-unit-tests/`;
   - generate `docs/addw.env` with the values in §2 (schema 7; uv/ruff/ty/pytest recipes; `uv.lock` pair);
   - generate `docs/charter.md`, `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE-rules.md`, `docs/4-unit-tests/TESTING.md` (with `Verification Recipes` + `Impact Rules` sections), `CHANGELOG.md`;
   - add to `AGENTS.md` (not a CLAUDE.md): `` `.claude/skills/lib/templates/adr.md` is the authoritative ADR format for this project. ``
3. Create labels `spec` and `backlog` via `bash .claude/skills/lib/tracker/tracker.sh create-label <label>` (leave `ready-for-agent` untouched). Optionally add the missing `wayfinder:prototype`.
4. Decide the implement/review adapter: verify Codex CLI works on this machine, or set `ADDW_IMPLEMENT_SKILL=inline` in `docs/addw.env`.
5. Migrate `TASKS.md`'s remaining open items to GitHub issues (`backlog` unless a human graduates them) and retire/demote the file; update the `AGENTS.md` sentence that calls it authoritative.
6. Run `make docs-test` to confirm the new docs don't break the strict MkDocs build.
7. Run `bash .claude/skills/addw-init/scripts/doctor.sh` to `HEALTHY: all checks passed`; commit `chore: initialize the ADDW workflow`.
8. Agree the pair discipline with adventure-library: its filings against this repo arrive as `needs-triage`/`backlog`, never `ready-for-agent`; graduation is a human act here.
