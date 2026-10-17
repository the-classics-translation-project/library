# Status — version 0.1.0

Last verified: **2026-10-17** (against the public GitHub repository and actual
GitHub Actions results). This file describes observed state, not a roadmap or a
claim that the software and literary workflows are finished.

## Repository and live services

- Canonical repository: <https://github.com/the-classics-translation-project/library>
  (public; default branch `main`). Work from its current files and
  [AGENTS.md](AGENTS.md), not an earlier conversation archive or starter ZIP.
- GitHub Pages: <https://the-classics-translation-project.github.io/library/>.
  Reader catalogue, contributor workbench and administrator intake interface
  are generated separately; Admin is at
  <https://the-classics-translation-project.github.io/library/admin/>.
- GitHub Actions **validation/build** and **Pages build/deployment** succeeded on
  2026-10-17:
  [validation run 39032202747](https://github.com/the-classics-translation-project/library/actions/runs/39032202747)
  and [deployment run 39032202765](https://github.com/the-classics-translation-project/library/actions/runs/39032202765).
  Successful deployment was confirmed by GitHub Actions; this status record is
  not a substitute for independent browser checks of every live interaction.
- Project Gutenberg's official CSV catalogue was downloaded, parsed and
  committed by the
  [catalogue refresh workflow](https://github.com/the-classics-translation-project/library/actions/runs/39031721097)
  on 2026-10-17: **79,576 catalogue records** at that refresh. The administrator
  search uses this cache, not the original three-record seed. Refresh is
  configured weekly (Monday 03:23 UTC), as well as manually.
- Authorized GitHub Issue intake has executed successfully:
  [Issue #6](https://github.com/the-classics-translation-project/library/issues/6)
  was accepted and recorded in `queue.json`. A subsequent workflow change
  configured Pages to rebuild when later intake runs add queue entries;
  the current public queue was redeployed in
  [deployment run 39032202765](https://github.com/the-classics-translation-project/library/actions/runs/39032202765).

## Literary work and requested editions

`queue.json` currently has **two requests/candidates**:

1. **Project Gutenberg #41445 — `gutenberg-41445`** (*Frankenstein*,
   1818): English (`en`) target; initial candidate from the founding
   discussion, not an Issue-submitted request.
2. **Project Gutenberg #36 — `gutenberg-36`** (*The War of the Worlds*):
   **Japanese (`ja`) only**, added through
   [Issue #6](https://github.com/the-classics-translation-project/library/issues/6).

Neither source has been acquired or structured. On the PR #7 branch, `books/`
contains automatic rights assessments and RDF evidence for both queued candidates;
those checks held both requests without retaining literary source text. **No real literary translation
has begun or been approved.** The `revisions/` material consists of synthetic
test/example snapshots and preserved legacy fixtures. `catalog.json` has an
empty distribution list, so there are **no approved reader or review editions**
available for download yet. The deployed web application and catalogue are not
the same thing as published books.

## Software implemented

- Source-package-per-work convention; schema-v2 ordered source trees with
  mechanical opaque node IDs, optional labels/prose, arbitrary nesting and
  text on branches. Translation preserves the larger source tree without
  mandatory sentence/paragraph alignment.
- Source acquisition and reversible block preparation; an AI can propose
  block-reference structures while code validates coverage/order and copies
  text mechanically, preserving original bytes and provenance.
- Draft coverage inventories, translated labels and body text, immutable
  revision-bound snapshots and review reports. Schema-v1 historical snapshots
  remain supported. Full retranslations need not preserve prior prose structure.
- Git-versioned prompts, work/edition notes and generation records that capture
  the exposed model label, exact supplied instructions, source/note fingerprints
  and generated output hashes. These are provenance records, not guarantees
  of reproducibility or literary quality.
- Reader/HTML and EPUB build machinery; contributor selection annotations,
  popup comment editing, marginal notes and multi-selection reports; token-free
  administrator search, language selection and Issue preparation.
- Strict maintainer-authorized, additive Issue intake; a reproducible queue
  and `./ctp task` brief for interactive agents. **No unattended model
  translation worker or separately billed model API is required or configured.**

## Verification and limitations

- The latest verified CI run passed **64 Python tests**, **9 legacy JavaScript
  checks** and **10 schema-v2 annotation checks**, plus the sample-preview
  build. The previous Pandoc footnote `<aside>` compatibility failure was
  corrected before these successful runs.
- Earlier local isolated-Chromium tests passed 13 interaction checks,
  including selection, headings, overlapping annotations and tablet/phone
  layouts. Those used simulated storage because browser navigation was
  restricted: **live browser storage persistence, Safari/iPad native text
  selection, and cross-device behavior remain unverified**.
- Sample EPUB ZIP/XML/navigation checks are **not EPUBCheck certification or
  Kindle rendering tests**. HTML/EPUB literary presentation requires inspection
  with real books and target-language typography.
- The importer presently targets UTF-8 TXT/Markdown, not general scan/OCR,
  illustrated layouts or arbitrary source formats. Existing trees are not
  silently reimported or renumbered. Copyright/source-edition identity and
  translation fidelity still require judgment and evidence.
- There is no selected blanket license for code/translation materials, no
  approved literary release, no automated KDP submission and no scheduled
  fresh-context translation invocation.
- **Documentation cleanup remains:** `README.md`, `docs/setup.md` and parts
  of `docs/maintainer-workflow.md` still describe the pre-deployment seed
  catalogue or missing GitHub deployment. This `STATUS.md` records the verified
  newer facts; reconcile those documents separately rather than relying on
  their stale status assertions.

## Next useful work

1. Acquire and verify an actual Gutenberg source package (including relevant
   rights/edition details), construct its source tree, and validate coverage.
2. Make and record the first real draft translation with an interactive agent;
   use work-specific and target-language notes, and do not promote the draft
   to the public reader catalogue without explicit editorial approval.
3. Inspect the live reader/contributor/admin interfaces on intended browsers,
   check EPUBs with EPUBCheck/readers, and update the stale setup documentation.
4. Decide whether and when to add isolated fresh-context agent invocations;
   do not require them for ordinary manual/interactive work.

## Acquisition automation revision — PR #7, 2026-10-18 (not deployed)

The intake workflow now checks a versioned, conservative US/Japan admission policy.
Passing English UTF-8 packages are preserved permanently under `books/` and staged
with their exact-byte/block hashes, source provenance, rights decision and RDF
evidence. There is no expiring acquisition artifact or owner confirmation per book.
Missing/unsupported evidence or unresolved contributions produces a durable hold
with reasons; no source text is committed for those cases. Network errors preserve
other successes and report failure after the records are saved. The policy is in
`docs/automatic-source-rights.md`; it is not worldwide or human/legal clearance.

A live metadata assessment on this branch held both current candidates:

- `gutenberg-36`: the provider supplies no original source-publication statement.
  Its Gutenberg release date is not evidence of the historical source edition.
- `gutenberg-41445`: the provider credits say “Revised by Richard Tonsing.” The
  first rule cannot resolve the separate contribution from that statement.

Both have an explicit US public-domain designation; the holds concern the Japanese
source-admission evidence/scope. Source prose was not acquired by this revised live
queue run. The saved decisions do not assert that either book remains copyrighted.
No literary tree or translation has been generated and `catalog.json` is unchanged.

Local verification: **94 Python tests**, **9 legacy JavaScript checks** and
**10 schema-v2 annotation checks** passed, along with project validation, the sample
HTML/EPUB build and workflow YAML/embedded-script parsing. A real in-app browser
opened the generated Admin page over local HTTP, expanded both hold explanations
and confirmed their text; no browser error logs were recorded. This checks the
new queue display, not Safari/iPad selection, annotation storage or every browser.
No live run of the revised intake workflow or remote source-acquisition deployment
is claimed.
