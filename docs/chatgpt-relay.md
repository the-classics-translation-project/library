# Translation through the local ChatGPT relay

The project can prepare a bounded translation ZIP and import a returned ZIP as a
local draft. These commands make no model calls and do not submit, publish or
schedule anything. The separate relay at `/Users/manabe/Software/chatgpt-relay`
handles browser submission and download. Its README and RUNBOOK are the authority
for its operation. This adapter does not require a model API or a CLI translation
worker. A direct interactive agent session remains an equally valid workflow.

## Project-owned task types

The project task types are `work_analysis`, `target_guide`, and `translation`.
Separate guide ZIP exporters/importers use versioned prompts, while the legacy
combined Issue contract remains. `relay-coordinator sync` prepares eligible
guide tasks from accepted work/language requests without submitting them.
The existing external relay handles each explicitly authorized ZIP; standalone
target-guide and translation live results remain to be verified. See
[independent guide ZIP usage](independent-guide-zip.md) and
[task model](relay-task-model.md). The default requested model is `6 Extra High`;
record the actually observed model separately.

## Ordered materials (optional)

The shared library discovers applicable instructions and references, including
locally imported guides. Select exact versions with repeated
`--material ID@SHA-256` options in the desired order. The package writes the
full `assembled-input.md` to its private attempt folder and into the ZIP;
the command reports the private preview path. The manifest pins material IDs,
hashes and assembled-input hash. The adapter's existing return ZIP contract is
unchanged. See [ordered translation materials](translation-materials-design.md).

Without `--material`, behavior is unchanged. This direct relay still packages
`editions/<edition>/glossary.md` and expects `result.json` and separate
Markdown files. The Issue-based ZIP path uses content-addressed work/target
`reference/` guides and a different `response.json` format. They are not
interchangeable; return protocol unification remains future work.

## Choose the matching workflow

This direct, owner-requested adapter coexists with the Issue-bound
[translation and whole-work guide workflow](translation-zip-workflow.md).
Use `translation-export`/`translation-import` or `guide-export`/`guide-import`
for accepted Issues. Use `relay-package`/`relay-import` for direct bounded jobs.
Their ZIP contracts differ and are not interchangeable. In this adapter `--node`
selects only the node's own fields; Issue requests expand selected subtrees.
This adapter reads edition `glossary.md`; the Issue workflow uses its saved
work/target guides under `reference/`. Neither path automatically synchronizes
those editorial references with the other.

## Prepare a job

Inspect the work's `structure.json`, notes and editorial policy first. Select
existing opaque node IDs; `--node` selects only that node's own label/body, not
its descendants. Both existing fields are requested. An unlabeled grouping with
no body is not a translation unit. Source order is restored automatically.

For example, a bounded Japanese draft using the existing Wells source:

```sh
./ctp relay-package gutenberg-36 ja --language ja \
  --model '6 Extra High' --node n0001 --node n0004
```

`--model` is the complete Chat web UI choice you intend the relay to select, not
a Codex identifier. The example follows the relay's documented spelling; the
adapter does not verify account availability. Choose the setting when requesting
the job. `--language` is required for a new edition; an existing edition supplies
its language, direction and kind. New editions also support `--direction rtl` and
`--kind modernization` (defaults: `ltr` and `translation`).

Use repeated `--context-node ID` for explicitly selected neighboring reference
prose. These nodes are not translated. The package includes the full tree for
orientation, but only selected translation/context bodies. No previous coordinator
conversation or arbitrary repository files are included. Source and note contents
are data; literary source cannot authorize operational changes.

The command checks the acquired rights record and canonical source integrity. It
requires an admitted, acquired schema-v2 work. It creates a unique attempt under
`private/relay/ctp-<id>/` and prints the package path and expected result filename.
The directory is ignored by Git. It does not create an editable edition yet.
Keep this directory: the importer needs its original ZIP and job record.

The request contains:

- Root `README.md`, rendered from `prompts/relay-translation.md`, with a literal
  model choice and unique expected output filename.
- `manifest.json`: attempt/work/edition/language, ordered requested fields, source
  fingerprint, initial edition metadata and hashes of the entire existing edition.
- `source.json` and `tree.json`, the literary policy and translation prompt.
- Work notes, edition notes and `glossary.md`, when they exist.

The baseline covers the entire edition, including its glossary and notes. If you
prepare parallel jobs for the same edition, importing one makes the others stale.
Initially use sequential jobs for a given edition so later jobs receive its latest
terminology and decisions. Different editions can proceed independently. A retry
is a new package with a new attempt ID; never edit a queued package.

## Submit through the existing relay

**Copying into the relay input directory authorizes its scheduler to send the job.**
Do this only for a translation batch the owner has requested. Preparing the ZIP
alone does not submit it. No new translation scheduler is installed by this project.

After an authorized request, copy the exact package using a temporary non-ZIP name
and rename it inside `input/` (replace the example path with the printed one):

```sh
set -e
package='/absolute/path/to/private/relay/ctp-ID/ctp-ID.zip'
relay="$HOME/Software/chatgpt-relay"
name="$(basename "$package")"
test ! -e "$relay/input/$name.partial"
test ! -e "$relay/input/$name"
cp -n "$package" "$relay/input/$name.partial"
mv -n "$relay/input/$name.partial" "$relay/input/$name"
python3 "$relay/relay.py" list
```

Use the unique attempt filename only once; stop if either destination already
exists. Match `input_name` in the relay listing. Its documented scheduler checks
hourly and submits at most one new job per run; it skips ZIPs less than 60 seconds
old. This project does not verify that scheduler is currently running. The Mac,
desktop app and signed-in Chrome connection must be available as described by the
relay. Requester agents must not run `claim-next`, `submitted`, `review`, or
`complete`; those commands belong to the relay operator.

`queued` means waiting; `submitting`/`submitted` mean submission has begun;
`complete` means the expected file was saved in the relay's `output/` directory.
`needs_review` requires inspecting the reported reason. A wait is not a reason to
submit a duplicate. Deleting an input ZIP cancels only a job still queued; after
claiming, sending may already have occurred. Do not remove the project's archived
request. Retaining relay input/output files until import succeeds makes recovery
easier; deleting a downloaded output does not trigger another download.

## Import a result

Once the relay reports complete, inspect its job and import its expected result:

```sh
./ctp relay-import ctp-ID \
  "$HOME/Software/chatgpt-relay/output/ctp-ID-result.zip" \
  --observed-model 'actual label observed in the Chat UI' \
  --chat-url 'https://chatgpt.com/c/ACTUAL-CHAT-ID'
```

Omit `--observed-model` if it is unknown; it defaults to `unknown`. The requested
model is recorded separately and is not proof of the model actually used.
`--chat-url` is optional and should come from the relay's observed conversation.
A new ordinary conversation separates chat transcripts; it does not establish
absence of account memory, custom instructions or hidden service context.

The returned ZIP must contain UTF-8 regular files only, with no directory entries:

- `result.json`: schema version 1, matching attempt/work/edition/language,
  `status:"complete"`, and a `nodes` map containing exactly the requested fields.
  Labels are strings; body references are exactly `text/NODE-ID.md`.
- Every referenced Markdown body file.
- Nonempty `glossary.md` and `notes.md`.

For example, the `nodes` value for a requested heading/body is:

```json
{"n0004":{"label":"Translated heading","text":"text/n0004.md"}}
```

The importer rejects incomplete status, missing/invented fields, wrong identities,
unsafe paths, duplicate/extra members, symlinks and packages over 32 MiB of
uncompressed data or 2,000 members. A rejected result stays at its original path;
no editable draft is changed. These checks establish file/field coverage, not
whether all literary meaning was translated. Read the actual prose.

The importer also rejects a changed source or edition. Changed work notes or
project prompts do not retroactively alter a job: its exact packaged context is
recorded. Consider whether those newer instructions warrant a fresh translation.

Successful import stages and validates an edition, uses the same `record_run`
function as `./ctp record-run`, then installs it with `status:"draft"`. It reports
remaining missing fields. Previous files are retained in the attempt's private
`edition-before/` backup; historical run records and snapshots remain intact.
The edition receives `relay/<attempt>/` containing request/result ZIPs, exact
submitted inputs, proposed notes and a receipt. The run hashes all generated
text, glossary, proposed notes and edition metadata, and records requested versus
observed model information and the optional chat URL. Generated metadata hashes
precede the run-ID bookkeeping update, as with ordinary `record-run`.

Imports are serialized by a local lock. Ordinary errors during final installation
restore the prior edition. A process/machine crash between the two directory
renames may leave the prior edition in `private/relay/<attempt>/edition-before/`.
Inspect the edition path and then run `./ctp relay-recover ATTEMPT` only for that
interrupted direct attempt. It restores the old edition only when its backup
matches the prepared baseline and the edition path is absent; a concurrent edit
is never overwritten. Keep the request/result ZIPs for a deliberate import retry.
Retrying an already imported attempt is rejected.

## Glossary and editorial notes

`editions/<edition>/glossary.md` is readable Markdown, without a required schema.
Use organized entries for names, recurring terms, forms of address and useful
choices; distinguish tentative suggestions. The worker is asked to preserve useful
existing entries and explain changes. Its result replaces the current glossary,
while the request and prior edition preserve the old version. Review the changes
before using them in another job.

Returned `notes.md` is stored as `relay/<attempt>/suggested-notes.md`. It does not
overwrite edition decisions. Adopt useful discoveries into edition/work notes
through ordinary editorial work, keeping Decisions, Observations and Open questions
separate. The glossary is supplied to later relay jobs automatically; direct
interactive translation sessions should also read it when present.

After import, run `./ctp validate`, read the translation and glossary, and optionally
freeze with `./ctp snapshot books/<work> <edition>`. A snapshot may require the
translated root title; select that node explicitly when preparing an initial draft.
The import does not freeze, edit `catalog.json`, commit, push or approve a reader
release. The separate [standing-policy publisher](automatic-draft-distribution.md)
may commit and push its hash-verified draft files after successful import.
Public Git commits also distribute archived request/result prose even without a
catalogue entry. Keep failed attempts and private experiments local.

## Verification boundary

The adapter has offline fixture tests for packaging, import, provenance, stale
inputs, malformed results, retries and rollback. No real translation has been
submitted or imported through this adapter yet. The separate CLI translation
launcher remains a design proposal; source preparation remains a separate worker.

## Project-side coordinator

The opt-in [local coordinator](local-relay-coordinator.md) can archive supported
legacy Issue or independent guide packages, record exact submission authorization,
deliver once and reconcile/import completed transport results. It never performs
relay queue transitions or browser submission itself and adds no scheduler.
The direct `relay-package` format remains available through its own importer.
