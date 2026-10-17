# Source-structure analysis — 2026-10-18

## Scope and method

Single bounded job: `gutenberg-36`, Gutenberg ID 36, stage `structure`, recorded
reasons `[]`. The supplied task restricts writes to books/gutenberg-36, forbids
GitHub credentials and pushing, and requires `./ctp validate`. No translation,
edition freeze, catalogue change or publication is part of this job.

AI-assisted analysis through the Codex agent interface. Exposed agent identity:
GPT-6; exact backend model snapshot unknown. No separately billed model API was
called. Reusable instructions: prompts/source-preparation.md and
prompts/structure-source.md, with AGENTS.md and the source-import/structure,
editorial, maintainer and local-source-automation documents. This note records
visible scope and references; it does not capture hidden instructions or all
conversation context. The trusted wrapper may append observed executor details.

Inspected the normalized source from provider header through the full trailing
license, and the numbered block record. Validated the original acquisition before
compiling a reference-only plan. `./ctp source-apply` copied source bodies and
allocated all node IDs mechanically. No literary prose was retyped or rewritten.

## Interpretation

The root title owns the byline and epigraph. Its children are Contents, Book One
and Book Two. Contents retains its four body blocks rather than duplicating them
as chapter nodes. Each Book owns its actual chapter headings and continuous prose
ranges through the next heading or Book boundary: 17 chapters, then 10. The
result has 31 nodes and 29 body files. No missing labels were invented.

The plan accounts for all 981 blocks: 920 assigned to the tree and 61 explicitly
excluded. Exclusions cover the eight-block distributor header, one isolated
slash, and the 52-block distributor end matter. Full excluded bytes remain in
the immutable acquisition. The slash interpretation and historical print-edition
uncertainty are recorded in ../notes.md. No separate modern preface or editorial
essay was identified within the retained literary span.

Canonical evidence is plan.json, audit.json, ../structure.json and ../source/.
Mechanical coverage is not a claim of human review or literary correctness.

## Verification and outcome

- `./ctp validate`: passed (3 works, 3 editable editions, 4 frozen snapshots,
  2 generation runs across the repository).
- `python3 -m unittest discover -s tests -p test_tree.py -v`: 34 tests passed.
- `git diff --check`: passed for tracked changes; new mechanically copied
  source bodies intentionally retain acquired whitespace.
- Compared all seven pre-existing rights/acquisition files byte-for-byte with
  Git HEAD: unchanged. Checked the final working-tree paths: all additions are
  within books/gutenberg-36.
- No UI/export implementation change; no site build, browser navigation or
  remote deployment check performed for this source-only job.

Outcome: complete for the bounded first-structure stage, with metadata marked
`imported`. Historical print-edition verification and human structural review
remain open. At the end of the agent phase, no commit or push had been made;
validation and publication by the trusted wrapper are separate.

## Local source-preparation run

- Method: AI-assisted source-structure analysis; mechanical `source-apply` copy and IDs.
- Exposed model label: `gpt-6.1-sol`.
- Executor: Codex CLI (`--ignore-user-config --ephemeral --sandbox workspace-write`).
- Task prompt SHA-256: `b78512657cb84c1e09d55e3e04d1bf8415da6fd3f4c7ed1c8ad85c71e220a417`; reusable instructions: `prompts/source-preparation.md`, `prompts/structure-source.md`.
- Structural checks do not establish human review or source-edition verification.
