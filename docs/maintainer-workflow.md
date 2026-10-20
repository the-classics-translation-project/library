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
unfinished work from files and contains no model call. The founding candidate,
Gutenberg 41445, has an English target and an imported source tree; it is not
translated or approved for publication. Change the candidate through ordinary
maintenance if another work is preferred.

Use already admitted acquisition files when present; held requests are listed with
reasons and are not automatically actionable. Acquire and structure sources using
[source import](source-import.md). The AI
may prepare metadata directly; the owner need not author JSON. Use source and
edition notes to record actual evidence and uncertainties.

**Local preparation code:** the first local-automation milestone is described in
[docs/local-source-automation.md](local-source-automation.md). The deterministic
check selects already acquired/unstructured works **and** supported holds needing
evidence research (which `./ctp task` currently skips). The agent may investigate
the exact hold, record narrow cited evidence under the existing policy and let
the acquisition workflow reassess it; unsupported or unresolved issues stay on
hold. After an admitted acquisition is available, the agent constructs a
reference-only plan and uses the mechanical importer to allocate node IDs.
The local wrapper handles validation and publishing. The code has fixture tests,
and a bounded live run published #41445 after validating its source tree; CI,
Pages and ledger reconciliation succeeded. A per-user LaunchAgent is installed
from a dedicated checkout under Application Support; its first scheduled tick
found no pending work and made no model call.

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

## Local CLI translation launcher (planned, not available yet)

The preferred implementation environment is a **local Work/Codex agent** operating
on a checkout, because it can test the installed CLI, authentication, process
isolation, file output and failure recovery where the actual translations will run.
ChatGPT with GitHub access can handle ordinary repository maintenance and review
the implementation; neither role requires a PR for every small change.

The intended user workflow is to ask the local coordinator to translate a
specified work and language. It should inspect `AGENTS.md`, `STATUS.md`,
`./ctp task`, source eligibility and the actual files; do not bypass a held
source. Once a work is properly acquired and structured, the coordinator can prepare
bounded translation inputs and launch separate **fresh-context CLI sessions**
rather than carrying its entire conversation into each translation.

See [translation runner design](translation-runner.md) for the input/output
boundary, provenance, failure handling and acceptance tests. The current CLI
commands `./ctp task` and `./ctp record-run` do **not** themselves invoke a model.
Do not claim a fresh-context launcher exists, or make paid API calls or schedule
unattended translations, without separately implementing and authorizing them.

## Translation Issues and existing ChatGPT ZIP relay

Source preparation and translation are separate. The static Admin page now
offers node selection, target language, a Git-versioned translation prompt,
a missing-only/retranslation scope and optional previous-version reference.
It prepares the Issue; the authorized intake workflow pins its exact prompt.
Local `./ctp translation-pending`, `translation-export`, and
`translation-import` commands form and validate packages for the owner's
existing ZIP-to-ChatGPT relay. They do not invoke a model. Whole-work context
and terminology guides use `guide-export` / `guide-import`.

Read [the detailed exchange guide](translation-zip-workflow.md) before using
the return ZIP importer. Frozen snapshots preserve previous translations;
unapproved drafts are not exposed as history on public Pages. Neither a model
result nor a successful import approves a reader release.

## Whole-work glossary request

In Admin, a structured work now offers a separate **Whole-work glossary and
translation guide** request for any supported target language. The prepared
GitHub Issue must be submitted by an authorized maintainer. Intake pins
the guide prompt and source fingerprint in `guide-requests.json`. After
intake, use `./ctp guide-pending` and
`./ctp guide-export --issue NUMBER --output build/guide.zip`, hand the ZIP
to the existing external ChatGPT relay, and import its returned ZIP with
`./ctp guide-import`. This preserves the guide's Markdown and earlier
versions, updates the current references and writes an Issue-bound import
receipt. The guide Markdown needs reasonable organization but has no
mandatory per-term fields.

See [the exchange instructions](translation-zip-workflow.md).
Manual `guide-export WORK TARGET` remains supported for experiments
without an Issue.
