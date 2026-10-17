# Decision record

These are working decisions from the founding discussion, not permanent rules.
Dates below describe the conversation's local calendar date.

## 2026-10-16 — Source packaging is the default work boundary

Use the source provider's package (such as one Project Gutenberg ebook) as the
ordinary unit of work. Internal volumes, books and parts do not automatically
become separate works or separate EPUB products. This is a convenience rule, not
a claim about abstract literary identity. Handle anomalous packages case by case.
Keep exact provenance rather than trying to classify all historical editions now.

## 2026-10-16 — Source structure is an arbitrary ordered tree

A node can have an optional label, optional text, and children. Both labeled and
unlabeled nodes are valid; a node can contain its own text and children. Translate
source labels, including the root/book title and internal headings, as well as
body text, but do not invent missing headings. Preserve the larger tree and order
without constraining prose segmentation or translation batch sizes. The model is described in [source-structure.md](source-structure.md).
It was initially a proposal; schema v2 implements it in version 0.1.0.

## 2026-10-16 — Use mechanical, opaque source node IDs

IDs should encode no terms like `volume` or `chapter`, nor the node's current
position or visible title. Assign once during source import and retain across
translations, corrections and retranslations. Do not renumber on subsequent
imports; allocate new IDs when new elements must be distinguished. The mapping,
not a regeneration algorithm, is the durable reference.

## 2026-10-16 — Keep edition packaging simple

Default to one translated EPUB/HTML reading edition for the whole imported source
package while preserving internal divisions. Postpone a separate configuration
for selling or distributing arbitrary subsets. Publication packaging is not the
core text structure. This decision may be revised for a real book that requires it.

## 2026-10-16 — Titles and headings are reviewable text

Reader-visible edition text supports annotations, including
the book title and internal division labels. Historical annotations cite an exact
revision and a node field, not an assumed permanent sentence. The initial demo supported only body text; the v0.1 schema-v2 workbench
now supports labels, body fields and bibliographic credits. Legacy snapshots keep
their original field model.

## 2026-10-16 — Visible compact marginal notes (UI experiment)

Explore short one-to-two-line notes displayed beside selected passages, with a
click/tap to see their complete text and an option to hide editorial marks. Keep
selection-triggered entry and the comfortable reader-first page. This remains a
preference to test through use. The v0.1 workbench now implements it, with a menu
toggle and phone-width fallback.

## 2026-10-16 — Reader and contributor routes are separate

Readers chiefly need a catalogue with HTML/EPUB links. Contributors need comfortable
reading plus annotation. A common entrance does not imply one UI or private access.
Reuse lessons from yomi-corpus and nippo-jisho, not their sentence/line task models.

## 2026-10-16 — Review the version, not a permanent sentence

Translations can be replaced wholesale when style preferences or models change.
Attach feedback to frozen revisions with quoted evidence. Do not constrain later
wording, sentence counts or paragraphing to preserve old annotation units.
Alternative rejected: permanent one-to-one aligned passages as the core data model.

## 2026-10-16 — The contributor reports; the maintainer decides

Multiple comments may become one Issue. A contributor need not propose a fix.
The maintainer and AI may choose a word change or a new translation. Do not design
automatic Issue-to-patch ingestion merely because it worked for transcription.

## 2026-10-16 — Minimal literary policy, detailed operating instructions

Use the contemporary-target-language-author thought experiment. Structural
adaptation is outside present scope; choose works suited to the purpose instead.
No assertion that any named classic is objectively unsuitable is adopted.

## 2026-10-16 — Start with one library repository

Share build tools and documentation. Keep per-work/edition files separate. No
contributor recruitment, deadlines or general-purpose platform commitment.

## 2026-10-16 — Small frozen text packages in Git

Store text, Markdown and rendered HTML in content-addressed snapshots so historical
feedback can be recovered after UI or renderer changes. Build distributable HTML
and EPUB from those packages. Reconsider storage before it becomes burdensome.
Alternative deferred: a dedicated immutable object store.

## 2026-10-16 — JSON metadata, Markdown prose, Pandoc conversion

Choose dependency-free metadata parsing and an established document converter.
The earlier YAML suggestion was provisional. The minimal implementation need not
make metadata format or generation strategy a permanent project identity.

## 2026-10-16 — No implicit publication

CI may validate anything submitted. Pages builds only the distribution allowlist
and has manual deployment plus explicitly enabled follow-up deployment from
metadata/queue workflows. This does not promote drafts or approve new books. Demonstration content is explicitly opt-in. Actual book
approval, licensing and KDP submission are separate owner decisions.

## 2026-10-16: Quiet contextual annotations (provisional)

The contributor interface is a reader with optional annotation, not a mandatory
step-by-step editing form. Selecting text opens a small nearby comment popup;
saving creates a subtle inline mark whose comment reopens on click or tap.
Details and help live behind the menu. Overlapping annotations and arbitrary
cross-paragraph spans remain permitted. An annotation belongs to an immutable
revision; displaying the mark must never mutate the frozen text or its offsets.
This can be revised after real use on phones and tablets.

## 2026-10-16 — Interactive intelligence, reusable mechanical commands

Prefer using the owner’s existing interactive model allowance before building a
paid API pipeline. The repository remains operable without either service. A task
brief is not a scheduled agent. Model scheduling/budget is separate configuration.

## 2026-10-16 — Capture prompts, model labels and evolving editorial memory

Reusable prompts live in Git; substantial generation records capture exact prompt
and note content, exposed model/interface, source identity and output hashes.
Unknown model internals stay unknown. Work-level and edition-level notes retain
useful findings across wholesale retranslations. Provenance is not reproducibility.

## 2026-10-16 — Administrator intake without manual metadata editing

Use official Gutenberg metadata to search titles/authors/IDs, select targets and
prepare an Issue. The public frontend has no credentials. A trusted parser accepts
only configured maintainers’ structured requests and merges them into a queue.
The queue records intentions; current files record actual progress. A three-record
seed is identified as such until the official CSV is successfully downloaded.
