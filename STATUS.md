# Status — version 0.1.0

Built locally on 2026-10-16 from the third starter package and the subsequent
project decisions. This is a working repository with implementation and tests, not
only a proposed file layout. **It has not been created or pushed on GitHub.**

## Implemented

- Schema-v2 ordered source trees with opaque mechanical IDs, optional labels/prose,
  arbitrary nesting and text on branches; same IDs across target editions.
- Reversible source-block preparation, AI reference-plan compilation, exact coverage/
  source-order checks, raw-source retention and first-import ID allocation.
- Draft missing-field inventories; title/heading translation; immutable snapshots
  containing source and target rendering, tree, metadata and provenance.
- Preserved schema-v1 snapshot/report compatibility without changing old hashes.
- Version-controlled prompts, compact model/prompt generation records, source hashes,
  captured policy/work/edition notes and output hashes.
- Separate reader catalogue, annotation workbench and administrator catalogue/queue.
  Title/heading/body annotations, selection popovers, overlapping highlights, compact
  persistent marginal notes, multi-section reports, import/export and storage warnings.
- Official Gutenberg CSV parser/fetch command, local substring catalogue search,
  numeric-ID fallback, target checkboxes and GitHub Issue preparation.
- Strict authorized/idempotent/additive Issue intake, file-derived queue progress
  and a bounded task brief for interactive agents; no model API dependence.
- HTML/EPUB export, local staging, CI/Pages/metadata-intake workflow definitions,
  and an explicit guarded publishing helper.

## Content present

There are no real imported literary works or approved reader publications. The
English/Japanese nested-tree samples are synthetic. The legacy example is preserved.
Gutenberg 41445 (Frankenstein, 1818) is a candidate in the queue, not an imported book.
The catalogue has **three metadata seed records**, not the full Gutenberg catalogue.
Direct source/CSV network downloads failed in this environment; the fetch code is
provided but no live acquisition success is claimed.

## Tests actually run

63 Python tests; 9 legacy JavaScript checks; 10 schema-v2 annotation-core checks.
The isolated Chromium run passed 13 interaction checks: nested navigation, title
and heading comments, mouse selection, cross-paragraph overlapping highlights,
margin editing, restoration from simulated storage, a multi-section report accepted
by the Python validator, fixture submission guard, tablet/phone layouts and valid
admin request preparation. No page JavaScript errors were recorded.

Browser navigation was blocked by the environment. The test therefore used fresh
DOMs and explicitly simulated in-memory Storage. **Real page navigation, true
localStorage persistence, native iPad/Safari selection and cross-device behavior are
not verified.** The code retains backup/export paths and explicit storage warnings.
The sample EPUBs passed ZIP/XML/navigation checks, not EPUBCheck or Kindle testing.

## Remaining boundaries

GitHub write/admin access was unavailable. No remote repository creation, push,
Actions execution, Pages deployment, live Issue intake or hosted catalogue refresh
was performed. The shell helper was syntax/plan checked, not run against an account.
Actions YAML has been inspected locally; runtime permissions and organization policy
still need the first live run.

The initial importer accepts TXT/Markdown only. Existing source trees require an
explicit future migration rather than being silently reimported. Image/scan handling,
automatic source identity/rights verification, fine-grained cross-version alignment,
unattended AI generation and KDP submission are not implemented. No license was
chosen on the owner's behalf and no literary edition was approved.

The next literary task is source acquisition/verification for the first chosen work,
followed by block-plan structuring and an explicitly recorded initial translation.
The next deployment task is running the publishing helper in a write-enabled,
authenticated environment and inspecting the actual workflow results.
