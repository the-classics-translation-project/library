# Status — version 0.1.0

Last updated: **2026-10-29** (next draft-production stage implemented offline,
submission disabled). This file describes
observed state, not a claim that the software or literary workflows are finished.

## Bounded draft-production automation — implementation in review, 2026-10-29

New Admin translation requests stay v2 even with an empty Applied list. New
acceptance pins the recipe, ordered material texts, execution variables,
source-field coverage and fixed output contract. Optional notes and guides are
no longer injected outside Applied; historical accepted requests keep their
earlier meaning. A shared version 2 translation return ZIP accepts separate
Markdown label/body files through both the Issue and opt-in direct adapters;
their earlier ZIP formats remain accepted. No version 2 return has yet been
tested with a live ChatGPT run.

`./ctp relay-dispatch` prepares accepted guide and translation Issue tasks and
can deliver bounded new jobs only under a committed owner-approved policy on a
clean, current `main`. `model-submission-policy.json` is **disabled** with zero
authorized submissions. The existing result-import heartbeat has not yet been
updated to call it. Offline checks passed: 210 Python tests, including bounded
policy and unified ZIP fixtures. A real v2 Issue pilot, timed follow-up of the
new dispatcher, sleep/restart behavior and a separately approved standing
submission scope remain open. Draft import/public Git distribution continues
under its existing policy; no reader release is implied. See the
[submission policy](docs/model-submission-policy.md),
[unified ZIP contract](docs/unified-translation-zip.md) and
[automation roadmap](docs/automation-roadmap.md).

The local demo/EPUB build, project validation and Admin JavaScript syntax check
also passed. A real Chrome interaction with the local Admin expanded the Wells
source tree, selected chapter III (`n0006`), and verified the prepared Issue URL
contains a v2 request with exactly that node and `materials: []`. No Issue or
model job was submitted by that browser check.

## Completed relay import and draft publication — 2026-10-28

[PR #27](https://github.com/the-classics-translation-project/library/pull/27)
merged the exact-result recovery and direct observer as `492a4f7`. In the
owner's Documents checkout, the already authorized relay jobs 25 and 26 were
matched to their archived request hashes and exact completed return ZIPs.
The previously held Frankenstein English target guide was imported with its
transport review history preserved; Wells Japanese chapter II was imported as
a draft. Both record the observed model as `unknown`. The returned prose was
inspected as draft data, without a human literary-quality finding.

`./ctp validate` and a local demo/EPUB build passed. The standing-policy
publisher pushed [commit `4d5dc7a`](https://github.com/the-classics-translation-project/library/commit/4d5dc7ac2ab93a860bebd4c5e7ed8319ea306ddc)
with exactly 20 imported draft/provenance/archive files and no `catalog.json`
change. [GitHub validation](https://github.com/the-classics-translation-project/library/actions/runs/40709341108)
and [Pages deployment](https://github.com/the-classics-translation-project/library/actions/runs/40709341239)
both passed. A real Chrome visit to deployed Admin showed the new Frankenstein
English guide in Available materials and Wells at 2/60 drafted fields. The
existing 30-minute app heartbeat was updated in place, confirmed
ACTIVE, and a manual repeat of its exact commands prepared/imported/pushed
nothing; project validation passed. It made no model call or relay submission.
See [the live rollout record](verification/completed-relay-rollout-2026-10-28.md).

Next: observe a timed heartbeat and sleep/restart recovery; resolve the v2
Applied-material/context inconsistencies; verify a real v2 Issue translation;
then consolidate the separate ZIP protocols and add remaining recovery tests.
The external relay source checkout remains a separate local project without a
Git remote. Reader release and `catalog.json` remain separate owner decisions.

## Completed relay returns and automatic import work — pre-rollout record, 2026-10-28

A fresh read-only inspection of the separate relay found **both** previously
missing exact return ZIPs in `output/`. Relay jobs 25 (Frankenstein English
target guide) and 26 (Wells Japanese chapter II) report `complete` with their
original request hashes and expected filenames. Both ZIPs pass archive integrity
checks. The project checkout still has not imported either result: the guide
coordinator attempt retains its earlier `needs_review` transport hold, and the
direct chapter is outside the existing coordinator heartbeat. The earlier
"missing ZIP" observations below describe their earlier inspection times.

This branch adds narrow completed-transport hold recovery and a read-only
relay-ledger observer for **already authorized** direct attempts. It never
submits or resends a job, changes the relay queue, or accepts a malformed ZIP.
An isolated rehearsal with copies of the owner's private attempts imported both
real results, recorded the automatic guide model as `unknown`, passed
`./ctp validate`, and made a 20-file local draft-publication commit with
`--no-push` and no `catalog.json` change. The temporary copy was removed.
The full offline Python suite passed (204 tests); 11 focused tests passed after
the final Chat URL guard. `./ctp validate` and `git diff --check` also passed.
A final real-ZIP rehearsal confirmed the relay database
bytes stayed unchanged. These checks did not call a model.
Live import, public Git publication and literary quality are not established by
that rehearsal. The activation sequence is to merge the implementation, update
the owner's Documents checkout and heartbeat, then run one bounded follow-up.
See [the exact rehearsal record](verification/completed-relay-import-rehearsal-2026-10-28.md).

## Automatic public-Git draft distribution — active, 2026-10-28

[PR #25](https://github.com/the-classics-translation-project/library/pull/25)
merged the standing-policy publisher as `157a648`. The owner's Documents
checkout fast-forwarded, passed `./ctp validate`, and ran `./ctp draft-publish`.
It pushed [commit `0b2e62c`](https://github.com/the-classics-translation-project/library/commit/0b2e62ca1134c3ebc631a6a4fe38f9362376a07a)
containing exactly nine guide, pointer and receipt/provenance files from the two
previously imported attempts. The commit changed no `catalog.json` entry and
made no model call. GitHub [validation for that commit](https://github.com/the-classics-translation-project/library/actions/runs/40545278652)
and its [Pages deployment](https://github.com/the-classics-translation-project/library/actions/runs/40545278692)
both passed.

The existing 30-minute **Import completed Classics relay results** app heartbeat
was updated in place and confirmed ACTIVE. Its saved prompt now runs draft
publication after guide preparation and authorized result import. A manual
no-op pass prepared zero jobs, kept the missing target-guide result at
`needs_review`, validated the project and found no files left to push. The
held direct Wells chapter result remains without an exact ZIP. A local
demo/EPUB build passed and included all three committed guide entries in Admin
metadata. In a real Chrome visit to the deployed Admin, all three guides
appeared in Available materials; the Wells work guide moved into Applied with
its matching hash prefix. No Issue was submitted. An actual timed run of the
updated heartbeat and sleep/restart behavior are still unverified. See
[rollout verification](verification/draft-distribution-rollout-2026-10-28.md).

## Implementation and pre-activation rehearsal — 2026-10-28

The owner authorized a standing policy for automatic public Git commits of
validated imported **guide and translation drafts** derived from admitted
US/Japan sources. This is separate from authorization to submit a model job and
from reader/review release. The versioned policy is `draft-distribution.json`;
`./ctp draft-publish` stages only imported, hash-verified output paths, checks
the source admission and Git baseline, validates the project, and pushes to
canonical `main` without force. The direct `relay-import` adapter now writes a
private exact-output manifest after successful installation. A held result has
no publication path. `catalog.json` remains untouched.

At the time this implementation was prepared, the Documents checkout held two
imported coordinator attempts: six Wells guide/receipt files and three
Frankenstein work-guide/provenance files. Their archived requests and results
and US/Japan source admission were rechecked read-only; neither has been pushed
by this branch yet. The missing standalone target-guide and chapter ZIPs remain
held. The existing app heartbeat still has its older no-push prompt until this
change is merged and the local checkout is updated. See
[automatic draft distribution](docs/automatic-draft-distribution.md) and the
[automation roadmap](docs/automation-roadmap.md).

Offline checks on this branch passed: the full Python suite (191 tests at that
run), seven focused draft-distribution fixtures after the final policy-state
adjustment, `./ctp validate`, `./ctp build --demo --epub`, Admin JavaScript
syntax and `git diff --check`. These do not establish a live GitHub push,
a real translated-node result or literary quality.
An isolated rehearsal copied the nine actual local guide/receipt files and
their private attempt ledgers into a temporary clone. `./ctp validate` passed;
`./ctp draft-publish --no-push` made one local commit containing exactly those
nine files from the two imported attempts and no catalogue change. The temporary
clone was removed. This still is not a live GitHub push.

## Independent code/documentation audit — historical snapshot, 2026-10-28

A review of public `main` at `3456b612` confirmed that the ordered material
selector, v2 accepted material snapshots, local exact preview, coordinator and
historical ZIP adapters match their broad documentation; latest validation and
Pages deployment passed. The audit identified **transitional differences**:
`editorial_policy` and optionally notes/guides are still injected from older
context paths even when absent from the removable Applied stack; those older
context values are not pinned at v2 Issue acceptance; and clearing Applied causes
a new Admin request to revert to v1. Private local guides intentionally remain
invisible in public Admin without explicit Git-distribution approval or a
private/metadata-only discovery alternative. The work-language target enrollment
policy is also undecided. These are static code-level observations, **not new
live-model failures or test results**. See
[dated audit and prioritized corrective tests](verification/code-documentation-audit-2026-10-28.md).

At that audit time, the two real trials were held because exact downloadable
ZIPs had not been found. Their exact returns were later recovered and imported;
see the live rollout above. The v2 prompt/context findings remain open.

## Ordered materials and guide task preparation — 2026-10-27

Implementation merged through [PR #19](https://github.com/the-classics-translation-project/library/pull/19)
as `4cc4922`. The Documents checkout was fast-forwarded to that commit without
adding its private generated guides. A live `relay-coordinator sync` reused the
already queued attempt, prepared no duplicate, and reported zero model calls or
relay submissions. `./ctp validate` passed in that checkout.

The merged implementation adds idempotent local guide task preparation
from accepted work/language requests. Submission stays per-package and requires
the owner's explicit authorization. It also adds a four-scope material library,
safe committed Admin metadata, ordered two-pool selection, v2 translation
Issue pinning and snapshotting, a local exact-input preview, and optional ordered
materials for the direct translation ZIP. Existing v1 Issue and direct return ZIP
formats remain supported. The public Admin cannot list locally imported,
uncommitted guides. No generated text has been approved for public Git
distribution or reader release.

Three previously generated local guides and their provenance/pointers were
hash-checked and copied to a private backup on 2026-10-27. A separately
authorized standalone Frankenstein English target-guide package was delivered
to the existing relay as attempt `attempt-40f5d35474a14e6b8f495a581f8ffc04`.
The relay registered it as job 25. At 2026-10-26 18:20 UTC, after the Chat
finished, the relay marked it `needs_review`: its purported result ZIP link did
not open or download, and no exact filename could be verified. A separate
browser recheck clicked the displayed link once and observed no UI change; the
rendered link had no `href`. No result was saved, imported or resent. The
existing 30-minute app heartbeat was updated in place to
run `sync` before `reconcile --import-ready`; the app confirmed it remains ACTIVE.
Its first updated timed execution reported no new preparations, imports or
failures while the Frankenstein guide remained queued; it stayed quiet as
configured. It prepares guide ZIPs
locally and imports already authorized completed results; it never submits a
new model job or publishes generated text. No generated text was committed.

For the bounded translation trial, *The War of the Worlds* Japanese chapter II
(`n0005`, 7,384 source characters) was packaged locally as direct relay attempt
`ctp-b6b987c229d8405aa6744e9fafebbb88`, with chapter I (`n0004`) as context
and exact ordered private Wells work and Japanese guide versions. The 69,026-byte
assembled-input preview matched the ZIP and manifest hash; requested fields are
only the chapter's label and body. The 47,102-byte ZIP was atomically placed in
the existing relay input with a private, hash-bound owner authorization record.
Its expected return is `ctp-b6b987c229d8405aa6744e9fafebbb88-result.zip`.
The relay registered it as job 26 and submitted it at 2026-10-26 18:21 UTC.
At 2026-10-26 19:23 UTC, its Chat finished but the purported translation ZIP
link did not open or download; the relay marked the job `needs_review`. A
separate browser click likewise caused no UI change and the rendered link had
no `href`. The exact result file was never saved or imported. No resend was
attempted, and no chapter prose was publicly committed.

The separate 30-minute app heartbeat **Finish Classics translation pilot**
was deleted after both bounded trials reached `needs_review`; neither can
progress through unattended import without an exact downloaded ZIP. Its final
configured instructions remain in `prompts/translation-pilot-follow-up.md`
for audit. The existing general guide-preparation/import heartbeat remains
ACTIVE but does not resume review holds or submit model jobs. Neither heartbeat
authorizes public Git distribution, a catalogue change or literary release.

Offline verification: 186 Python tests passed, including committed-material
privacy, exact-input and interrupted-import recovery checks. Nineteen JavaScript
core checks and `node --check site/translation-admin.js` passed. `./ctp validate`
and `./ctp build --demo --epub` passed locally. The Pages build and deployment
for merged PR #19 completed successfully in [run 40358969727](https://github.com/the-classics-translation-project/library/actions/runs/40358969727).
A real browser check of that deployed Admin selected Wells chapter II, added,
reordered and removed public materials, and confirmed that the prepared v2
Issue URL pinned the selected order and hashes. Private uncommitted guides were
absent from the public list; no Issue was submitted. A reload cleared the local
selection. See [browser verification](verification/materials-browser-2026-10-27.md).
No real translated-node result has been verified. Both exact result ZIPs must
be recovered, or fresh attempts separately authorized, before their respective
live protocols can be verified. Unified ZIP formats and remaining recovery
tests follow a real translated-node import. See
[automation roadmap](docs/automation-roadmap.md).

The direct ZIP importer also has a guarded `relay-recover ATTEMPT` command and
fixture for a crash between its directory renames. It restores only a byte-matched
prior edition when the target path is absent; an intervening edit remains intact.

## Automatic relay result import — 2026-10-25

Both real guide jobs have now been imported **locally** using the coordinator:
Wells Issue #12 supplied a work reference and Japanese terminology guide; the
independent Frankenstein job supplied a work-analysis guide. Source/job identities,
strict return ZIP contracts and project validation passed. Wells was explicitly
resumed after the previously unavailable download became available; that earlier
browser failure remains recorded below. Both private attempt records now say
`imported`. This verifies real guide relay/import paths, not translation fidelity,
human review or the standalone target-guide protocol.

At the owner's request, the app heartbeat **Import completed Classics relay
results** is ACTIVE at a 30-minute interval for this local chat/workspace. It runs
`./ctp relay-coordinator reconcile --import-ready` for existing, explicitly
submission-authorized attempts only. It does not submit new jobs, automatically
resume review holds, change the external relay, commit/push generated material or
approve publication. It stays quiet on unchanged state and reports new imports
or actionable problems. The app confirmed registration; the first timed heartbeat
and sleep/restart behavior have not yet been observed. The local Mac/app must be
available. The source-worker LaunchAgent was not changed.

A repeat local import poll changed neither editorial files nor attempt records,
made no relay database writes or new submissions, and `./ctp validate` passed.
All 174 Python tests passed, including a regression for the first translation
after importing a guide-only target directory. The sample HTML/EPUB build also
passed. The translation packager now distinguishes an existing `edition.json`
from a directory that only contains imported reference material.
The generated Markdown, content-addressed pointers and provenance are currently
uncommitted local draft references, not included in this documentation change or
reader distribution. The catalogue remains empty. See
[coordinator usage](docs/local-relay-coordinator.md) and
[automation roadmap](docs/automation-roadmap.md).

Post-merge validation and Pages deployment for `b2c5b8a` both succeeded:
[validation](https://github.com/the-classics-translation-project/library/actions/runs/40154561062),
[deployment](https://github.com/the-classics-translation-project/library/actions/runs/40154560930).

## Initial local relay integration observations — 2026-10-25 (historical)

The Documents checkout was fast-forwarded to `5b64630`. The owner authorized the
local assessment's execution sequence. Legacy guide/translation ZIP exports now
include an explicit requested model (default `6 Extra High`) and exact return
filename while preserving accepted job hashes. Issue #12's package was copied
into the relay input directory for pickup; no completed live result is claimed.
A separate independent Frankenstein work-analysis job was delivered second.
The opt-in project coordinator now supports explicit authorization, deduplication,
transport reconciliation, staged import/recovery and separately approved exact-file
Git publication; no new scheduler is installed. Local verification passed: 173 Python tests (19 coordinator tests), 19 JavaScript
checks, `./ctp validate` and the sample EPUB build. Wells Issue #12 was submitted as relay job 21. Its Chat completed after 13m43s,
but Chrome showed a response-loading error and no downloadable result after
reload; the response Copy control returned empty text. The project attempt is
stopped as `needs_review`, with the original input retained and no automatic
resubmission. The relay database was not edited by the requester. Frankenstein
remains delivered for pickup. No live result has been imported, approved or
published; real round-trip completion remains unverified. See [coordinator usage](docs/local-relay-coordinator.md) and
[automation roadmap](docs/automation-roadmap.md) for the durable handoff.

Actual Chrome checks passed for deployed Admin tree/selection/request controls
and local synthetic-workbench persistence across reload and section navigation.
The existing source worker reports 317 runs and latest exit code 0, with repeated
idle no-model logs; sleep/restart and headless model execution remain unverified.
See [browser/runtime verification](verification/relay-browser-2026-10-25.md).

## Independent guide ZIP export/import — initial offline milestone (historical)

At this milestone, new `./ctp guide-task-export` and `./ctp guide-task-import` commands independently packaged/imported `work_analysis` and `target_guide` tasks, using versioned Markdown prompts and **requested model default `6 Extra High`**. One guide is returned as `result.json` plus `guide.md`. Packaging pins exact source, work-reference version, prompt, notes, target and previous-guide pointer. Import enforces strict ZIP/job/field identities, source and guide-baseline staleness, immutable SHA-named guide text, serializes local imports, records requested vs observed model and full rendered editorial instructions, and preserves old guide versions. See [independent guide ZIP usage](docs/independent-guide-zip.md). No live model/relay run was performed during that initial implementation. Later real guide imports and the current coordinator/Admin state are recorded above.

## Automation roadmap and bounded guide planner — initial read-only milestone (historical)

The owner-facing end-to-end goal, milestones, compatibility constraints, and mandatory cross-session handoff are tracked in [docs/automation-roadmap.md](docs/automation-roadmap.md). The repository includes a read-only `tools/guide_task_planner.py` and offline tests. It proposes missing work/target guides from `queue.json`, existing content-hashed guide pointers and compatible outstanding legacy Issue requests. It makes **no relay, network, model or file-write actions**. Independent guide ZIP exporters/importers are now available manually, but no new independent guide Issue queue or ordered-material UI is implemented. The coordinator and live guide imports are recorded above.

## Three ChatGPT task types — initial ZIP milestone (historical)

The proposed project-owned task types are `work_analysis`, `target_guide` and `translation`; `chatgpt-relay` remains a ZIP submission/download transport. See [task model](docs/relay-task-model.md) and separate versioned `prompts/work-analysis.md` / `prompts/target-language-guide.md`. The existing combined guide ZIP operation, accepted Issue #12, and both current translation adapters remain unchanged. Read-only task discovery and independent local guide ZIP handlers now exist; there is no automatic enqueue/submission scheduler or registered new independent guide Issue intake. Real relay round-trip verification remains necessary.

## Ordered translation materials — initial design before PR #19 (historical)

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
