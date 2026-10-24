# Status — version 0.1.0

Last updated: **2026-10-24** (against the public GitHub repository and actual
GitHub Actions results). This file describes observed state, not a roadmap or a
claim that the software and literary workflows are finished.

## Automation roadmap and bounded guide planner — implemented read-only

The owner-facing end-to-end goal, milestones, compatibility constraints, and mandatory cross-session handoff are tracked in [docs/automation-roadmap.md](docs/automation-roadmap.md). The repository includes a read-only `tools/guide_task_planner.py` and offline tests. It proposes missing work/target guides from `queue.json`, existing content-hashed guide pointers and compatible outstanding legacy Issue requests. It makes **no relay, network, model or file-write actions**. Independent per-type guide ZIP implementations, authorized local coordinator and ordered-material UI are not yet implemented; do not infer otherwise from the planner. The live Mac/relay path remains unverified.

## Three ChatGPT task types — documented, not executed

The proposed project-owned task types are `work_analysis`, `target_guide` and `translation`; `chatgpt-relay` remains a ZIP submission/download transport. See [task model](docs/relay-task-model.md) and separate versioned `prompts/work-analysis.md` / `prompts/target-language-guide.md`. The existing combined guide ZIP operation, accepted Issue #12, and both current translation adapters remain unchanged. Automatic *discovery* on source/target addition is proposed, but no task planner, new task-type ZIP handler or auto-submission scheduler was implemented in this branch. Real round-trip verification remains necessary.

## Ordered translation materials — planned, not implemented

The current design direction is an **ordered transfer-list (dual-listbox) UI**
for composing translation requests from versioned Markdown/text materials.
The **Available** pool is filtered by general, target-language, work and
work+target scope; the **Applied** pool is ordered, user-editable, and may start
with suggested but removable guides. Materials distinguish **instructions**
from **reference documents** (glossaries, character guides, terminology).
A complete preview of resolved input is required before relay submission,
including selected source and a proposed fixed final output contract.

A shared material discovery/assembly layer should eventually serve **both**
the Issue-based translation ZIP workflow and the direct browser-relay adapter.
Their current prompt/reference storage and ZIP return contracts **still differ**.
A unified output format (possibly JSON metadata plus Markdown body files)
remains to be chosen and tested. No new UI, prompt assembler, automatic guide
registration or return format was implemented by this documentation update.
See [full design/implementation brief](docs/translation-materials-design.md).
Do not mistake this direction for completed functionality.

## Local relay adapter — 2026-10-23

`./ctp relay-package` and `./ctp relay-import` now prepare explicit translation
packages and validate returned results as drafts, with Markdown glossaries,
stale-input guards, preserved attempts and generation provenance. See
[relay usage](docs/chatgpt-relay.md). This is a browser-relay alternative to the
still-unimplemented CLI translation launcher. No live translation job was submitted
or imported while implementing it; it adds no scheduler or publication approval.
Validation passed locally: 126 Python tests (including 16 relay adapter tests),
19 JavaScript checks, `./ctp validate` and `./ctp build --demo --epub`. These
are offline/software checks, not a browser translation or deployment test.
The repository/service observations below retain their stated verification dates.

## Repository and live services

- Canonical repository: <https://github.com/the-classics-translation-project/library>
  (public; default branch `main`). Work from its current files and
  [AGENTS.md](AGENTS.md), not an earlier conversation archive or starter ZIP.
- GitHub Pages: <https://the-classics-translation-project.github.io/library/>.
  Reader catalogue, contributor workbench and administrator intake interface
  are generated separately; Admin is at
  <https://the-classics-translation-project.github.io/library/admin/>.
- GitHub Actions **validation/build** and **Pages deployment** succeeded for
  source-tree commit `b787dc9`:
  [validation run 39051177283](https://github.com/the-classics-translation-project/library/actions/runs/39051177283)
  and [deployment run 39051177252](https://github.com/the-classics-translation-project/library/actions/runs/39051177252).
  A direct read of the live Admin HTML confirmed both trees in its embedded
  manifest; this does not verify browser expand/collapse interaction.
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

Both Gutenberg sources were **admitted and acquired on 2026-10-17** under
`gutenberg-us-jp-v2`, using the documented per-work citation files. The original
UTF-8 packages, raw bytes, reversible blocks, evidence and hashes are retained in
`books/gutenberg-36/acquisition/` and `books/gutenberg-41445/acquisition/`.
Both works have AI-assisted, mechanically validated source trees. #36 has
31 nodes and accounts for all 981 blocks (920 assigned, 61 explicitly excluded
with reasons); #41445 has 38 nodes and accounts for all 917 blocks (854 assigned,
63 explicitly excluded with reasons). Their imported metadata does not claim
human review or exact historical print-edition verification. **Neither work has
been translated.**
`catalog.json` still has an empty distribution list, so there are **no approved
reader or review editions** available for download.
The deployed web application and catalogue are not
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
- A deterministic local source-work selector, one-work Codex executor, external
  retry ledger, OS lock, isolated Git worktree and guarded publication code.
  A per-user LaunchAgent is installed at a 30-minute interval. The Admin build
  embeds validated source-tree labels and IDs with nested expand/collapse code.

## Verification and limitations

- The source-admission merge was validated by
  [CI run 39043911914](https://github.com/the-classics-translation-project/library/actions/runs/39043911914),
  after the PR had passed **94 Python tests**, **9 legacy JavaScript checks** and
  **10 schema-v2 annotation checks**, plus the sample-preview build. The previous
  Pandoc footnote `<aside>` compatibility failure was corrected before these runs.
- Earlier local isolated-Chromium tests passed 13 interaction checks,
  including selection, headings, overlapping annotations and tablet/phone
  layouts. Those used simulated storage because browser navigation was
  restricted: **live browser storage persistence, Safari/iPad native text
  selection, and cross-device behavior remain unverified**.
- [PR #9](https://github.com/the-classics-translation-project/library/pull/9)
  passed **110 Python tests**, **9 legacy JS** and **10 schema-v2 JS** checks,
  `./ctp validate` and `./ctp build --epub` locally; its GitHub checks and Pages
  deployment passed after merge. A synthetic acquired work completed the mock
  one-work path without network or model use. A real Codex CLI invocation
  structured #36 in an isolated worktree; the full wrapper then structured
  #41445, validated the exact diff, and pushed
  [commit `b787dc9`](https://github.com/the-classics-translation-project/library/commit/b787dc9a5d938b5768e26ff4611e2913bb16cb4c).
  Both GitHub workflows passed, the worker ledger reconciled to `complete`, and
  an idle re-run returned `pending: []` with `model_called: false`. The
  ChatGPT.app-bundled Codex CLI 0.162.0 passed a read-only login/model smoke test;
  the older global 0.46.0 CLI failed with this account's configured model.
  The live Admin manifest contains both trees without full literary prose, but
  **the new tree UI has not had a real browser interaction check**.
- The source-work LaunchAgent was installed on 2026-10-18 from a clean dedicated
  checkout in `~/Library/Application Support/CTP/source-worker/library`. Its
  first `RunAtLoad` invocation exited **0** with `pending: []` and
  `model_called: false`; `launchctl` reports a 1800-second interval. A first
  attempt from the Documents checkout exited 126 because macOS denied that
  process access to the protected directory; it was removed before the
  dedicated checkout was installed. An actual interval tick, sleep/restart
  recovery and headless model invocation under launchd remain unverified.
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
- `README.md`, `docs/setup.md`, `docs/maintainer-workflow.md` and the founding
  queue note have been reconciled with the admitted sources and local worker.
  Physical Safari/iPad checks and independent source-edition inspection remain.

## Next useful work

1. **Inspect both source trees:** verify the AI-assisted block placements and
   exclusions against the source packages, then test the expandable Admin trees
   in an allowed real browser. The manifest and deployment are confirmed; those
   editorial and browser interaction checks remain open.
2. **Observe scheduled source preparation:** confirm a later interval tick and
   login/sleep/restart recovery. The first installed `RunAtLoad` tick passed,
   but no scheduled model invocation has been needed yet.
3. Exercise an actual guide/translation ZIP round trip (Issue #12 is the
   first accepted Wells/Japanese guide request) and then use the results to
   develop the **shared scoped-material library and ordered two-pool UI** in
   [docs/translation-materials-design.md](docs/translation-materials-design.md).
   Keep the current Issue-based and direct browser-relay ZIP formats working
   until a tested compatible output contract replaces them. The separate
   unattended CLI translator remains optional.
4. Inspect Admin/workbench/EPUB on intended browsers. No draft should be promoted
   without explicit approval.

## Source admission — successful v2 acquisition on 2026-10-17

[PR #7](https://github.com/the-classics-translation-project/library/pull/7)
introduced conservative automatic US/Japan admission, originally holding both
queue entries because of missing original-publication metadata for Wells and the
later production-revision credit for Shelley's Gutenberg transcription.

[PR #8](https://github.com/the-classics-translation-project/library/pull/8)
added the `gutenberg-us-jp-v2` rule with narrowly scoped, version-controlled
`admission-evidence.json` per work. The Morgan Library's **1898** first-edition
record supplies Wells's missing historical publication year. The Gutenberg
**1818 photo-reprint** note and the exact Richard Tonsing production credit
are explicitly assessed as ancillary text without waiving checks for other
modern additions. Old v1 records remain re-playable by the validator. Neither
a historical publication citation nor an ancillary-credit assessment proves
the exact source edition has been independently inspected.

The [live acquisition workflow](https://github.com/the-classics-translation-project/library/actions/runs/39046838132)
successfully admitted and committed both sources to `main` in commit
`33ae1d5`. The exact packages are preserved with their Gutenberg credits and
license text, block provenance and SHA-256 evidence hashes. Both saved rights
records now have `status: acquired` and `eligible: true`. These are bounded
source-admission decisions, **not** final human rights clearance, literary
fidelity inspection, translation generation or permission to publish.

PR #8 passed **100 Python**, **9 legacy JavaScript** and **10 schema-v2
annotation** tests. The acquisition workflow's first follow-up Pages build
revealed a repository-fixture test that assumed both books would always remain
on hold. Commit `6cbc753` corrected the test to replay legacy v1 records
independently; the subsequent
[CI run](https://github.com/the-classics-translation-project/library/actions/runs/39047021644)
and [Pages deployment](https://github.com/the-classics-translation-project/library/actions/runs/39047021719)
both passed. Historical v1 decisions remain in Git history.

## Local translation runner — design only

See [docs/translation-runner.md](docs/translation-runner.md). The intended local
coordinator knows the repository and starts a separate CLI translation worker with
an explicit bounded input, so previous coordinator conversation is not sent along
implicitly. Local Work/Codex is preferred for implementing and experimentally
verifying this CLI integration; GitHub-connected ChatGPT can maintain/review the
repository and merge changes. PRs are optional for simple validated work.

**No launcher, per-translation fresh CLI session, subscription-login compatibility
test or automatic translation has been implemented or exercised yet.** The next
step is local implementation and an explicitly invoked smoke test before any
claims about model invocation, context isolation or production translation.

## Automated local source preparation — scheduled poll installed

On 2026-10-18 the owner selected a **local macOS scheduler + on-demand Codex**
approach for completing the path from a GitHub work Issue to source acquisition,
bibliographic research when a hold requires it, literary source-tree analysis,
version-controlled changes and an expandable Admin tree.

The existing GitHub Actions intake and acquisition fast path is operational.
The local worker, retry ledger, launchd installer and Admin tree renderer are
implemented in repository code. #36 was structured through the Codex executor
and trusted validation functions, then merged through PR #9. The complete
`run-once` wrapper subsequently structured and published #41445 in commit
`b787dc9`; validation and Pages deployment passed, and the next poll reconciled
its ledger without a model call. The implementation contract is in
[docs/local-source-automation.md](docs/local-source-automation.md);
the source agent prompt is
[prompts/source-preparation.md](prompts/source-preparation.md).
The owner-authorized LaunchAgent is installed from the dedicated Application
Support checkout. Its first scheduled tick found no pending work and made no
model call. A 30-minute interval is configured; subsequent timed ticks and
headless Codex execution have not yet been observed.
The public Admin page serves both trees in its embedded data, but its actual
expand/collapse interaction has not been verified in a real browser.

## ZIP-based translation requests and work guides — implementation

The repository-side workflow adds selectable templates in
`prompts/translation/`, node-level translation requests in Admin, a
strict maintainer-authorized GitHub Issue parser, an immutable
`translation-requests.json` queue, and `./ctp translation-export` /
`./ctp translation-import` commands. A whole-work preparation task uses
`./ctp guide-export` / `./ctp guide-import`; guide versions are retained
by SHA-256. The CLI builds a self-contained README/manifest/source ZIP
for the owner's existing local ChatGPT relay and imports an exact-coverage
response ZIP. A successful translation import creates a draft, captures the
actual expanded prompt and model label, preserves snapshots and tracks an
idempotent result. No model execution or automatic distribution is involved.

Admin displays current draft field coverage, allows retranslating translated
nodes and loads **only explicitly approved** historical snapshots for viewing.
Unapproved prose is retained in Git but is not automatically exposed on public
Pages. The Issue UI merely prepares a GitHub form: clicking it does not submit
an Issue. [Operating guide](docs/translation-zip-workflow.md).

This is mechanical functionality, **not evidence that an actual novel has
been translated or that the external ZIP relay has been integrated into CI**.
Existing source-work LaunchAgent behavior is unchanged.

## Whole-work glossary requests — Markdown guides with Issue handling

Admin can now prepare separate work-level glossary/translation-guide requests
for a target language, showing whether versioned guides are saved. The
authorized GitHub intake workflow records accepted requests in
`guide-requests.json` with pinned instructions from
`prompts/whole-work-guide.md`. Local `guide-pending` and
`guide-export --issue N` commands produce input ZIPs for the existing
external ChatGPT relay; `guide-import` validates responses and records
idempotent receipts under `guide-results/`. The earlier direct
`guide-export WORK TARGET` command remains valid.

The guide documents are **free-form, moderately organized Markdown**: the
model is encouraged to distinguish confirmed decisions from tentative
suggestions and document contextual alternatives, without a machine-readable
term-by-term schema. Both source-level and target-specific guides retain
content-addressed history. The Admin manifest shows their existence only;
it does not expose their text. No automatic model call, claimed human review,
or literary publication is involved.

This workflow has new automated tests for authorized intake, prompt pinning,
ZIP import, regeneration/history and Admin status. Real-browser checks and
processing a real literary guide through the external relay remain to be done.
