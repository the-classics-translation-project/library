# Automation roadmap and durable handoff

**Repository source of truth:** This document, [STATUS.md](../STATUS.md), [AGENTS.md](../AGENTS.md), and the implementation linked below. Update these in the **same PR as each meaningful automation change**. A chat transcript is not a progress ledger. Prefer verified observations and commit/PR links over impressions.

## Owner's intended experience

In public Admin select *The War of the Worlds* and requested target languages (currently only Japanese is actually requested; Korean is an illustrative future selection), submit an authorized GitHub Issue, and let the local computer generate **one language-independent work guide** and **one target-language terminology guide per requested language** through the existing ChatGPT ZIP relay. Later, select source nodes and an ordered, removable set of applicable reference/prompt materials, create another authorized Issue, and have the local relay process and import draft translations without manually copying ZIPs or running commands. No material is approved for reader distribution merely because its task succeeds.

## Architectural boundaries

- Project Git repository: canonical admitted sources, authorized work/language requests, three task types (`work_analysis`, `target_guide`, `translation`), immutable reference versions, task/attempt provenance and snapshots.
- Public static Admin: select works, languages, nodes and applicable **safe metadata** only; never expose private/unapproved draft text to implement prompt preview.
- GitHub Issue intake: authenticates authorized requestors and pins exact request meaning. Opening an Issue form is not submission.
- Local project coordinator (not yet built): discovers eligible jobs, prepares exact bounded ZIPs, checks dependencies, verifies relay completion, validates/imports the result, and publishes only permitted records safely.
- External `chatgpt-relay`: ZIP submission and retrieval transport, **not** the source of truth for editorial tasks.
- Source preparation worker and launchd installation: separate, already implemented; do not piggyback a model submission on its idle check.

## Milestones (ordered)

### M1. Guide task planning and independent guide operations — OFFLINE IMPLEMENTED; ISSUE AUTOMATION PENDING

**Done on main:** read-only deterministic planner `python3 tools/guide_task_planner.py`; legacy combined-guide Issue coverage; SHA-256 verification of existing guide pointers; unit tests. The planner returns `proposed`, `awaiting_work_analysis`, `covered_by_legacy_issue`, `completed`, and `blocked`. It currently derives requests from `queue.json` and the current guide Issue queue; it does **not** persist a new task queue, submit ZIPs, or mutate Git files. It uses the current canonical source fingerprint.

**Implemented offline in this milestone:** `./ctp guide-task-export` / `guide-task-import` provide **separate** `work_analysis` and `target_guide` ZIP contracts, saved and rendered versioned prompts, requested default model `6 Extra High`, SHA-pinned source/reference context, strict return ZIP validation, atomic immutable-guide/pointer updates, local import lock, per-job provenance and stale/duplicate rejection. The accepted legacy Issue #12 combined-guide importer remains unchanged. See [independent guide ZIP usage](independent-guide-zip.md) and `tests/test_independent_guide_jobs.py`. These new commands have not submitted or imported a **real ChatGPT relay result**.

**Next:** decide how automatic task proposals become persistent **authorized** independent requests, handle a coordinator's job/attempt ledger, and wire them to the local relay without duplicate submissions. The planner itself still makes no model call. Do not require a target guide for every translation.

**Acceptance:** one work with two target languages yields one work reference and two target guides; repeat checks submit nothing; existing references are never overwritten without a versioned regeneration; old requests keep working.

### M2. Local authorized relay coordinator — NOT STARTED

Discover accepted project tasks; reconcile project task state with the external relay's transport ledger; package into immutable attempt ZIPs, copy atomically into watched input only when the owner has authorized this submission class, import valid downloaded responses, and commit/push safe approved changes. Locks, crash recovery, retries, no-op zero-model polling, stale inputs, duplicated completed results and Git conflicts all require tests. Separately verify the actual relay is operational on the Mac. Do not install/enable any new LaunchAgent without explicit owner action.

**Acceptance:** one authorized guide request travels Issue → local packaging → actual ChatGPT relay → validated guide files → Git commit, with a safe retry after simulated interruption.

### M3. Shared material library and two-pool Admin UI — NOT STARTED

Four scopes (general, target language, work, work+target), instruction/reference type, optional tags, ordered/removable Applied list, defaults that can be removed, material versions pinned at Issue acceptance. One deterministic assembler produces exact preview and ZIP contents. Full private-source preview must happen at an authorized local step, not through public Pages. Existing translation requests retain backwards compatibility.

**Acceptance:** select work/target/nodes/materials in Admin, pin exact order/versions, and import translated node-level results using their supplied guides.

### M4. Real integration and ZIP contract consolidation — NOT STARTED

Run actual whole-work guide, target-guide and translation round trips. Evaluate output size/context coverage, malformed ZIP handling, retries/restarts, snapshot/report preservation and Pages safety. Only after that select a unified long-prose output format (likely JSON metadata plus Markdown body files) and retain compatibility adapters for historical formats.

## Explicit current facts and risks

- `queue.json`: Wells `gutenberg-36` has **Japanese only**. Do not claim Korean is selected.
- `guide-requests.json`: accepted Issue **#12** asks for both Wells work guide and Japanese guide through the **legacy combined** output contract. A pending legacy request must suppress duplicate proposals for both of these products for the same source fingerprint.
- Both Wells and Frankenstein have canonical source trees, but neither has a recorded translated edition.
- The two existing translation ZIP protocols differ and must not be silently conflated.
- Existing offline relay tests do not prove the physical browser transport ran.
- Reader/review publication requires separate explicit approval; public Git commits themselves distribute content.

## Maintaining a trustworthy handoff (mandatory for future work)

1. **Start:** read `AGENTS.md`, `STATUS.md`, this roadmap, the pertinent design and actual source/tests. Inspect Git state, pending Issues, current guide pointers, branch and any CI runs. Never treat prior conversation text as more authoritative.
2. **Before modifying:** identify the next bounded milestone, its invariants and compatibility constraints. Put substantial design choices here, or in a linked focused document.
3. **With every PR:** update this document's completed/remaining status and `STATUS.md`; record exact commands/tests, whether they passed, environment limits, whether a real model/relay/browser was exercised, and links to PR or commits. A failed or unexecuted test must be labeled as such.
4. **Before merge:** check documentation and code describe the same actual behavior, no unchecked submission/publishing, and tests for changed logic. Don't describe a branch-only change as released.
5. **After merge:** ensure the canonical `main` documents reflect the merged behavior and remaining tasks; record production execution/CI/Pages checks only when observed. A PR link is sufficient for provenance; do not invent a deployment.
6. **On interruption:** the latest committed roadmap, STATUS, code/tests, and GitHub requests must suffice to resume. Avoid maintaining a contradictory second checklist in chat or private notes.

A test checks the existence of this handoff and its key sections, but meaningful accuracy still requires editorial discipline; no automated test can guarantee every status claim is truthful.
