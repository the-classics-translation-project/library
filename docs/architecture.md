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
manually dispatchable and reusable. Authorized Issue intake and weekly CSV refresh
may commit only their designated state files; they call Pages explicitly when
`CTP_PAGES_ENABLED=true`. There is no automatic model generation or KDP upload.

A future scheduled ChatGPT/agent session can inspect `queue.json` and actual files,
do a bounded task, validate and commit. Its availability, budget and permissions
must be configured separately; ordinary GitHub Actions does not grant subscription
model capacity. Keep API orchestration optional.

## Deliberate limits

No generic source-tree migration, image/PDF importer, cross-version automatic
annotation reanchoring, literary quality score, full production scheduler or retail
packaging model. Add these only when a real work demonstrates the need.
