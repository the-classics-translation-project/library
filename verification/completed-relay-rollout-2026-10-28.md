# Live completed-relay rollout — 2026-10-28

The implementation in [PR #27](https://github.com/the-classics-translation-project/library/pull/27)
merged as `492a4f7`. The owner's Documents checkout fast-forwarded to it.
The existing relay jobs 25 and 26 already reported `complete`, with the exact
original request hashes, expected filenames and valid ZIP archives recorded in
[the rehearsal](completed-relay-import-rehearsal-2026-10-28.md). Neither request
was resubmitted and the relay queue was not changed.

| Step | Observed result |
| --- | --- |
| `relay-coordinator sync` | No new guide prepared or submitted. |
| `reconcile --import-ready --recover-completed` | Imported the held Frankenstein English target guide, preserving its prior transport-review reason; observed model `unknown`. |
| `relay-direct-reconcile` | Imported the Wells Japanese chapter II result as a draft; observed model `unknown`. |
| `./ctp validate` | Passed: 4 works, 4 editable editions, 4 frozen snapshots, 3 generation runs. Structural/provenance validation does not establish literary fidelity. |
| `./ctp build --demo --epub` | Passed locally; this was not a remote deployment. |
| `./ctp draft-publish` | Pushed [commit `4d5dc7a`](https://github.com/the-classics-translation-project/library/commit/4d5dc7ac2ab93a860bebd4c5e7ed8319ea306ddc), exactly 20 draft/provenance/archive files; no `catalog.json` change. |

The imported guide has an immutable English reference, current pointer and
guide-task run record. The chapter result supplies Japanese text for source
node `n0005`, a glossary, suggested notes, archived request/response, an
import receipt and a generation run. The edition remains `draft`; other
chapters remain untranslated. The chapter and source were inspected for the
expected chapter scope and broad story order. No human literary review or
reader release is claimed. The model label was not independently visible and
was recorded as `unknown` for both imports.

The existing **Import completed Classics relay results** app heartbeat was
updated in place and confirmed `ACTIVE` at its existing 30-minute interval.
Its prompt matches `prompts/relay-result-import.md`. A manual repeat produced
zero new preparation, a guide already in `imported` state, an existing direct
attempt, passing validation, and no publication commit or push. The Documents
checkout was clean and matched `origin/main` after publication. This checks
idempotence, not an actual timed wake or sleep/restart recovery.

[GitHub validation for the draft commit](https://github.com/the-classics-translation-project/library/actions/runs/40709341108)
and [Pages deployment](https://github.com/the-classics-translation-project/library/actions/runs/40709341239)
both passed. A real Chrome visit to the deployed Admin on 2026-10-28 showed
*Frankenstein; or, The Modern Prometheus* — English Literary Guide in the
Available materials for Gutenberg #41445; that work reported its English
terminology guide saved. Gutenberg #36 showed 2/60 fields drafted and retained
its Japanese translation guide in Available materials. No Issue was submitted
during this browser check. No new model job was submitted, no reader catalogue
was edited, and no generated draft was approved as a literary release.
