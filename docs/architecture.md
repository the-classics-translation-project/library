# Architecture

The repository is persistent editorial memory. Ordinary scripts do mechanical work;
an interactive agent provides interpretation and prose when asked. No API account
or unattended agent is required to inspect, validate, annotate or publish artifacts.

## Data flow

```text
Admin catalogue / direct instruction
  -> GitHub work-request Issue -> authorized additive queue
  -> acquired source bytes -> numbered reversible blocks
  -> AI reference plan -> mechanically allocated source tree
  -> editable target labels/prose + notes + generation records
  -> immutable snapshot
  -> explicit distribution catalogue
  -> reader HTML / workbench HTML / EPUB

Workbench -> version-specific observation report -> GitHub Issue
  -> maintainer + AI judgment -> small edit OR whole retranslation
```

The owner can skip the feedback route entirely and ask an agent to rewrite the
text. The same invariants protect source and historical evidence in either path.
No element of the data model assumes that a new translation incrementally edits
its predecessor or preserves its sentence boundaries.

## Components

`tools/source_import.py` preserves acquisition bytes, numbers blocks, checks an
AI reference plan and copies a canonical tree. `tools/ctp.py` validates schema-v2
work/edition records, freezes revisions, captures generation provenance and exposes
the CLI. `tools/legacy_v1.py` preserves compatibility with old example snapshots.

`tools/site_builder.py` builds readers, an annotation workbench and a token-free
administrator page, and exports EPUB. `site/annotation-core.js` is the independent
anchor/report core; `site/reader.js` handles selection, highlights, marginal notes,
notebooks and export. `site/admin.js` searches cached metadata and prepares requests.

`tools/intake.py` parses a strict request format, authorizes by account login,
merges target requests without deleting old work, and derives task state. No Issue
content is interpreted as shell instructions or sent to a model. `./ctp task`
produces a bounded agent instruction, not a claim that an agent has been scheduled.
`tools/acquire_queue.py` and `tools/source_rights.py` run the separately approved,
conservative Gutenberg US/Japan source-admission checks without calling a model.

## Build versus release

Building is local and deterministic except for artifact timestamps and optional
explicit network commands. It does not approve a literary edition. Snapshots are
retained; `dist/` is disposable and replaced only after staging a successful build.
The source tree and available translation fields are independent of export files.

Reader catalogue, contributor workbench and Admin are separate routes with shared
navigation. They are all public when deployed; Admin is not an authentication wall.
Authorization happens during Issue intake. There are no secrets in browser assets.

## Automation in this version

CI tests/builds on pushes and pull requests, with read-only permissions. Pages is
manually dispatchable and reusable. Authorized Issue intake may commit its queue
and admitted source/hold records; weekly CSV refresh may commit catalogue metadata.
Those state-writing workflows invoke Pages explicitly when relevant files change.
There is **no automatic model translation** or KDP upload.

A future scheduled ChatGPT/agent session can inspect `queue.json` and actual files,
do a bounded task, validate and commit. Its availability, budget and permissions
must be configured separately; ordinary GitHub Actions does not grant subscription
model capacity. Keep API orchestration optional.

## Deliberate limits

No generic source-tree migration, image/PDF importer, cross-version automatic
annotation reanchoring, literary quality score, full production scheduler or retail
packaging model. Add these only when a real work demonstrates the need.

## Proposed separation of agent responsibilities

A ChatGPT conversation with GitHub access is suitable for repository maintenance,
documentation, code review and merging PRs. A local Work/Codex agent is preferable
for **implementing and smoke-testing a translation launcher** against the actual
installed CLI, local authentication and filesystem. This is a pragmatic division of
labor, not an access restriction: either can make code changes, and direct commits
are acceptable for small validated changes. PRs are helpful for cross-agent review
and potentially consequential changes, not mandatory ceremony.

The intended model-execution path has **two distinct contexts**:

1. A coordinator reads the work queue, verified/structured source, relevant
   editorial memory, progress and repository instructions; it plans bounded work.
2. It assembles an explicit, auditable input and starts a **new isolated CLI
   translation process/session**. That worker should receive only the selected
   source, target, literary instructions and necessary context; it should not inherit
   the coordinator's conversation history or unrelated repository contents.
3. The coordinator checks output, saves draft files, records run provenance and
   freezes revisions when appropriate. Neither generation nor a snapshot is a
   publication decision.

This is a **design direction, not a runnable feature**. Fresh user-level context
does not imply absence of the model product's built-in instructions or tooling.
A local implementation must test isolation and CLI/authentication details rather
than assuming any specific flags or subscription behavior. See
[translation runner design](translation-runner.md).
