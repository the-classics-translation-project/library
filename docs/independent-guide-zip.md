# Independent guide ZIP jobs (offline, opt-in exchange)

**Implemented as local packaging and import commands, not an unattended worker.**
This protocol is **separate from and not interchangeable with** the established
`guide-export` / `guide-import` **combined** guide ZIP contract. Accepted
legacy guide Issue #12 and every existing translation ZIP remain valid.

## Which operations?

- `work_analysis` generates **one original-language-independent Markdown work
  reference** using versioned [work-analysis instructions](../prompts/work-analysis.md).
  Its result lives under `books/WORK/reference/`.
- `target_guide` generates **one work-and-target-language Markdown terminology
  and stylistic guide** using versioned
  [target-guide instructions](../prompts/target-language-guide.md).
  It can include a pinned work reference, if one exists. Its result lives under
  `books/WORK/editions/TARGET/reference/`.

These are editorial reference materials, **not translations**, human approvals
or automatically enforced one-to-one terminology schemas. The model gets all
validated structured source labels and prose, the exact rendered prompt,
applicable work/target notes, and the selected work-reference version.

## Read-only planning

```sh
./ctp guide-task-plan
# Or independently:
python3 tools/guide_task_planner.py
```

This detects missing work guides and target guides from accepted `queue.json`
languages, existing saved `reference/current.json` pointers, and outstanding
legacy combined requests. Repeated planning submits **zero** relay jobs and
does not persist a new task queue.

**Present example:** Gutenberg #36 (Wells) has Japanese only; Korean has **not**
been requested. Accepted guide Issue #12 still covers *both* the Wells work
guide and Japanese guide through the **legacy combined** protocol. The normal
planner therefore does not propose either as a duplicate. Process Issue #12
through its existing `./ctp guide-export --issue 12 ...` commands, or explicitly
decide how to retire/reconcile it before generating replacement guides. Do not
mistake this new standalone protocol for an Issue #12 response format.

## Independently package a task

For a work that the planner labels `proposed`:

```sh
./ctp guide-task-export work_analysis gutenberg-41445 \
  --output build/frankenstein-work-analysis.zip

# Once its work guide has been imported, and a target is requested:
./ctp guide-task-export target_guide gutenberg-41445 --target en \
  --output build/frankenstein-en-guide.zip
```

The requested ChatGPT model **defaults to `6 Extra High`**. Override explicitly
with `--model 'OTHER UI LABEL'`; this is a requested setting, not evidence of
which model actually executed. `--attempt initial` is the initial deterministic
identity. To regenerate a previously saved guide, supply an explicit new
`--attempt revision-2` **and `--force`**. `--force` also deliberately allows
bypassing the planner's missing-guide/dependency/legacy-request protection;
it does **not** bypass source admission, accepted language checks or ZIP
validation. A target guide can be forced before a work reference exists, but
the package honestly records that none was supplied.

The exporter writes only the exact ZIP path you request. It never copies it
to the relay input folder. Moving a ZIP into the external relay's watched
input directory **authorizes submission**; do so only for owner-authorized jobs.
The relay operates independently and may be offline.

Request ZIP members:

```text
README.md
input/job.json
input/manifest.json
```

The README includes the requested model and exact expected result filename.
The job includes the original source nodes, source fingerprint, versioned
prompt text and hash, work/target notes, optional pinned work reference,
baseline saved guide pointer, attempt label and requested model. The
manifest pins the canonical job hash.

## Expected return ZIP and import

The model must return exactly:

```text
result.json
guide.md
```

`result.json` must contain the exact schema-1 keys
`schema_version`, `task_type`, `work`, `target` (null for
`work_analysis`), `job_sha256`, `status` (must be `complete`),
`model_label` (observed UI label or `unknown`), and
`guide_file` (literal `guide.md`). The guide itself is organized,
free-form UTF-8 Markdown. An incomplete job cannot be imported.

```sh
./ctp guide-task-import \
  build/frankenstein-work-analysis.zip \
  /path/to/returned/frankenstein-work-analysis-result.zip
./ctp validate
git status --short
```

The **original, unchanged request ZIP** is required for import: it pins the
prompt/source/reference input the model actually received. The importer
rejects a changed source, stale guide baseline, wrong job ID, wrong target,
unexpected/duplicate/unsafe ZIP members, invalid Markdown and conflicting
responses to an already imported job.

Successful import saves `SHA256.md` and
`reference/guide-task-runs/JOB_SHA256.json` provenance containing the pinned
rendered instructions, notes, source and prompt fingerprints, requested vs
observed model, response and output hashes. Then it atomically updates
`reference/current.json` as the final publication *pointer within the repo*
(not reader publication). Old guide versions remain intact. Re-import of the
identical response is idempotent; a conflicting result for the same job is
rejected. Import performs no `git commit`, push, catalogue change, browser
submission or model call.

Generated guides are AI-assisted **draft reference materials**, not
independently checked source truth or approved editorial decisions.
Do not commit material whose rights/distribution status is unresolved.

## What is still missing

The normal Admin flow does **not yet** issue independent guide requests, and
there is no persistent independent guide queue, automatically scheduled
relay coordinator, Git publication helper, or end-to-end physical browser
verification. The next milestone in [the roadmap](automation-roadmap.md) is
an owner-authorized local coordinator with durable attempt state and safe
reconciliation. The ordered two-pool material UI is a later milestone.

Unit tests exercise offline request/response ZIPs; actual model quality,
context capacity, local relay availability and macOS wake/restart behavior
require explicit live verification.
