# Local relay coordinator

This opt-in command group joins existing project ZIP adapters to the separately
installed ChatGPT relay. It creates no scheduler, calls no model API, performs no
browser actions and never writes the relay SQLite queue. The source-preparation
LaunchAgent is separate. A direct interactive session remains supported.

## Exact authorization and durable state

Use `./ctp relay-coordinator status` for read-only task proposals and local attempt
status. This command does not create state files. New coordinator state lives in
Git-ignored `private/relay-coordinator/attempts/ATTEMPT/`, alongside the exact
request ZIP, captured response ZIP, authorization note and recovery journal.
Back up that directory when moving machines; do not delete an uncertain attempt
merely to make it disappear from status.

Prepare one accepted guide or translation Issue:

```sh
./ctp relay-coordinator prepare --guide-issue 12
# Or an accepted translation request:
./ctp relay-coordinator prepare --translation-issue NUMBER
```

For a newly proposed independent guide:

```sh
./ctp relay-coordinator prepare --task-type work_analysis --work gutenberg-41445
./ctp relay-coordinator prepare --task-type target_guide --work gutenberg-41445 --target en
```

The target guide normally follows its imported work analysis. Existing guide
Issue #12 covers both Wells guides; do not generate competing independent Wells
jobs. Preparation checks current source admission and canonical input identity.
It creates an immutable local request, with default requested model `6 Extra High`
(overridable by `--model`). It does not deliver anything to the watched folder.
Repeated preparation of the same editorial job returns its existing active
attempt; it does not create another Chat request. The direct `relay-package`
translation format is not handled by this coordinator; use its existing importer.

Archive a previously exported compatible ZIP with `adopt REQUEST.zip`. It must
match one of the supported current exporter contracts. For legacy exports this
requires the explicit model/output README metadata added on 2026-10-25. An
already delivered request can be adopted without copying or resubmitting it.

Submit only a batch the owner has authorized:

```sh
./ctp relay-coordinator submit ATTEMPT --authorization 'Exact owner request and scope'
```

An authorization note documents the human instruction; inventing a note does not
create permission. It binds this exact package hash and relay location, not all
future proposals, target languages or retries. The command publishes the ZIP into
the existing watched folder with an atomic no-overwrite operation, recording a
`delivering` state before doing so. The relay's operator handles scan, claim,
ChatGPT model selection, upload, send and download, under its own RUNBOOK.
No requester calls the transport's claim/submitted/complete commands.

The default relay path is `~/Software/chatgpt-relay`. To choose another installed
relay, put `--relay /absolute/path` **before** the subcommand when preparing or
adopting. Existing attempts retain their pinned relay path.

## Reconcile and import

```sh
./ctp relay-coordinator reconcile
./ctp relay-coordinator reconcile --import-ready
```

The first observes only; the second additionally accepts completed, validated
results. Both update local attempt records. They open the relay database in
read-only mode and match the exact input name, request hash, requested model and
expected output name. A missing database leaves delivery waiting. Relay
`submitting` remains uncertain and is never automatically resent. Elapsed time
alone is not failure. Missing/changed downloads, relay review requests, changed
inputs and malformed results stop the attempt with a reason.

A `complete` transport record is not an imported or reviewed literary result.
The exact downloaded ZIP is copied into private attempt storage. Import runs the
appropriate existing importer in an isolated staging copy, checks that canonical
editorial files have not changed, and installs only the task's expected
reference/edition, receipt and immutable snapshot files. It never changes
`catalog.json` or source acquisition files. Existing strict response formats
remain distinct and accepted historical Issues retain their pinned meaning.

Before installation, the coordinator saves prior versions and a per-file journal.
Ordinary installation failures restore prior files. On a later reconcile after
an interrupted installation, it rolls back recorded outputs and stops for review.
Recovery refuses to overwrite a current file whose hash matches neither the
previous nor attempted output, preserving an intervening human edit. Imports and
submissions are serialized with a nonblocking OS lock. Keep other editors away
from the same output files during the short final installation operation.

An imported attempt is not imported again on subsequent polls. Snapshots/reports
and old guide versions are preserved by the underlying adapters. Requested model
and observed model are distinct. The response's exposed label remains unknown
when not actually established; no internal model snapshot is inferred. The
coordinator records actual checkout Git context in its private attempt receipt;
staged importer provenance may have no Git context of its own.

## Review, retry and Git distribution

Inspect `needs_review` reasons and the archived input/result before retrying.
If the same submission can safely finish (for example its missing download was
restored), use `resume ATTEMPT` and then reconcile again. This only retries
observation/import, never copies a ZIP or sends another Chat request. After a
rolled-back import it requires the old file state to be restored and preserves
the old transaction journal. A wrong model/hash or stale input still fails.
After deciding a second submission is appropriate, prepare the same job using
`--retry-of STOPPED_ATTEMPT`, then explicitly authorize the new attempt. It gets
new transport filenames and retains its link to the original. It is never an
automatic resend. Changed source or guide baselines require a newly prepared job;
existing guide regeneration still uses the explicit standalone guide workflow.

Successful import leaves files local. Read AI-generated guides as draft references,
not adopted editorial decisions or exhaustive analysis. Structural validation
establishes neither fidelity nor human review.

Optional Git publication requires a **separate** explicit approval for public
repository distribution:

```sh
./ctp relay-coordinator publish ATTEMPT --approve-git-distribution
# Add --push only when that Git push is also authorized.
```

This validates the project, requires an empty index and no unrelated working-tree
changes, checks every imported output hash, and stages only that attempt's exact
file list. A push uses the existing branch without force; remote conflicts stop
rather than being silently merged. Publishing code or an approved older draft
is not permission to publish newly generated guide/translation text. Even without
Pages listings, public Git commits distribute their contents. No command selects
a license, approves a reader/review release, or submits to KDP.

## Verification boundaries

Offline tests use admitted source fixtures and a synthetic SQLite transport,
including no-op polling, same-job deduplication, explicit authorization, result
identity checks, legacy/independent/translation import, rollback, process locking,
retry boundaries and exact-file Git distribution. Actual model/browser/relay
outcomes are recorded separately in STATUS and the automation roadmap. Nothing
in this implementation enables automatic scheduled project submissions. The
independent guide Issue intake and ordered-material UI remain future milestones.

## Automatic completed-result follow-up (owner enabled on 2026-10-25)

The app heartbeat **Import completed Classics relay results** checks this local
workspace every 30 minutes using `reconcile --import-ready`. The owner requested
this after both real guide outputs were downloaded. Existing per-package
submission authorization remains required. It imports valid completed results as
local drafts and reports a newly imported result or a new actionable failure;
unchanged checks stay quiet. It does not prepare/submit new jobs, automatically
resume `needs_review`, alter the relay schedule/queue, commit/push output or
approve release. Review holds still require an explicit reviewed `resume`.

The two existing guide attempts were imported immediately, including an explicit
resume of the recovered Wells result, and a repeated local poll was a no-op.
The app confirmed the heartbeat is active; its first timed execution and recovery
after sleep/restart remain unverified. The local Mac and desktop app need to be
available. No new LaunchAgent was installed. The exact heartbeat instructions are
recorded in [the prompt](../prompts/relay-result-import.md); view or manage the
heartbeat through the app's automation controls. Repo code itself installs no
scheduler. Generated guide files remain local until separately approved for Git
distribution, regardless of whether they were imported manually or by heartbeat.
