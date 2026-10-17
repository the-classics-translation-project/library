# Maintainer workflow

## Add a work without editing the queue

Open Admin, search title/author/ID, choose targets and prepare an Issue. Submit the
form on GitHub. The intake workflow parses only the configured maintainer's requests
and updates the queue, then checks pending sources against the automatic US/Japan
rights policy. Passing packages are downloaded and committed to the repository;
uncertain cases stay on hold with recorded reasons. See
[source import](source-import.md) for evidence, supported cases and retries. Public visitors may see the form but cannot
authorize work. The live search uses the full Gutenberg CSV cache; the catalogue
workflow or `./ctp catalogue-refresh` refreshes it.

For manual intake, use `./ctp intake --github` with GH_TOKEN in the local environment,
or `./ctp intake --issues trusted-issues-export.json`. A fabricated export is not
proof of identity; use only an export fetched from the intended repository. Closing
an Issue does not erase work already accepted, and editing a request only adds targets.

## Start or continue an agent session

```sh
./ctp task
```

Give `build/next-task.md` to an interactive agent with the repository. It identifies
unfinished work from files and contains no model call. The initial candidate is
Gutenberg 41445, based on the founding discussion, with an English target. It has
not been imported and is not a publication approval. Change the candidate through
ordinary maintenance if another work is preferred.

Use already admitted acquisition files when present; held requests are listed with
reasons and are not automatically actionable. Acquire and structure sources using
[source import](source-import.md). The AI
may prepare metadata directly; the owner need not author JSON. Use source and
edition notes to record actual evidence and uncertainties.

## Translate, read, revise

Create an edition from `templates/edition/`, set its language/kind and map translated
labels and body paths to existing source IDs. Empty drafts are acceptable; omit
untranslated fields rather than inserting filler. Follow the short policy, work
notes and relevant target notes. Translate a useful amount; save progress locally.

Record substantial generation with `./ctp record-run` and freeze with
`./ctp snapshot books/<work> <edition>`. The exact command details are in
[provenance](provenance.md). A freeze records a draft without publishing it.

To distribute a draft for review, obtain the owner's approval and add its snapshot
to `catalog.json` with `audience:"review"`, `listed:true`, `approved_by` and an
approval note. Then `./ctp build --epub` builds it; Pages deployment is separate.
For private/local experimentation, avoid committing/distributing protected text.
A temporary local allowlist entry can be used for a preview without being committed.

Read and speak directly to an agent, or collect workbench comments. A rewrite may
replace one word, several nodes or the whole edition. Keep the original snapshot
and any useful observations. A new run should record the changed intent and inputs.
Do not modify old reports to fit new text.

## Review reports

Retrieve the Issue/report and validate its revision with `./ctp check-review`.
Inspect the original, quoted target and surrounding context. Decide whether the
observation is sound and whether to edit, retranslate, explain, defer or reject it.
Use `reviews/` and `templates/disposition.json` for durable dispositions when useful.
Do not automatically close reports after a new version is generated. A missing
quotation in a new draft is not evidence that its underlying concern disappeared.

## Approve and publish

Use [quality and publication](quality-and-publication.md). `ready` and a reader
catalogue approval are owner decisions, not rewards for passing tests. The book's
rights/distribution record must be suitable for the intended territories. A Pages
build can update explicitly approved review material without changing those approvals.
No KDP work is automated in this version.

The publishing helper only establishes/uploads this repository and requests site
builds. It cannot make the translation commercially ready. Check workflow results
rather than treating a push or dispatch as successful deployment.
