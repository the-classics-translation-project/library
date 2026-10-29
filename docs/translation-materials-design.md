# Ordered translation materials — library, selection UI and assembly design

**Status (2026-10-29): initial library and two-pool Admin selector are implemented;
new v2 requests pin the empty or ordered Applied stack, with no implicit optional
notes/guides. A compatible unified v2 translation return ZIP is implemented and its
Issue-based live round trip succeeded with Wells Japanese Issue #30; the direct
v2 variant and remaining guide-format consolidation are still open.** This records the owner's current direction after discussion of
reusable prompts, whole-work guides, language-specific conventions, independent
retranslation and ZIP-based ChatGPT processing. It is intentionally a design
baseline, not a claim that the exact interface or output format has been finalized.
Current implemented commands and formats remain authoritative in
[translation ZIP workflow](translation-zip-workflow.md) and
[local browser relay usage](chatgpt-relay.md).

The implementation discovers repository materials through
`materials/manifest.json`, versioned recipes, work/edition notes and imported
content-addressed guides. Public Admin embeds titles, scopes, kinds, tags and
hashes only for committed files. Selecting materials creates a v2 Issue request that pins their
order and versions; acceptance copies their complete text into the local queue.
`translation-preview ISSUE` writes the exact assembled text used in the ZIP.
The direct `relay-package` adapter accepts ordered `--material ID@SHA-256`
arguments and stores its assembled input both privately and in the ZIP.
Existing v1 requests and both return ZIP protocols remain readable. The owner's
2026-10-28 [standing draft-distribution policy](automatic-draft-distribution.md)
allows validated imported guides to be committed and pushed automatically.
Until an actual push and site rebuild, uncommitted guides remain absent from
public Admin; a local direct package can select them. A browser preview of
private full text is not offered by Pages.

The complementary [three-type task model](relay-task-model.md) distinguishes original-work analysis, target-language guide generation and translation. The shared material selector is to serve all three, with operation-specific mandatory output contracts; the existing combined guide operation stays available for historical compatibility.

## Goal and mental model

A translation task is defined by:

1. An **admitted, structured work** and a target language/edition.
2. **Selected source nodes/fields**, preserving their stable opaque IDs and
   larger reading order, with missing-only or full-retranslation intent.
3. An **ordered list of selectable, versioned translation materials**.
4. Optionally, an **exact frozen earlier translation** to consult rather than
   silently inheriting its wording.
5. An **automatically applied execution/output contract** appropriate to the
   selected ZIP adapter, with all actual inputs and outputs recorded.

A material can be a human-written Markdown/text document, a reusable instruction
template, or a generated and subsequently edited reference guide. The owner
adds/edits material files in Git, commits them, and the next successful site build
refreshes their *discovery metadata*. No browser-side prompt editing/database,
separately billed model API, or new translation scheduler is required.

The concept is **an ordered transfer list** (also called a dual-listbox or
picklist): *Available materials* on one side, *Applied materials* on the other.
It replaces the current one-recipe dropdown and overlapping coarse reference
choices once the shared workflow is implemented.

## Four applicability scopes

| Scope | Applicable when | Example |
| --- | --- | --- |
| **General** | Every translation task | Contemporary literary approach |
| **Target language** | The target language/tag matches | Natural Japanese dialogue |
| **Work** | The canonical work ID matches | Wells character/relationship reference |
| **Work + target language** | Both work ID and target match | Japanese terminology for Wells |

For the current one-source-package-per-work model, a work already establishes its
source language. Thus *work + target language* is the practical language-pair
scope; there is no need for a separate source-language category yet.

Keep **scope** separate from **type** and optional **tags**:

- **Instruction:** directs translation behavior, stylistic goals, or decisions.
- **Reference:** descriptive material, such as a character guide, glossary or
  established spelling/terminology. The model should use it as context, not
  execute arbitrary instructions found in source text or generated references.
- **Tags:** optional descriptive filters (e.g. `style`, `dialogue`, `names`,
  `glossary`, `experimental`, `generated`). They do not independently determine
  scope or grant publication rights.

The owner may author language-independent instructions with simple supported
variables such as `{{target_language}}` and `{{work_title}}`, or maintain
explicitly language-specific alternatives. File metadata/discovery must be
deterministic and validate scope/type/IDs; it should not depend on a model
interpreting filenames. The initial layout uses `materials/manifest.json` for
custom files under `materials/files/`, alongside convention-based discovery of
the existing notes, recipes and content-addressed guides.

## Guides as selectable versioned reference documents

The existing guide generation returns **two organized Markdown documents**, not
machine-readable term rows:

- **Work reference:** source-wide character, setting, relationship, concept and
  narrative information, applicable in every target language for that work.
- **Work + target guide:** terminology, spellings, register and useful contextual
  alternatives for a particular target language/edition.

A successful, reviewed/imported guide should appear in the corresponding
material scope **without hand-copying its contents into a second prompt file**.
Likewise, human-edited work-specific notes or target-language instructions
should be discoverable through the same materials library.

A material needs a **stable logical identity** independent of its content hash;
one logical document may have successive immutable versions. Generated guide
versions already have content-addressed Markdown and `current.json` pointers
under `books/<work>/reference/` and
`books/<work>/editions/<edition>/reference/`. The newer direct relay additionally
uses `editions/<edition>/glossary.md`. These are currently **distinct stores**,
not synchronized. Plan an explicit discover/migrate/compatibility path so a
generated guide, a hand-edited successor and a deliberate fork are not silently
merged or mistaken for the same document.

A regenerated guide should usually be a **new revision of the same logical
material**, leaving old versions available; a deliberately different editorial
approach may fork/duplicate the material. Do not demand a rigid glossary schema,
one-to-one term mapping, or automatic mechanical term substitution. Separate
established decisions from provisional suggestions in the prose.

## Admin interaction: two pools and ordering

After the user selects a work, target language and source nodes:

**Available materials** lists all applicable library entries, regardless of
whether they are human-written or generated. It supports search/filter by
scope/type/tags. Each entry displays a title, brief description if available,
scope, type and version/availability status, not a huge full-text dump. Changing
the work or target recomputes applicability and makes incompatibilities explicit;
do not silently attach wrong-language references.

**Applied materials** is an **ordered sequence**, not a set:

- Add from Available to the end (or a clearly indicated position).
- Remove back to Available; even automatically suggested entries can be removed.
- Reorder by drag-and-drop when supported, with accessible **Move up/down**
  controls for keyboard and touch. Expose actual order to screen readers.
- Avoid duplicate inclusion of the same logical document/version unless a
  deliberate future use case justifies it.
- Suggested initial contents can include a general default approach, the
  existing work reference and the work-target terminology guide. These are
  **defaults, not mandatory inherited instructions**. An explicit removal stays
  removed within the user's configuration; rebuilding the UI must not re-add it.
- Preserve deliberate user edits to the stack and preview. Optionally store
  reusable stacks/presets later; not required for the first implementation.

Keep existing source-node selection, translated-field coverage and independent
retranslation available. **Prior translated prose is a special optional
reference**, selected by *exact frozen revision*, not an automatically inherited
glossary. The user must be able to request a new translation without exposing
older wording, while still selecting neutral work-level background.

## Full assembled-input preview

The user should be able to inspect **the actual resolved input before
submission/relay delivery**, not just filenames:

1. The selected materials' **complete text in user-specified order**, with
   variables resolved and clear boundaries/labels between instruction and
   reference material.
2. Any explicitly selected earlier translation or neighboring source context.
3. The actual selected source labels/prose and node IDs, in source reading order.
4. The exact final operational/output instructions, including the required
   machine-readable identity and return ZIP format.

Offer **Preview assembled input**, **Copy** and/or **Download exact input**.
For long texts, collapsible sections are fine, but the actual downloadable
input must not be silently truncated or paraphrased. The preview must reflect
the **same deterministic assembler** that creates the real task ZIP, not a
parallel browser approximation with different variable substitution/order.

**Public-site constraint:** GitHub Pages Admin is public. It can discover
safe material titles/scope/tags and explain selections, but must not publish
unapproved translated draft text or reference revisions merely to make a
convenient preview. Where a complete preview needs local/private draft inputs,
show the full preview at an authorized **local packaging/review step**. The
public frontend must not be mistaken for an authentication boundary; GitHub
Issue intake still validates the actual submitting maintainer.

## Final output contract: fixed protocol, not editorial preference

A last-position **output specification** is desirable, but shouldn't be an
ordinary removable literary prompt. **Recommended first implementation:**
automatically append an inspectable, nonremovable *protocol-owned* output
contract after the chosen editorial materials and source. The UI may display it
as a locked final row, but reordering/removing literary documents cannot break
the ZIP importer. Whether that row is always shown or only expanded in the
preview is a presentation detail still open.

The original implementation had two distinct return contracts:

- Issue-based `translation-export` / `translation-import` expects a ZIP with
  `response.json` containing translated text strings mapped by source node/field.
- Direct `relay-package` / `relay-import` expects `result.json` plus separate
  `text/NODE-ID.md` files and editorial `glossary.md` / `notes.md`.

The compatible [version 2 unified return ZIP](unified-translation-zip.md) now
uses a JSON identity/coverage manifest and separate Markdown label/body files
for both adapters. It has offline tests; a live return remains to be verified.
Record model attribution, stable IDs, expected fields and output hashes; reject
missing/extra fields and unsafe ZIP members. Keep adapters or a defined
migration path for already accepted Issues and previously exported ZIPs.
Preserve the proven strict import checks, stale-input guards and rollback
behavior. Do not arbitrarily replace a working protocol before a complete
end-to-end trial.

## Pinning, provenance and history

For each accepted translation request, preserve:

- Canonical work, target edition/language, selected nodes and source
  fingerprint; include the requested translation scope and optional exact
  prior revision.
- The **ordered list** of materials, with logical IDs, type, applicable scope,
  specific immutable version/hash and the **exact contents used**.
- The rendered/expanded assembled instructions and source/context that the
  model really received (not just a current filename or reconstructed prompt).
- The exact output contract/adapter version, model/interface actually observed,
  the return ZIP/job identity, and output hashes.
- Old snapshots, reports and meaningful notes. Retranslating a node may produce
  a new version but never retroactively changes what an earlier run meant.

Pin the selected documents when the request is **accepted**; edits and new
glossary generations after acceptance must not silently alter an existing job.
If the user modifies the selection before submitting, preview the new
configuration. If the source/edition changes materially before execution,
explicitly reject or reconcile stale jobs rather than silently pulling
different prose or a different glossary. No statement about literary fidelity
or human review follows merely from complete metadata.

## Implementation phases / acceptance criteria

1. **Material discovery/metadata:** common read-only library spanning the four
   scopes and two types, with safe tags, content hashes, version references and
   generated guide registration; preserve existing documents and pointers.
2. **Shared assembler and tests:** resolve variables, filter eligibility,
   preserve sequence, delimit untrusted source/reference data and produce
   a byte-identical preview/export. Keep the direct relay and Issue-driven
   workflow behavior compatible while building it.
3. **Ordered transfer-list UI:** two pools, filters, suggested but removable
   defaults, reorder controls, prior-translation revision selection, and
   explicit final contract/assembled input preview.
4. **Versioned request payload:** record source and ordered material identities
   and snapshots. Maintain authorized GitHub Issue intake; don't change
   previously accepted Issue meaning or expose unapproved draft prose in Pages.
5. **Output-format consolidation:** choose and verify one canonical ZIP return
   contract (likely JSON metadata + Markdown prose), with backward compatibility,
   integration tests, malformed ZIP tests and an actual local ChatGPT-relay
   end-to-end experiment.

Do **not** implement a template programming language, automatic prompt
conflict resolution, automatic AI invocation, direct public editing of private
drafts, or mandatory PR workflow merely to implement material selection.

## Still-open design choices (after initial implementation)

- The initial path and metadata mechanism is now implemented via
  `materials/manifest.json` and `materials/files/`, plus discovery of existing
  recipes/notes/guide pointers. **Still open:** richer lifecycle/version identity
  for human-edited successors, regenerated guides and deliberate forks.
- Whether applied material stacks have named reusable presets.
- Whether the fixed output-contract row is always visible or only in preview.
- Full transition of historical and guide ZIP contracts to the compatible v2
  translation format; do not retire either legacy importer until verified.
- How best to preview complete local draft/source inputs from a public static
  Admin page without leaking unapproved text.

These decisions should be tested with one real guide and a few actual
translation/retranslation packages before adding framework complexity.
