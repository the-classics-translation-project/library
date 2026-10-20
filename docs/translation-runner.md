# Local CLI translation runner — proposed design

**Status: optional future CLI automation proposal.** The separate ZIP-based
translation-request/export/import workflow is implemented as described in
[translation ZIP workflow](translation-zip-workflow.md); it uses the owner's
existing external ChatGPT relay rather than launching a model here.
There is no implemented unattended CLI translation launcher,
verified CLI invocation, fresh-session integration or actual translation run in
this repository. The goal is to make a request such as *translate The War of the
Worlds into Japanese* actionable once that source is lawfully admitted,
structured and ready, without requiring the owner to manually shuttle prompts.

**Separate first milestone:** [automated local source preparation](local-source-automation.md)
runs before translation: Issue intake → rights/source → source-tree analysis →
Admin display. That local coordinator may need broad bibliographic and source
context. It is NOT the fresh-context literary translation worker specified
below. Do not make the initial source automation translate any text.

## Responsibility boundary

A **coordinating agent** can retain full repository context: `AGENTS.md`,
`STATUS.md`, `queue.json`, progress, source-tree IDs, work/edition notes and
validation tools. It decides what bounded translation work is ready, assembles
inputs, checks outputs and maintains revision/provenance records.

A separate **translation worker**, started through an installed local model/agent
CLI, should get a newly created session for that one task. Its supplied context
should be explicit and minimal: a literary prompt, exact target language, selected
authorized source prose and labels, only necessary neighboring context and
relevant editorial notes. Do **not** silently send the coordinator's whole chat,
unrelated files or stale conversation attachments. "Fresh context" means no
previous **user-supplied session/conversation history**; the CLI/model can still
have built-in instructions, tools or service-side context. The launcher must
discover and test the CLI's actual session behavior.

The local Work/Codex agent is the preferred developer/tester because it can run
the owner's installed CLI and check actual authentication, workspace isolation,
arguments, exit codes, output and recovery. ChatGPT with GitHub access can also
write ordinary code/docs, review changes and merge PRs. Direct commits are fine
for small validated changes; PRs are useful for independent review, not required.

## Proposed execution sequence

1. **Check readiness.** Inspect live repository files and `./ctp task`. Do not
   translate a work held by the source-rights policy, a missing source package
   or unstructured source. Confirm intended work, target edition and version.
2. **Assemble a bounded, auditable job.** Select ordered source node fields (both
   labels and prose), source hashes/IDs and the target language. Include the exact
   contents of `prompts/translate.md`, applicable literary policy, selected
   work/edition notes, and only justified adjacent context. Record the inputs and
   their ordering; batching must not imply sentence/paragraph alignment.
3. **Launch a new CLI session.** Use a fresh process/session rather than resuming
   a coordinator/earlier worker session. Restrict ambient workspace/configuration
   and tool permissions to what the tested CLI actually supports, preferably
   with no repository write access and an explicit output destination. Do not
   assume undocumented flags work or that a user's ChatGPT subscription can
   authenticate until verified locally. No separate paid model API is required.
4. **Capture output and failure information.** Keep stdout/stderr, exit status
   and partial results separate. Do not treat a nonzero exit, missing data or
   partial text as a finished edition. Validate identity, order, source-field
   coverage, translated labels and edition schema; don't manufacture absent
   headings. Structural validation does not establish literary fidelity.
5. **Save a draft and provenance.** Only after checks, write editable translation
   fields and record the actual supplied prompt/session instructions, source
   fingerprint, visible model/CLI details and all output hashes with
   `./ctp record-run`. Snapshot with `./ctp snapshot` when appropriate.
   Review, distribution-catalogue approval and KDP are independent owner choices.

The coordinator may retry or split a failed job, but a retry should be a newly
identified attempt: never overwrite a historical run silently or claim success
because a prior translation file happened to exist. Existing editorial notes can
inform successive fresh sessions without inheriting unseen prior conversations.

## Local implementation and acceptance tests

- **Offline fixtures:** prove deterministic job assembly, stable source IDs,
  rejection of held/unstructured works, prompt/notes selection, output parsing,
  missing-field detection, no accidental repository writes and failure/retry
  bookkeeping. No model invocation should be needed for these tests.
- **Explicit local smoke test:** with the owner's permission, verify the
  installed CLI and authentication, launch a small real translation in a new
  session, inspect the exact input visible to it, record output and exit status,
  and repeat with another job to test absence of previous user conversation.
  Do not infer lack of built-in prompts or service-side state.
- **Provenance test:** verify a completed smoke run integrates cleanly with
  `record-run`, `./ctp validate` and snapshots, and that incomplete/failed
  attempts are not mislabeled as complete.
- **Cost/safety boundary:** do not add a paid API dependency, scheduled model
  calls, unattended translation runs, credential logging or automatic reader
  publication without the owner's separate authorization.

Open implementation choices include the specific CLI, supported fresh-session
flags, stdin versus input files, structured output contract, context-window and
batch sizing, model selection and available subscription limits. Resolve them by
running the real CLI locally; this document is not evidence that those features
are already supported.
