# Prompts, generation provenance and editorial memory

## Three scopes

Project guidance lives in `docs/editorial-policy.md` and related operating documents.
`books/<work>/notes.md` holds source-specific findings: characters, voices, uncertain
readings, narrative context and issues shared by target languages.
`books/<work>/editions/<edition>/notes.md` holds target-language decisions: names,
forms of address, register and useful criticism from earlier versions. An optional
`glossary.md` beside edition notes holds organized, human-readable terminology;
`record-run` captures it when present.

Use **Decisions**, **Observations**, and **Open questions** rather than presenting
all notes as established facts. Cite source locations, reports and relevant
revisions where useful. Notes may evolve without regenerating a translation and
should survive a complete retranslation. Maintain one logical edition per target
approach; stylistic experiments can be branches/revisions rather than needless new
edition IDs with detached notes.

## Reusable prompts

Store prompts in `prompts/` as ordinary Markdown. Git versions them. Capture the
exact text used in each generation record, so uncommitted prompt changes and
interactive additions are not hidden behind a filename or an obsolete Git ref.
Do not create a second, more restrictive literary policy inside a prompt.

Current starting points are `structure-source.md`, `translate.md`, `review.md` and
`next-task.md`. They are instructions for an agent, not scripts making model calls.
The retained `translation-start.md` is an earlier reference, not a separate policy.

## Recording a substantial generation

After saving the output and recording the material session instructions:

```sh
./ctp record-run gutenberg-41445 en \
  --model 'actual label exposed in the interface' \
  --interface chatgpt --operation retranslation \
  --prompt prompts/translate.md \
  --instructions 'This attempt should make the dialogue less formal.' \
  --output books/gutenberg-41445/editions/en/text/n0004.md \
  --output books/gutenberg-41445/editions/en/edition.json
```

List all generated/rewritten text files. Include `edition.json` when labels were
changed. Store longer visible session instructions in a Markdown file and pass it
as another `--prompt`; do not rely on a vague summary when exact text is available.
Record omissions in contextual coverage. Do not include private transcripts or keys.

The command captures prompt and note text with hashes, a source fingerprint, the
current Git context when available, operation, interface, exposed model label,
creation time and output paths/hashes. It appends its run ID to the edition. The
`model_snapshot` field is null unless reliable exposed information is recorded;
a product label is not a promise of an immutable backend model. API parameters can
be recorded as additional explicit data if an API is later introduced.

The command updates `edition.json` to attach its run, so that file's recorded hash
identifies the generated metadata **before that bookkeeping update**. It is not a
hash of the subsequently modified edition.json. Snapshotting captures the final
metadata and referenced records together. Historical output hashes are not compared
against today's editable prose; those files may legitimately have been rewritten.

Freeze after recording:

```sh
./ctp snapshot books/gutenberg-41445 en
```

The snapshot embeds the referenced generation records and all available rendered
source/target fields. Missing run records fail validation. Small editorial fixes
can use Git commit messages and notes; do not invent model provenance for a human
change or require a new model run for each typo.

## Limits

These records establish provenance, not exact reproducibility. ChatGPT conversation
history, hidden instructions, model routing and nondeterminism may not be fully
visible. Unknown values remain unknown. Attribution is not a claim of copyright,
literary quality, or human review. Initial synthetic migration records explicitly
identify inherited prose whose original model is not known.

## Proposed provenance for isolated local CLI translation

A future coordinating agent may render a **fully assembled, per-run input** from
versioned prompts, authorized source text/labels, target-language instructions and
relevant work/edition notes, then pass it to a fresh CLI translation worker.
Preserve that exact supplied input (or its complete constituent files with
order and hashes), not just the template name. Also capture the selected source
node IDs, source fingerprint, output paths/hashes, exposed model label, actual
CLI/interface and version when available, explicit command/configuration and
any human-visible session instructions. Never record credentials.

Use `./ctp record-run` and `./ctp snapshot` as the existing evidence and
freezing mechanisms, adapting their integration only when necessary. The launcher
must establish whether a new process really avoids prior user conversation and
ambient repository context. It **cannot guarantee** absence of hidden system
instructions, service-side behavior or nondeterminism. A skipped/failed/partial
run is not a completed translation or editorial approval.

This launcher and its CLI-specific metadata capture are **not yet implemented**.
For the proposed execution contract and local smoke tests, see
[translation runner design](translation-runner.md).

## Browser relay generation

`relay-import` uses `record_run` with the exact archived package inputs instead of
recapturing current policy/notes. It includes submitted source/context, glossary,
manifest and the short relay submission message. The requested model is separate
from the observed model label (default `unknown`); an internal model snapshot
remains unknown. The result ZIP and request ZIP are retained under the edition's
`relay/<attempt>/` directory with hashes in the run. See [relay usage](chatgpt-relay.md).
Glossaries are Markdown editorial memory; proposed returned notes do not replace
adopted decisions. Structural import success is not human review or publication.
