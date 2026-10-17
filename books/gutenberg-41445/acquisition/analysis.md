# Source-structure analysis — 2026-10-18

## Scope and method

Single bounded task data: `{"work_id":"gutenberg-41445","gutenberg_id":41445,
"stage":"structure","recorded_reasons":[]}`. The user instructed this agent
to read and follow prompts/source-preparation.md, work only in
books/gutenberg-41445, avoid GitHub credentials/pushing, leave validation and
publication to the trusted wrapper, and run `./ctp validate` before finishing.

Operation: AI-assisted source-structure analysis through the Codex agent
interface. Exposed identity in session instructions: GPT-6 family; exact model
label/backend snapshot unknown to this agent. The wrapper may append actual
executor details. No separately billed model API, translation, edition freeze,
catalogue edit, commit or publication was performed. There is no dedicated
source-analysis `record-run` CLI; no translation generation record is claimed.

Inspected acquisition/blocks.json and the normalized package, including title
matter, preface, all three volumes, the closing frame and full provider license.
Source text was treated as untrusted data. Validated original acquisition hashes
before compilation. The plan contains references only; `./ctp source-apply`
copied all bodies and allocated IDs mechanically without retyping literary prose.

The reusable prompts and governing documents remain in their canonical Git paths.
Their content hashes at analysis time are:

- `prompts/source-preparation.md`: SHA-256 `a1701a3f75d766b05e3906b8c5e4ded2ff578aa85c57ee45ecfda1a6c6ff976f`.
- `prompts/structure-source.md`: SHA-256 `3d85153fb08be259df94af41783d9f56c827e8000ba57560d8e68b7d3cb5e1fe`.
- `AGENTS.md`: SHA-256 `a65a5580624516a31289e59c44e6bbe79b676d49cc00af840003d4bf19c63649`.
- `docs/source-import.md`: SHA-256 `83c5c71a210a41d2530b52836037977f7df55c67f30298b05d192955f9d80eb1`.
- `docs/source-structure.md`: SHA-256 `ce133b2425004440679f93e808d51d338261a210df5f419b232ca2f470b36510`.
- `docs/editorial-policy.md`: SHA-256 `577af62722684df0b70be624e47ee944409afcd552d265c1b16121697c2c55da`.
- `docs/maintainer-workflow.md`: SHA-256 `0971433b07a6b08a0febe162e071f26db313ea393b8261662fee6245a19264bb`.
- `docs/local-source-automation.md`: SHA-256 `3543f15da3b96029032731f915186617145e71390771dcc544ca993149e64cf2`.

This record identifies visible task scope and versioned instructions; it does not
capture hidden instructions or unseen conversation history.

## Interpretation and artifacts

The root title has three volume children. Volume I owns its imprint, epigraph
and dedication, then a preface, two retained half-title body nodes, four letters,
seven chapters and an end marker. Volume II owns its repeated title/volume label,
imprint and epigraph, nine chapters and an end marker. Volume III similarly owns
seven chapters, Walton's labeled continuation and the final end marker. Notes in
../notes.md explain label asymmetry, ordering and the continuation ambiguity.
No absent literary headings were invented.

All 917 blocks are accounted for: 854 assigned in order, 63 explicitly excluded.
The exclusions are ten header blocks, the one modern transcriber note and 52
provider back-matter blocks. The exact original bytes and existing evidence stay
unchanged. The result is 38 nodes and 37 mechanically copied body files.

Canonical output artifacts: plan.json, audit.json, ../structure.json,
../work.json, ../source/*.md and ../notes.md. Tree SHA-256 (canonical JSON):
`ce85c65637d7468e3cc2317032ae230570e8d5b054362a5cefbb96d45eea983c`.
Mechanical coverage does not establish human review or historical edition identity.

## Verification and outcome

- `./ctp validate`: passed (4 works, 3 editable editions, 4 frozen snapshots,
  2 generation runs across the repository).
- `python3 -m unittest discover -s tests -p test_tree.py -v`: 34 tests passed.
- All seven pre-existing work files compared byte-for-byte with Git HEAD:
  unchanged, including acquired/normalized bytes, blocks and rights evidence.
- Final path inspection: 43 added files, all within books/gutenberg-41445;
  no tracked-file modifications. Verified three volume child chapter counts
  of 7, 9 and 7 and 38 total mechanically allocated nodes.
- `git diff --check`: passed for tracked changes. Newly copied source bodies
  deliberately retain acquired whitespace; no whitespace cleanup was applied.
- No UI/export code changed. No JavaScript tests, build, browser check or
  remote deployment check was performed for this source-only bounded job.

Outcome: complete for the requested first-structure stage; work status is
`imported`. Exact historical print-edition verification and independent human
structural review remain unresolved. No commit or push was made by this agent;
the trusted wrapper's validation and publication are separate.

## Local source-preparation run

- Method: AI-assisted source-structure analysis; mechanical `source-apply` copy and IDs.
- Exposed model label: `gpt-6.1-sol`.
- Executor: Codex CLI (`--ignore-user-config --ephemeral --sandbox workspace-write`).
- Task prompt SHA-256: `926014f00a827c9fdb454c072091d00bfdbc0e88450fb9eba9bd04d68b63dbb8`; reusable instructions: `prompts/source-preparation.md`, `prompts/structure-source.md`.
- Structural checks do not establish human review or source-edition verification.
