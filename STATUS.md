# Status — version 0.1.0

Last updated: **2026-10-18** (against the public GitHub repository and actual
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

Both Gutenberg sources were **admitted and acquired on 2026-10-17** under
`gutenberg-us-jp-v2`, using the documented per-work citation files. The original
UTF-8 packages, raw bytes, reversible blocks, evidence and hashes are retained in
`books/gutenberg-36/acquisition/` and `books/gutenberg-41445/acquisition/`.
Gutenberg #36 now has an AI-assisted, mechanically validated source tree with
31 nodes. Its 981 blocks are accounted for (920 assigned, 61 explicitly
excluded with reasons); the imported metadata does not claim human review or
exact historical print-edition verification. Gutenberg #41445 is acquired but
still needs a source tree. **Neither work has been translated.**
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
  A per-user LaunchAgent helper is available but not installed. The Admin build
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
- The source-preparation branch passed **108 Python tests**, **9 legacy JS** and
  **10 schema-v2 JS** checks, `./ctp validate` and `./ctp build --epub` locally.
  A synthetic acquired work completed the mock one-work path without network or
  model use. A real Codex CLI invocation structured #36 in an isolated worktree;
  the full wrapper's Git push/CI reconciliation path has not run live. The
  ChatGPT.app-bundled Codex CLI 0.162.0 passed a read-only login/model smoke test;
  the older global 0.46.0 CLI failed with this account's configured model.
  The built Admin manifest contains #36's 31-node tree without full literary
  prose, but **the new tree UI has not had a real browser interaction check**.
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

1. **Validate the first source-tree deployment:** merge/review the implementation,
   observe GitHub CI and Pages, and inspect #36's expandable Admin tree in an
   allowed real browser. The browser interaction check remains open.
2. **Exercise the complete local worker on #41445** from a clean current `main`
   checkout. Confirm one bounded Codex run, guarded push, CI/Pages outcomes,
   no source-byte changes and a correct tree before considering scheduling.
   Install the LaunchAgent only through the owner's explicit one-time action.
3. Implement future **node-level translation request Issues** and the separate
   fresh-context translation launcher, following
   [docs/translation-runner.md](docs/translation-runner.md).
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

## Automated local source preparation — code present, not running

On 2026-10-18 the owner selected a **local macOS scheduler + on-demand Codex**
approach for completing the path from a GitHub work Issue to source acquisition,
bibliographic research when a hold requires it, literary source-tree analysis,
version-controlled changes and an expandable Admin tree.

The existing GitHub Actions intake and acquisition fast path is operational.
The local worker, retry ledger, launchd installer and Admin tree renderer are
implemented in repository code. #36 was structured through the Codex executor
and trusted validation functions, then committed on the implementation branch;
the complete scheduled wrapper has not published a live job. The first
implementation constraints and tested command contract are in
[docs/local-source-automation.md](docs/local-source-automation.md);
the source agent prompt is
[prompts/source-preparation.md](prompts/source-preparation.md).
No LaunchAgent installation or unattended Codex job has occurred. The public
Admin page must not be reported as showing #36 until a successful Pages
deployment and browser inspection confirm it.
