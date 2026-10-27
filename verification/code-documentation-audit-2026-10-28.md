# Code/documentation consistency audit — 2026-10-28

**Reviewed baseline:** public `main` at commit `3456b612c300` (2026-10-26 UTC; October 27 Japan time). Read `AGENTS.md`, `STATUS.md`, the automation roadmap, translation-material and local-coordinator documentation, the current Python/JavaScript implementation and related test declarations. Reviewed GitHub's completed validation and deployment runs. **This is a static/remote audit.** No access to the owner’s uncommitted Mac checkout, external `chatgpt-relay` source/SQLite database, current Chrome sessions or live app automation state; no local Python/JS tests or model calls were run during this audit. The tests and live observations cited below were previously recorded by local agents.

## Verified coherent pieces

- Source rights/structure, read-only guide discovery, independent and legacy guide ZIP handlers, local coordinator prepare/sync/explicit submit/reconcile/import, and the source worker have committed implementations. The coordinator has a local attempt ledger and safeguards against implicit resubmission.
- Versioned translation materials are discovered by four applicability scopes. `tools/materials.py` validates material IDs/hashes and emits only **committed** material metadata in the public Admin manifest. The test fixture checks that a locally saved but uncommitted guide is absent.
- The Admin's Available/Applied list supports add/remove/move up/down and emits ordered v2 material IDs and hashes. `tools/translation_jobs.py` snapshots the chosen material text on accepted v2 Issues. Both local preview and Issue ZIP use `prepare_job`; the direct adapter saves its assembled input with the ZIP. Tests cover order, pinning, privacy filtering and preview identity.
- The earlier v1 Issue and direct relay ZIP contracts remain intact. Requested default model is `6 Extra High` in the new guide and translation paths.
- Prior recorded tests: 186 Python tests, 19 JS core checks, project validation and HTML/EPUB build passed. Latest `main` GitHub validation and deployment runs completed successfully. This audit does not re-certify literary quality or the external browser workflow.

## Confirmed or explicitly unresolved discrepancies

### A. Applied-list removal does not completely control editorial context — fix next

In `site/translation-admin.js`, every Applied item is presented as removable, but `tools/translation_jobs.py::prepare_job` always adds `editorial_policy` to `job.context`. When the independent **Earlier material** dropdown is `notes` or `text`, it also inserts work notes, edition notes, and both guides outside the Applied list. `tools/translation_relay.py::package` similarly includes existing policy/notes/glossary alongside optional explicitly selected materials.

This is a genuine transitional difference from the design's **removable, ordered** editorial stack: excluding a document from Applied does not guarantee exclusion of its contents. Existing previews display the actual assembled text, which is good, but do not eliminate this surprise.

**Decision:** decide which parts of editorial policy are mandatory *operational* constraints and show those visibly as locked/pinned inputs. For v2, make all **optional editorial** references controlled by the Applied list or another explicit pinned reference with non-overlapping semantics. Keep legacy v1 semantics unchanged. Add a test where a guide is removed from Applied while the earlier-material dropdown is `notes` and verify that nothing is invisibly reinstated.

### B. Material pinning is complete for selected entries, not for older context — fix next

`translation_jobs.intake` saves the exact `materials_snapshot` for accepted v2 Issues. However, `prepare_job` still reads current work notes, edition notes, policy and guides when it runs. Those files can change between Issue acceptance and ZIP export, changing the job even though the Issue's ordered materials are pinned. `reference.mode=text` does pin the exact frozen prior translation revision.

**Decision:** for new v2 requests, pin **every** editorial/context input at acceptance (or explicitly record an execution-time reference choice), and ensure that the preview and actual model ZIP are byte-identical. Extend the tests to modify a legacy context file *after* Issue intake. Historical v1 requests must remain replayable. Document what is and is not pinned.

### C. An empty Applied list falls back to legacy v1 — fix in the same UI/contract pass

The Admin emits schema v2 only when `selectedMaterials.length > 0`; an explicitly empty list emits v1. As a result, a request cannot distinguish “I deliberately applied no optional materials” from an old v1 request, with its default context behavior.

**Decision:** emit v2 even with `materials: []` for new Admin requests, after defining the optional/mandatory context boundary. Preserve support for previously accepted v1 Issues and ZIPs.

### D. Private generated guides cannot yet be selected in public Admin — design decision

This is an **intentional privacy rule, not a bug**. `materials.public_metadata` and `site_builder.admin` show only committed references. The three previously imported guides are reported in local private state, not on public `main`, and therefore are absent from the Admin selector. The direct local translation adapter may select them explicitly.

**Decision:** choose a safe path for the owner's intended “guides are generated, then selectable” UX: separately approve public Git distribution of a guide, or build a private/local selector or a metadata-only registry with local content resolution. Do **not** publish AI-generated guide prose merely to make it show in a public dropdown. Record any cross-checkout synchronization/backup policy: Git-ignored guide data and attempt ledgers are not recoverable from a clean public clone.

### E. Work target enrollment versus translation target choice — policy decision

The Admin translation selector offers all globally supported target languages, while `validate_request` only checks `project.json.targets`, not that the target is in the particular work's accepted `queue.json.targets`. This differs from the intended progression “select work + requested languages, then translate those editions”; it may instead be a deliberately flexible alternative. Clarify whether a translation Issue automatically authorizes a new work target or must follow separate work-language intake. Add a test for the chosen rule.

### F. Documentation status needs chronological tightening — fix now and maintain

`AGENTS.md` still said that real Admin tree interaction was unverified, even though `verification/relay-browser-2026-10-25.md` and `verification/materials-browser-2026-10-27.md` report real Chrome checks. `docs/translation-materials-design.md` still called the initial library path/metadata mechanism undecided after `materials/manifest.json` was implemented. Long `STATUS.md` and roadmap sections interleave older “not yet imported” observations with newer successful imports; dates and historical headings help, but future agents should start from the newest state at the top.

Current and historical observations should remain distinguishable. Retain provenance in dated verification documents rather than repeatedly growing the primary status snapshot. Never overwrite or erase original failure evidence.

## Current external blockers (not code failures proven)

Two owner-authorized live trials reached `needs_review` after the Chat claimed completion but no real downloadable ZIP was verified: independent Frankenstein English target guide (relay job 25) and Wells Japanese chapter II `n0005` (job 26). Separate browser clicks saw links without `href`. Neither was imported or automatically resent. Prior Wells combined and Frankenstein work-reference guide imports succeeded locally, establishing that some relay paths work. The exact failure cause (model failed to create a file, Chat attachment persistence, rendered link, or relay's download interaction) is **not established**.

**Next experiment:** inspect the existing attempts' evidence and, without resending them, try to recover the exact original result artifacts. Then separately authorize a minimal ZIP-attachment smoke test on the same model/browser/relay path (and, if useful, a control through manual ChatGPT UI). Verify real ZIP bytes and the precise expected basename before declaring the transport complete. Do not treat a textual sandbox link or “finished” Chat message as an attachment. Change or retry the transport only after identifying the failure and obtaining the owner's authorization.

## Recommended next implementation sequence

1. **P0 — Unblock actual artifact delivery.** Analyze job 25/26 outputs without unauthorized resend; verify that ChatGPT can produce an actual attached ZIP and that the external relay can download it. Repeat a bounded real translation import only when an exact archive exists. Keep failed-attempt history.
2. **P1 — Reconcile v2 prompt semantics.** Address A–C together: optional materials truly optional, explicit locked operational instructions, full context pinning, and v2 empty Applied requests; preserve v1 compatibility and add regression tests.
3. **P1 — Decide private-guide discovery/storage.** Address D, including user-visible availability and backed-up state without leaking unpublished text to public Pages.
4. **P2 — Align work-language authorization.** Resolve E; then run a real accepted v2 Issue → intake → local exact preview → relay → translated-node import with the chosen materials.
5. **P2 — Consider auto-submission policy separately.** Current `sync` only prepares independent guide tasks and the heartbeat only imports previously authorized results. To deliver the owner's fully automatic initial Issue experience, define a bounded, auditable authorization policy and add an idempotent dispatcher only with explicit approval. Do not quietly reinterpret “prepare” as “submit.”
6. **P3 — Consolidate return ZIP formats** only after both standalone guide and translated-node end-to-end trials succeed. Preserve historical packages/importers. Continue real browser and sleep/restart verification.

## Repository-state boundary

At audit time `queue.json` still requests **Japanese only** for Wells; Korean is illustrative. `translation-requests.json` and `catalog.json` contain no real translation requests or approved reader revisions. Guide pointers imported locally are absent on public `main`. Local work since the last pushed commit may be newer; inspect it before applying any implementation fix. The latest published `main` GitHub validation and Pages deployment both passed, but CI cannot validate private Mac/browser state.

This document is an **audit/next-action handoff**, not an implementation of the proposed fixes or permission to submit model requests, commit private guide prose, or publish literary editions.
