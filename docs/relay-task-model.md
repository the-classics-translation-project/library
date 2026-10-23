# Three task types for ChatGPT ZIP exchange

**Status:** implementation plan and versioned prompt templates. The two existing ZIP adapters remain authoritative; this document does **not** imply a shared queue, new importer, or automatic execution has been implemented.

## Boundary

The Classics Translation Project owns task discovery, eligibility, reference selection, prompt assembly, acceptance of results, and provenance. The separately installed `chatgpt-relay` is a transport: it submits an owner-authorized ZIP to ChatGPT and downloads the corresponding ZIP. It must not infer literary task semantics from filenames or manage editorial decisions.

Distinguish **creating a pending task** from **authorizing its submission**. A deterministic local planner may propose tasks without invoking a model. Copying ZIPs into the relay's watched input directory is an actual submission authorization and requires the owner's explicit policy/request. No new model scheduler or API billing is authorized by this design.

## Operations

| Stable proposed type | Key | Required source | Primary result | Typical trigger |
| --- | --- | --- | --- | --- |
| `work_analysis` | Work ID + source fingerprint + selected input/template versions | Complete admitted structured original | Language-independent work reference Markdown | First source-tree preparation |
| `target_guide` | Work ID + target language + source fingerprint + selected input/template versions | Complete original and optionally the pinned work reference | Work/target-language Markdown guide | Target language added to an admitted structured work |
| `translation` | Work ID + edition/target + selected node fields + exact inputs | Selected source fields and applied materials | Translated labels and bodies | Owner requests translation/retranslation |

These are *operations*, not styles or recipes. Each can use differently versioned prompts and an ordered material stack. Source descriptions are **reference data**; they are not instructions with permission to override the operational contract.

### Work analysis

Read the **entire** structured source, including its ending, and document names, relationships, geography, recurring concepts, narrator, chronology, ambiguities and useful node references. Do not translate it into a target language. This guide belongs to the **work**, not an edition. If context limits prevent complete analysis, report that limitation explicitly; do not mark a partial guide as comprehensive. Versioned prompt starting point: [`prompts/work-analysis.md`](../prompts/work-analysis.md).

### Target-language guide

Use the original, the target language and the *specific immutable version* of the work reference when supplied. Describe translation choices for names, recurrent terms, voices, styles and registers, with contextual alternatives and distinctions between established decisions and suggestions. It belongs to a **work + target-language** scope; it is not automatically an edition-specific binding glossary. A guide may be generated before the work reference is available, but the absence must be recorded. Versioned starting point: [`prompts/target-language-guide.md`](../prompts/target-language-guide.md).

### Translation

Operate on explicit node/field selections with an ordered, pinned stack of applicable instructions and references; translate labels as well as source bodies. Old translated prose is supplied **only when explicitly selected** from a frozen revision. AI-produced glossary suggestions do not become editorial decisions without a separate adoption policy. See [ordered materials design](translation-materials-design.md).

## Initial task discovery (proposal, not active automation)

- On the first validated, admitted source-tree completion, **propose** one `work_analysis` task if no matching completed guide exists and no equivalent pending/submitted task exists.
- On adding a target language, **propose** one `target_guide` task for that work/target if not already completed or pending. Never regenerate the language-independent guide once per language.
- The proposals are idempotent by canonical key, do not publish results, and do not enqueue a relay ZIP automatically. A failed attempt can be retried deliberately with a new attempt identity; a changed source fingerprint renders old queued results stale.
- Existing guides should be adopted/discovered, not silently regenerated. Later source edits or deliberate editorial revisions should require explicit regeneration or a separately authorized policy.
- A target guide may depend on a successful work analysis for the default sequence, but this is **soft**, not an absolute gate. Translation itself must remain possible with no guides.

## Conceptual queue and lifecycle (not yet a persisted schema)

```json
{
  "task_id": "example-id",
  "type": "target_guide",
  "work": "gutenberg-36",
  "target": "ja",
  "source_fingerprint": "<sha256>",
  "material_versions": [],
  "status": "pending"
}
```

Suggested states: `pending → packaged → submitted → returned → validated → imported`, with explicit `failed`, `needs_review`, and `stale` exceptions. Track *request identity* separately from *attempt identity* so retries cannot masquerade as successful originals. Preserve exact input bytes, model choice requested vs. model observed, output hashes, reference versions and the actual adapter contract. Model-generated documents must never be marked as human-reviewed merely because ZIP validation passed.

The project queue, if implemented, is distinct from the relay's transport status ledger. No task is considered imported merely because relay download was completed.

## Compatibility and migration

Today `guide-export` / `guide-import` perform a **combined** work+target guide task and expect a ZIP containing only `response.json` with both `work_guide` and `target_guide`. The existing accepted guide Issue #12 and historical requests **must continue to work**. Treat this as a `legacy_combined_guide` *adapter operation*, not a fourth canonical task type; it may produce two independently discoverable materials.

Today `translation-export` / `translation-import` expect a different single-`response.json` ZIP from `relay-package` / `relay-import`, which expect `result.json`, Markdown bodies, `glossary.md` and `notes.md`. Do not alter either importer or claim interchangeability. The eventual unified transport protocol should carry explicit `task_type`, a versioned output contract, input manifest hash, declared output artifact types and strict safe-member validation. Define the exact layouts through tests, then add compatible import adapters.

Recommended incremental implementation:

1. Keep the existing accepted guide request contract operational. Add standalone prompt templates for work analysis and target-language guidance; these are **not** yet registered as selectable runnable ZIP task types.
2. Implement a read-only, deterministic discovery/planning command with idempotent canonical task keys, including seeded fixtures, missing-guide cases, stale source and no-submission tests.
3. Add new packaging/import support for one guide type at a time, with explicit per-type output validation, content-addressed Markdown, current-version pointers and provenance. Never overwrite or erase existing guide versions.
4. Integrate those operations with the shared ordered-material assembler, then connect an authorized local queue to the existing relay transport.
5. Exercise one real round trip for each type before enabling any opt-in automatic submissions; check rollback, no-op polling, idempotent retries and no accidental publication.

This project does not need a mandatory GitHub Issue for each owner-directed local task. Authorized Issue intake remains one optional request-entry path.

## Acceptance checklist for a future implementation

- Adding one work and three target languages proposes **one** work analysis and **three** target guides; repeated discovery proposes no duplicates.
- The first pending guide does not silently submit itself; no-model, no-op planning succeeds.
- Each guide is independently regenerable with a new immutable version; old approved/editorially used references remain available.
- Changing source bytes or a pinned material does not silently rewrite an already accepted task.
- Incomplete whole-work examination is visible; strict ZIP validation does not claim literary accuracy.
- Legacy guide Issue #12 and both existing translation ZIP formats remain importable.
- Full assembled input can be inspected using the same deterministic assembler as the real exported job, without leaking private drafts to public Pages.
- No generated document updates `catalog.json` or authorizes reader publication.
