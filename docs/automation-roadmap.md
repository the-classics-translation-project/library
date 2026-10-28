# Automation roadmap and durable handoff

**Repository source of truth:** This document, [STATUS.md](../STATUS.md), [AGENTS.md](../AGENTS.md), and the implementation linked below. Update these in the **same PR as each meaningful automation change**. A chat transcript is not a progress ledger. Prefer verified observations and commit/PR links over impressions.

## Conditional standing submission — proposed, 2026-10-29

The next bounded stage prepares a still-disabled policy for accepted Wells
Japanese translation Issues using `6 Extra High`, with three submissions total,
one per run and one in flight. The separately authorized Issue #30 pilot is
outside that cap. The dispatcher must verify the pilot's exact authorized
attempt, imported receipt, archived request and response hashes, and unified
version 2 ZIP before any policy-authorized delivery. Missing, held, altered or
legacy-format results block without a resend. A policy-authorized attempt that
later needs review blocks subsequent delivery. The clean/current `main` and
committed-policy checks still apply. Accepted tasks can still be prepared while
this condition is unmet.

At this inspection Issue #30 remains `delivered` with no verified result. The
policy stays disabled and has no owner authorization record. The next steps are
to observe/import the real pilot, review its draft and provenance, then obtain
the owner's approval of the **specific enabled policy revision** before any
automatic delivery. After activation, observe one real scheduled dispatch and
its import, stopping or lowering the cap if the relay has a new failure. A
manual exact-package route remains available. The focused gate/dispatcher
test, 211 Python tests, `./ctp validate` and `git diff --check` passed locally;
the later policy-hold assertion was rechecked in the focused test. No new model job or
reader release occurred in this proposal.

## Authorization wording — merged, 2026-10-29

The owner's informal, interactive workflow and its bounded automation can use
either exact-package authorization or one explicit standing authorization for
a narrow policy revision. Merged [PR #33](https://github.com/the-classics-translation-project/library/pull/33)
clarifies that an active,
owner-approved policy authorizes in-scope submissions up to its limits without
asking again for each job. Task intake remains distinct from model submission;
stopped attempts are not resent automatically. This was a rule clarification,
not activation: `model-submission-policy.json` remains disabled. The bounded
Wells/Japanese scope above is prepared for later owner review. Maintainers may
continue using individual package approvals.
That wording change touched no dispatcher code or policy JSON; `./ctp validate`, the
focused bounded-dispatcher test and `git diff --check` passed locally. The
pilot result and a separately scoped activation decision remain. No additional
model job was submitted by that wording change.

## Next draft-production stage — merged; preparation active, 2026-10-29

[PR #29](https://github.com/the-classics-translation-project/library/pull/29)
merged as `ac5d9a5`. Its main-branch validation and Pages deployment passed.

New Admin requests always use v2, including an empty Applied stack. Their
accepted queue pins all optional materials, template variables, source-field
coverage and output contract; no unselected notes or guides enter the new
assembled input. Old accepted v1/v2 requests replay under their prior rules.
The compatible [unified translation return ZIP](unified-translation-zip.md)
works with both new Issue requests and opt-in direct packages in offline tests;
the historical protocols stay readable. A real version 2 return is still needed.

The new [bounded dispatcher](model-submission-policy.md) prepares accepted
guide and translation tasks and can deliver to the existing relay only from a
clean, current, committed `main` under a versioned owner policy. The checked-in
policy is disabled and authorizes zero jobs. Offline verification passed 210
Python tests, project validation, the demo/EPUB build and Admin syntax check.
A real local Chrome interaction selected Wells chapter III (`n0006`) and showed
a v2 Issue URL with `materials: []`. The existing 30-minute heartbeat is now
ACTIVE with the dispatcher, and a manual run prepared/submitted/imported/pushed
nothing. Its first timed run on this prompt remains unverified.
The owner-account [Issue #30](https://github.com/the-classics-translation-project/library/issues/30)
then requested that chapter with three ordered materials. GitHub intake
accepted it in `1515581`; the dispatcher prepared exact private attempt
`attempt-7195ba9ade6345339ac6dc167b4b44a8`. The
Issue intake's site job failed because a fixture assumed no real translation
requests existed. [PR #31](https://github.com/the-classics-translation-project/library/pull/31)
isolated that fixture and merged as `572c36e`; main validation and Pages
deployment passed. The owner explicitly authorized one submission of the
exact Issue #30 package, whose archived and relay-input SHA-256 both equal
`6950b9894337441ad9f2c3dca60380f0929ddb818fed9a2cddc46ecd418cb696`.
The coordinator says `delivered`; relay registration and model execution are
not yet verified. The standing submission policy remains disabled. After its real return and
recovery checks, review a bounded standing authorization for automatic model
submission. Reader release remains a separate decision.

## Live completed-result rollout — 2026-10-28

[PR #27](https://github.com/the-classics-translation-project/library/pull/27)
merged as `492a4f7`. The owner's Documents checkout then imported both exact
returns from already authorized relay jobs: the independent Frankenstein
English target guide (job 25) and Wells Japanese chapter II (job 26). The
first import retained the earlier transport-review reason; both recorded
observed model `unknown`. The direct chapter is still a draft, with the
remaining work untranslated. The real result confirms the two existing ZIP
contracts remain different; unified ZIP handling and related recovery tests
are still open.

Project validation and a local demo/EPUB build passed. `./ctp draft-publish`
pushed the exact 20-file [draft commit `4d5dc7a`](https://github.com/the-classics-translation-project/library/commit/4d5dc7ac2ab93a860bebd4c5e7ed8319ea306ddc)
without a reader-catalogue change or model call. [GitHub validation](https://github.com/the-classics-translation-project/library/actions/runs/40709341108)
and [Pages deployment](https://github.com/the-classics-translation-project/library/actions/runs/40709341239)
both passed. A real Chrome visit to deployed Admin showed the newly committed
Frankenstein English guide in Available materials and Wells at 2/60 drafted
fields. The existing 30-minute app heartbeat is ACTIVE with the updated saved
prompt: prepare eligible guide attempts, import only exact authorized completed
results, validate, then publish policy-approved drafts. A manual no-op pass
repeated these commands with zero new preparation, import or publication.
See [the live rollout record](../verification/completed-relay-rollout-2026-10-28.md).

**Next:** observe a timed heartbeat and sleep/restart recovery; correct v2
Applied-material/context semantics; verify a v2 Issue translation; consolidate
the separate guide/translation return ZIP contracts and their recovery tests.
The relay tool source checkout is a separate local project without a Git remote.
Per-package model submission authorization and reader release remain separate.

## Completed-result recovery and direct import — pre-rollout record, 2026-10-28

The relay's exact return files for job 25 (Frankenstein English target guide)
and job 26 (Wells Japanese chapter II) now exist. Its read-only ledger says
`complete` for both with the original request SHA-256 values and expected
filenames; both ZIPs passed archive integrity checks. The project has not yet
imported them. The target-guide coordinator row is held because its earlier
transport status was `needs_review`; the direct package is not scanned by the
existing 30-minute heartbeat.

This implementation adds `relay-coordinator reconcile --import-ready
--recover-completed`, which reopens only an authorized prior **transport** hold
when its exact completed relay result appears, and `relay-direct-reconcile`,
which imports only direct jobs with a matching private submission-authorization
record, exact relay request identity and completed output. Both use the existing
strict ZIP importers and leave other holds untouched. No relay queue transition,
model submission, `catalog.json` change or reader approval is added. The saved
heartbeat prompt in this PR includes both steps before validation and the
standing-policy publisher. An isolated rehearsal imported the two real ZIPs,
validated the project and produced a 20-file local no-push draft commit; this
does not prove live activation or literary fidelity. See the
[exact rehearsal record](../verification/completed-relay-import-rehearsal-2026-10-28.md).
The full offline Python suite passed (204 tests), 11 focused tests passed after
the final Chat URL guard, project validation passed,
and the final real-ZIP rehearsal left the relay database byte-for-byte unchanged.

**Next after merge:** fast-forward the owner's Documents checkout, update the
existing heartbeat in place, run a bounded real follow-up, inspect provenance
and draft prose, then record exact imported/pushed files and CI/Pages outcomes.
Keep the original ZIPs and attempts for recovery. The relay tool's own source
checkout remains a separate local project with no Git remote; this change does
not publish that tool.

## Draft-distribution rollout observed — 2026-10-28

[PR #25](https://github.com/the-classics-translation-project/library/pull/25)
merged as `157a648`. In the owner's Documents checkout, `./ctp draft-publish`
verified the two previously imported guide attempts and pushed the exact
nine-file [draft commit `0b2e62c`](https://github.com/the-classics-translation-project/library/commit/0b2e62ca1134c3ebc631a6a4fe38f9362376a07a).
No held ZIP, unrelated file, catalogue change or model call entered that step.
[GitHub validation](https://github.com/the-classics-translation-project/library/actions/runs/40545278652)
and [Pages deployment](https://github.com/the-classics-translation-project/library/actions/runs/40545278692)
both passed. A local build lists all three guides as public Admin material
metadata. A real Chrome visit to the deployed Admin showed the three guides
in Available materials and moved the Wells work guide into Applied with the
recorded hash prefix. No Issue was submitted. See the
[rollout verification](../verification/draft-distribution-rollout-2026-10-28.md).

The existing 30-minute app heartbeat was updated in place and confirmed
ACTIVE with the saved `prompts/relay-result-import.md` instructions. A manual
pass of its exact commands produced no new preparation or import, kept the
Frankenstein target-guide attempt held, passed validation and made no new
publication commit. The direct Wells chapter trial also remains held without
its exact return ZIP. Next: observe a real timed heartbeat and sleep/restart
behavior, recover/diagnose the two missing ZIPs without resubmitting,
then fix v2 material semantics and complete a real translated-node import.
Reader release and `catalog.json` remain separate editorial decisions.

## Standing draft-distribution implementation and rehearsal — 2026-10-28

The owner authorized automatic public Git distribution of validated imported
guide and translation **drafts** whose admitted source has passed the saved
US/Japan policy. `draft-distribution.json` records the standing scope; the
[publisher](automatic-draft-distribution.md) validates exact import archives,
output hashes, source admission, path scope, Git baseline and project state
before committing only those outputs. It does not submit model jobs, resume held
relay attempts, change `catalog.json` or approve a literary release. A direct
`relay-import` result gets a private publication manifest only after successful
installation. Existing coordinator imports already have exact output ledgers.
Offline verification passed on the branch: 191 Python tests in the full suite,
seven focused draft-distribution fixtures after the final policy-state adjustment,
project validation, demo/EPUB build, Admin JavaScript syntax and diff check.
The push retry fixture uses a local bare Git remote; no live GitHub push or
new model job occurred during these tests.
An isolated rehearsal with copies of the owner's two real imported attempt
records and nine local output files passed validation and made an exact nine-file
local commit with `--no-push`; no held result or catalogue file was included.
The temporary clone was removed. Live GitHub publication remains to be observed.

**Historical activation plan (completed as recorded above):** merge this
implementation, fast-forward the owner's Documents checkout, publish the two
verified imported guide attempts, and update the existing app heartbeat.
The two attempts without downloadable return ZIPs remain held. The next
technical work remains ZIP recovery, v2
material semantics and a real translated-node import; reader catalogue release
still needs its own editorial decision.

## Owner's intended experience

In public Admin select *The War of the Worlds* and requested target languages (currently only Japanese is actually requested; Korean is an illustrative future selection), submit an authorized GitHub Issue, and let the local computer generate **one language-independent work guide** and **one target-language terminology guide per requested language** through the existing ChatGPT ZIP relay. Later, select source nodes and an ordered, removable set of applicable reference/prompt materials, create another authorized Issue, and have the local relay process and import draft translations without manually copying ZIPs or running commands. No material is approved for reader distribution merely because its task succeeds.

## Architectural boundaries

- Project Git repository: canonical admitted sources, authorized work/language requests, three task types (`work_analysis`, `target_guide`, `translation`), immutable reference versions, task/attempt provenance and snapshots.
- Public static Admin: select works, languages, nodes and applicable **safe metadata** only; never expose private/unapproved draft text to implement prompt preview.
- GitHub Issue intake: authenticates authorized requestors and pins exact request meaning. Opening an Issue form is not submission.
- Local project coordinator (implemented, opt-in): discovers eligible jobs, prepares exact bounded ZIPs, checks dependencies, verifies relay completion, validates/imports the result, and publishes only permitted records safely.
- External `chatgpt-relay`: ZIP submission and retrieval transport, **not** the source of truth for editorial tasks.
- Source preparation worker and launchd installation: separate, already implemented; do not piggyback a model submission on its idle check.

## Historical audit priorities — code audit 2026-10-28

The [independent code/documentation audit](../verification/code-documentation-audit-2026-10-28.md)
was performed against public `main` at `3456b612`, not uncommitted Mac files.
**First**, diagnose the two held real relay return-ZIP links and recover exact
archives where possible, with **no automatic resend**; a separate minimal
attachment test needs its own authorization. **Second**, reconcile the v2
Applied-material semantics with older implicitly included editorial references:
make optional documents truly removable, pin all execution context, and preserve
an explicitly empty v2 Applied stack while retaining historical v1 behavior.
**Third**, select a privacy-safe way for locally generated, uncommitted guides to
be discoverable in the translation UI; decide whether work-target enrollment is
mandatory or can be expanded by a translation Issue. **Fourth**, complete one
real v2 Issue-based translation import and standalone target-guide import.
The two exact ZIPs and standalone target-guide/direct-node round trips were
subsequently recovered and verified as recorded in the live rollout above.
The v2 material semantics, v2 Issue translation and ZIP consolidation remain
open. Any automatic submission extension still requires separate authorization.

## Milestones (ordered)

### M1. Guide task planning and independent guide operations — LOCAL PREPARATION IMPLEMENTED; SUBMISSION REMAINS EXPLICIT

**2026-10-27 change:** `relay-coordinator sync` turns proposed tasks from
accepted `queue.json` work/target requests into immutable local ZIP attempts.
Repeated syncs reuse active attempts; stopped attempts remain held for deliberate
retry. It never delivers a ZIP or authorizes model submission. The independent
Frankenstein English target-guide package was separately prepared and explicitly
delivered for one owner-authorized live trial; the relay registered it as
job 25. At 2026-10-26 18:20 UTC its Chat had finished, but the displayed
result ZIP link did not open or download. The relay and coordinator marked the
attempt `needs_review`; a separate browser click also left the page unchanged,
with no verified result file. No resend or queue mutation was attempted. The three
previously imported guides have a private hash-checked local snapshot, with no
Git distribution approval. The existing 30-minute heartbeat now runs `sync`
before reconciled import; the app confirmed ACTIVE status. Its first updated
timed run found no new preparation/import/failure and stayed quiet. Implementation and tests merged in
[PR #19](https://github.com/the-classics-translation-project/library/pull/19)
as `4cc4922`. A live no-op sync on the updated Documents checkout reused job 25
and reported zero model calls/submissions; project validation passed.

**Done on main:** read-only deterministic planner `python3 tools/guide_task_planner.py`; legacy combined-guide Issue coverage; SHA-256 verification of existing guide pointers; unit tests. The planner returns `proposed`, `awaiting_work_analysis`, `covered_by_legacy_issue`, `completed`, and `blocked`. It currently derives requests from `queue.json` and the current guide Issue queue; it does **not** persist a new task queue, submit ZIPs, or mutate Git files. It uses the current canonical source fingerprint.

**Implemented offline in this milestone:** `./ctp guide-task-export` / `guide-task-import` provide **separate** `work_analysis` and `target_guide` ZIP contracts, saved and rendered versioned prompts, requested default model `6 Extra High`, SHA-pinned source/reference context, strict return ZIP validation, atomic immutable-guide/pointer updates, local import lock, per-job provenance and stale/duplicate rejection. The accepted legacy Issue #12 combined-guide importer remains unchanged. See [independent guide ZIP usage](independent-guide-zip.md) and `tests/test_independent_guide_jobs.py`. A real independent Frankenstein work-analysis result was imported locally on 2026-10-25. The standalone target-guide round trip remains unverified; Wells used its legacy combined contract.

**Next:** recover and verify the exact standalone target-guide ZIP, if the saved
Chat makes it available. A fresh attempt would need separate owner submission
authorization; the held trial does not authorize a resend. Do not require a
target guide for every translation.

**Acceptance:** one work with two target languages yields one work reference and two target guides; repeat checks submit nothing; existing references are never overwritten without a versioned regeneration; old requests keep working.

### M2. Local authorized relay coordinator — IMPLEMENTED; LIVE GUIDE IMPORT VERIFIED LOCALLY

**Latest observation, 2026-10-25:** Wells Issue #12 and the independent Frankenstein
work-analysis request both completed in the external relay, and both were imported
locally through the coordinator with retained exact ZIPs/provenance. Wells was
explicitly resumed after its download was recovered. `./ctp validate` passed; a
second import poll left editorial files, attempt records and relay state unchanged.
No generated guide has been committed, pushed or approved for distribution.
The live guide import exposed a guide-only target directory before an edition
exists: the direct translator now checks for `edition.json` rather than treating
any directory as an existing edition, preserving previously imported guides.
A regression fixture covers the first translation after a guide-only import;
source-based tests isolate their temporary fixtures from real local results.
All 174 Python tests, project validation and the sample HTML/EPUB build passed.
The public-Git leg of the acceptance criterion remains a separate owner decision.

The owner then requested automatic result handling. At its initial installation,
the app heartbeat **Import completed Classics relay results** ran only
`reconcile --import-ready` every 30 minutes on existing authorized attempts.
It never submitted jobs, automatically resumed review holds or published files.
The first timed heartbeat and Mac sleep/restart behavior are unverified; creation
was confirmed by the app. This is separate from both the external relay's existing
hourly schedule and the source-worker LaunchAgent. Exact configured instructions
are recorded in `prompts/relay-result-import.md`.

**Initial implementation and trial history (superseded by the observations above):**

2026-10-25 local work: updated the Documents checkout to `5b64630`. Legacy ZIP
export README transport metadata now supplies an explicit model and exact output
name without changing accepted job identities. Offline guide/translation fixture
checks passed. The owner explicitly requested the assessed local sequence;
Issue #12 was packaged and placed in the relay input directory for pickup. This
is submission authorization, not evidence that ChatGPT has received or completed
it. The independent Frankenstein work-analysis package was prepared and delivered
second, using the new coordinator's explicit authorization boundary. Both attempts
are tracked under private local state; imported results must be verified separately.

The opt-in [local coordinator](local-relay-coordinator.md) is now implemented. It
supports explicit prepare/adopt/submit, read-only relay reconciliation, staged
imports with journal/rollback, deliberate retries and separately approved exact-file
Git publication. It installs no scheduler, makes no direct model/browser calls,
and does not authorize proposals automatically. Offline tests cover all three
supported adapter paths. Local validation passed: 173 Python tests (19 coordinator tests), 19 JavaScript
checks, `./ctp validate` and `./ctp build --demo --epub`. The final Git-publication
helper was additionally rechecked with its exact-file fixture after improving
error reporting. No live guide result has been imported yet.

Live state: Wells Issue #12 was submitted as relay job 21, with saved Chat URL
in the private attempt receipt. Its Chat completed after 13m43s, but Chrome
reported a response-loading error; reloading and the response Copy control did
not reveal a downloadable result. The project attempt is `needs_review` and
preserves the original ZIP; the requester has neither changed the transport
queue nor resent it. Frankenstein is delivered to watched input, awaiting pickup.
No actual guide output has been imported. This is a failed live result-retrieval
check, not a completed round trip or proof of an importer failure. Exact attempt
IDs and archived ZIPs are under `private/relay-coordinator/attempts/`.
The external relay remains on its existing hourly schedule; no requester queue
state transition or new LaunchAgent has been used. Live outcome verification is
still in progress.

Actual Chrome checks passed for deployed Admin expansion/selection/request payloads
and local synthetic-workbench note persistence across reload/navigation. See
[verification](../verification/relay-browser-2026-10-25.md).


Discover accepted project tasks; reconcile project task state with the external relay's transport ledger; package into immutable attempt ZIPs, copy atomically into watched input only when the owner has authorized this submission class, import valid downloaded responses, and commit/push safe approved changes. Locks, crash recovery, retries, no-op zero-model polling, stale inputs, duplicated completed results and Git conflicts all require tests. Separately verify the actual relay is operational on the Mac. Do not install/enable any new LaunchAgent without explicit owner action.

**Acceptance:** one authorized guide request travels Issue → local packaging → actual ChatGPT relay → validated guide files → Git commit, with a safe retry after simulated interruption.

### M3. Shared material library and two-pool Admin UI — INITIAL IMPLEMENTATION

`tools/materials.py` discovers four scopes and instruction/reference type from
files and local guide pointers. Public Admin lists only committed
safe metadata. A removable, reorderable Available/Applied selector pins ordered
IDs and hashes in a v2 Issue request. Acceptance snapshots full material text;
the local `translation-preview` and exporter use one assembled input. The direct
relay adapter can also include ordered pinned materials and a private exact
preview. Legacy request/response contracts remain available. The public Admin
cannot select uncommitted private guides. The owner later approved draft Git
distribution, and all four imported guides are now committed; the real direct
translated-node round trip also completed. A v2 Issue-based round trip remains
pending. The PR #19 Pages build/deployment succeeded; a real
browser check selected Wells chapter II, added/reordered/removed two public
materials and inspected the v2 Issue URL with exact ordered hashes. Private
uncommitted guides were absent from the public list. The selection reset on
reload; no Issue was submitted. See
[browser verification](../verification/materials-browser-2026-10-27.md). Offline
verification passed: 186 Python tests, 19 JavaScript core checks, Admin syntax
check, `./ctp validate`, and `./ctp build --demo --epub`. The committed-material
privacy fixture passed after the final guard change. These checks do not
establish literary fidelity.

Four scopes (general, target language, work, work+target), instruction/reference type, optional tags, ordered/removable Applied list, defaults that can be removed, material versions pinned at Issue acceptance. One deterministic assembler produces exact preview and ZIP contents. Full private-source preview must happen at an authorized local step, not through public Pages. Existing translation requests retain backwards compatibility.

**Acceptance:** select work/target/nodes/materials in Admin, pin exact order/versions, and import translated node-level results using their supplied guides.

### M4. Real integration and ZIP contract consolidation — DIRECT NODE AND GUIDE ROUND TRIPS VERIFIED; FORMAT WORK OPEN

The legacy combined Wells guide, independent Frankenstein work-analysis guide,
standalone Frankenstein English target guide and direct Wells Japanese chapter
II (`n0005`) translation have completed exact relay-to-local-import paths. The
last two were initially held after Chat links failed to download, then
recovered from the relay's completed exact ZIPs without resubmission. Their
drafts were pushed under the owner's later standing Git-distribution policy.
No output format was retired or changed. The separate 30-minute **Finish
Classics translation pilot** heartbeat was deleted while both trials were held;
its historical prompt remains at `prompts/translation-pilot-follow-up.md`.
The general import/publish heartbeat is ACTIVE. Timed execution of its latest
prompt and sleep/restart behavior remain unverified. A real v2 Issue-based
translation, unified ZIP contract and related recovery tests remain open.
The direct adapter's old-edition rename gap now has an explicit guarded recovery
command and an interruption/concurrent-edit fixture. Relay heartbeat restart
behavior remains unverified in the live app.


Run actual whole-work guide, target-guide and translation round trips. Evaluate output size/context coverage, malformed ZIP handling, retries/restarts, snapshot/report preservation and Pages safety. Only after that select a unified long-prose output format (likely JSON metadata plus Markdown body files) and retain compatibility adapters for historical formats.

## Explicit current facts and risks

- `queue.json`: Wells `gutenberg-36` has **Japanese only**. Do not claim Korean is selected.
- `guide-requests.json`: accepted Issue **#12** asks for both Wells work guide and Japanese guide through the **legacy combined** output contract. A pending legacy request must suppress duplicate proposals for both of these products for the same source fingerprint.
- Both Wells and Frankenstein have canonical source trees. Wells Japanese now has a chapter II draft; the remaining source fields are largely untranslated.
- The two existing translation ZIP protocols differ and must not be silently conflated.
- Offline tests remain distinct from real execution: the historical direct translation and standalone target-guide paths have real imported returns; a v2 Issue translation and unified return ZIP have not yet had a live model round trip.
- Reader/review publication requires separate explicit approval; public Git commits themselves distribute content.

## Maintaining a trustworthy handoff (mandatory for future work)

1. **Start:** read `AGENTS.md`, `STATUS.md`, this roadmap, the pertinent design and actual source/tests. Inspect Git state, pending Issues, current guide pointers, branch and any CI runs. Never treat prior conversation text as more authoritative.
2. **Before modifying:** identify the next bounded milestone, its invariants and compatibility constraints. Put substantial design choices here, or in a linked focused document.
3. **With every PR:** update this document's completed/remaining status and `STATUS.md`; record exact commands/tests, whether they passed, environment limits, whether a real model/relay/browser was exercised, and links to PR or commits. A failed or unexecuted test must be labeled as such.
4. **Before merge:** check documentation and code describe the same actual behavior, no unchecked submission/publishing, and tests for changed logic. Don't describe a branch-only change as released.
5. **After merge:** ensure the canonical `main` documents reflect the merged behavior and remaining tasks; record production execution/CI/Pages checks only when observed. A PR link is sufficient for provenance; do not invent a deployment.
6. **On interruption:** the latest committed roadmap, STATUS, code/tests, and GitHub requests must suffice to resume. Avoid maintaining a contradictory second checklist in chat or private notes.

A test checks the existence of this handoff and its key sections, but meaningful accuracy still requires editorial discipline; no automated test can guarantee every status claim is truthful.
