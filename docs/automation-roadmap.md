# Automation roadmap and durable handoff

**Repository source of truth:** This document, [STATUS.md](../STATUS.md), [AGENTS.md](../AGENTS.md), and the implementation linked below. Update these in the **same PR as each meaningful automation change**. A chat transcript is not a progress ledger. Prefer verified observations and commit/PR links over impressions.

## Owner's intended experience

In public Admin select *The War of the Worlds* and requested target languages (currently only Japanese is actually requested; Korean is an illustrative future selection), submit an authorized GitHub Issue, and let the local computer generate **one language-independent work guide** and **one target-language terminology guide per requested language** through the existing ChatGPT ZIP relay. Later, select source nodes and an ordered, removable set of applicable reference/prompt materials, create another authorized Issue, and have the local relay process and import draft translations without manually copying ZIPs or running commands. No material is approved for reader distribution merely because its task succeeds.

## Architectural boundaries

- Project Git repository: canonical admitted sources, authorized work/language requests, three task types (`work_analysis`, `target_guide`, `translation`), immutable reference versions, task/attempt provenance and snapshots.
- Public static Admin: select works, languages, nodes and applicable **safe metadata** only; never expose private/unapproved draft text to implement prompt preview.
- GitHub Issue intake: authenticates authorized requestors and pins exact request meaning. Opening an Issue form is not submission.
- Local project coordinator (implemented, opt-in): discovers eligible jobs, prepares exact bounded ZIPs, checks dependencies, verifies relay completion, validates/imports the result, and publishes only permitted records safely.
- External `chatgpt-relay`: ZIP submission and retrieval transport, **not** the source of truth for editorial tasks.
- Source preparation worker and launchd installation: separate, already implemented; do not piggyback a model submission on its idle check.

## Milestones (ordered)

### M1. Guide task planning and independent guide operations — LOCAL PREPARATION IMPLEMENTED; SUBMISSION REMAINS EXPLICIT

**2026-10-27 change:** `relay-coordinator sync` turns proposed tasks from
accepted `queue.json` work/target requests into immutable local ZIP attempts.
Repeated syncs reuse active attempts; stopped attempts remain held for deliberate
retry. It never delivers a ZIP or authorizes model submission. The independent
Frankenstein English target-guide package was separately prepared and explicitly
delivered for one owner-authorized live trial; the relay registered it as
queued job 25, with another job ahead and no imported result. The initial preservation of the three
previously imported guides is a private hash-checked local snapshot, with no
Git distribution approval. The app result-import heartbeat still needs an
explicit configuration update to call `sync` on each run.
Implementation and tests are in [PR #19](https://github.com/the-classics-translation-project/library/pull/19).

**Done on main:** read-only deterministic planner `python3 tools/guide_task_planner.py`; legacy combined-guide Issue coverage; SHA-256 verification of existing guide pointers; unit tests. The planner returns `proposed`, `awaiting_work_analysis`, `covered_by_legacy_issue`, `completed`, and `blocked`. It currently derives requests from `queue.json` and the current guide Issue queue; it does **not** persist a new task queue, submit ZIPs, or mutate Git files. It uses the current canonical source fingerprint.

**Implemented offline in this milestone:** `./ctp guide-task-export` / `guide-task-import` provide **separate** `work_analysis` and `target_guide` ZIP contracts, saved and rendered versioned prompts, requested default model `6 Extra High`, SHA-pinned source/reference context, strict return ZIP validation, atomic immutable-guide/pointer updates, local import lock, per-job provenance and stale/duplicate rejection. The accepted legacy Issue #12 combined-guide importer remains unchanged. See [independent guide ZIP usage](independent-guide-zip.md) and `tests/test_independent_guide_jobs.py`. A real independent Frankenstein work-analysis result was imported locally on 2026-10-25. The standalone target-guide round trip remains unverified; Wells used its legacy combined contract.

**Next:** after the code reaches the canonical local checkout, update the
existing heartbeat to call `sync` before result reconciliation. Each prepared
attempt still needs separate owner submission authorization. Verify the live
standalone target-guide return and do not require a target guide for every
translation.

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

The owner then requested automatic result handling. The app heartbeat
**Import completed Classics relay results** is active every 30 minutes, running
only `reconcile --import-ready` on existing authorized attempts. It never
prepares/submits jobs, automatically resumes review holds or publishes files.
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
cannot select uncommitted private guides; using them locally requires the direct
adapter until the owner approves their Git distribution. A real translated-node
round trip and genuine deployed browser check are still pending. Offline
verification passed: 186 Python tests, 19 JavaScript core checks, Admin syntax
check, `./ctp validate`, and `./ctp build --demo --epub`. The committed-material
privacy fixture passed after the final guard change. These checks do not
establish browser behavior or literary fidelity.

Four scopes (general, target language, work, work+target), instruction/reference type, optional tags, ordered/removable Applied list, defaults that can be removed, material versions pinned at Issue acceptance. One deterministic assembler produces exact preview and ZIP contents. Full private-source preview must happen at an authorized local step, not through public Pages. Existing translation requests retain backwards compatibility.

**Acceptance:** select work/target/nodes/materials in Admin, pin exact order/versions, and import translated node-level results using their supplied guides.

### M4. Real integration and ZIP contract consolidation — GUIDE ROUND TRIPS VERIFIED LOCALLY; REMAINDER OPEN

The legacy combined Wells guide and independent Frankenstein work-analysis guide
have completed actual relay-to-local-import paths. Standalone target-guide and
translated-node round trips, restart/failure behavior of the new heartbeat and
format consolidation still require work. No output format was retired or changed.
The standalone target-guide trial is queued in the external relay, not yet completed. A short
Frankenstein chapter trial is planned only after the guide result is imported.
The direct adapter's old-edition rename gap now has an explicit guarded recovery
command and an interruption/concurrent-edit fixture. Relay heartbeat restart
behavior remains unverified in the live app.


Run actual whole-work guide, target-guide and translation round trips. Evaluate output size/context coverage, malformed ZIP handling, retries/restarts, snapshot/report preservation and Pages safety. Only after that select a unified long-prose output format (likely JSON metadata plus Markdown body files) and retain compatibility adapters for historical formats.

## Explicit current facts and risks

- `queue.json`: Wells `gutenberg-36` has **Japanese only**. Do not claim Korean is selected.
- `guide-requests.json`: accepted Issue **#12** asks for both Wells work guide and Japanese guide through the **legacy combined** output contract. A pending legacy request must suppress duplicate proposals for both of these products for the same source fingerprint.
- Both Wells and Frankenstein have canonical source trees, but neither has a recorded translated edition.
- The two existing translation ZIP protocols differ and must not be silently conflated.
- Offline tests remain distinct from real execution: the two guide relay/import paths above are observed; translation and standalone target-guide paths remain unverified.
- Reader/review publication requires separate explicit approval; public Git commits themselves distribute content.

## Maintaining a trustworthy handoff (mandatory for future work)

1. **Start:** read `AGENTS.md`, `STATUS.md`, this roadmap, the pertinent design and actual source/tests. Inspect Git state, pending Issues, current guide pointers, branch and any CI runs. Never treat prior conversation text as more authoritative.
2. **Before modifying:** identify the next bounded milestone, its invariants and compatibility constraints. Put substantial design choices here, or in a linked focused document.
3. **With every PR:** update this document's completed/remaining status and `STATUS.md`; record exact commands/tests, whether they passed, environment limits, whether a real model/relay/browser was exercised, and links to PR or commits. A failed or unexecuted test must be labeled as such.
4. **Before merge:** check documentation and code describe the same actual behavior, no unchecked submission/publishing, and tests for changed logic. Don't describe a branch-only change as released.
5. **After merge:** ensure the canonical `main` documents reflect the merged behavior and remaining tasks; record production execution/CI/Pages checks only when observed. A PR link is sufficient for provenance; do not invent a deployment.
6. **On interruption:** the latest committed roadmap, STATUS, code/tests, and GitHub requests must suffice to resume. Avoid maintaining a contradictory second checklist in chat or private notes.

A test checks the existence of this handoff and its key sections, but meaningful accuracy still requires editorial discipline; no automated test can guarantee every status claim is truthful.
