# Completed relay result rehearsal — 2026-10-28

The local relay ledger was read through SQLite read-only mode. Jobs 25 and 26
both reported `complete` at `2026-10-26T22:31:58Z`; the project attempts had
not been imported. No queue state or input ZIP was changed during this check.

| Job | Task | Archived request SHA-256 | Exact result SHA-256 |
| --- | --- | --- | --- |
| 25 | Frankenstein English target guide | `09de9095321c1efdee544475b0a1891ae9b86570242b1b3443d10711158b93ec` | `edf58e97982e70a2f2b85f73e250c81b86c79a0fd10f24b24b5f55a8e89d625d` |
| 26 | Wells Japanese chapter II | `507b16a8a45f455a06ad13b714b19fdfef7f188df59cbc3ef65c1825f106afde` | `0868348bdb294caf41c137c65ccf9b8f1ca7aa7a3e8953f341e83eef7c276701` |

Both downloaded ZIPs passed archive integrity checks. Their result manifests
identified the expected guide job and direct translation attempt. That alone
does not establish literary quality or a verified Chat UI model label.

An isolated clone of the owner's canonical-main checkout received copies of
the private attempt records. With the new implementation, completed-transport
recovery imported the guide as an `en` target reference (three editorial output
files) and recorded observed model `unknown`; the direct observer imported the
chapter as a Japanese draft with 58 fields still missing across the work.
`./ctp validate` passed in that clone. A no-push publisher rehearsal made one
20-file local commit containing the two attempts' exact outputs and no
`catalog.json` change. The relay database was byte-for-byte unchanged. The
clone was removed. The full offline Python suite passed (204 tests), with 11
focused tests passing after the final Chat URL guard. No model job was submitted or
resubmitted, and neither result was installed in the owner's live checkout by
this rehearsal.

Live import, automatic heartbeat execution, public Git push, CI/Pages outcomes,
and literary review remain to be verified after the implementation merges.
