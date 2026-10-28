# Automatic Git distribution of imported drafts

The owner authorized a standing **public Git draft-distribution** policy on
2026-10-28. Its machine-readable record is [`draft-distribution.json`](../draft-distribution.json).
It covers validated guide and translation drafts derived from works whose saved
source-rights records pass both the US and Japan checks. This is permission to
commit and push those **draft files and their provenance** to this public
repository. It does not authorize a model submission, human-review claim,
`catalog.json` change, reader/review listing, license selection, or KDP release.
The initial source admission remains a bounded evidentiary check, not a legal
guarantee for unrelated third-party material later inserted into a task.

Run `./ctp draft-publish` from the trusted local `main` checkout after result
imports. The existing 30-minute app heartbeat runs it after
authorized guide sync and completed-result checks for coordinator and direct
relay attempts. The command reads only imported
coordinator attempts and direct `relay-import` publication manifests. It checks
their exact request and result archives, recorded output hashes, source admission,
path scope, Git baseline and project validation; stages only the named imported
files; then commits and pushes to canonical `origin/main`. Other local files remain
unstaged. A repeat run is a no-op after a recorded push. A failed push leaves the
local commit and private records available for a safe retry. Git divergence,
altered output, missing evidence or a failed validation stops distribution for
review. There is no force push or automatic retranslation.

The importer still leaves output local first. A coordinator result with
`needs_review`, `stale` or no verified return ZIP has no publishable output.
Direct relay imports receive a private `publication.json` manifest only after a
successful installation. Older direct imports without that manifest require
review before distribution; the publisher never guesses their changed files.
Imported references retain their versioned Markdown, pointers and run records.
Direct translation drafts retain their edition metadata, prose, exact relay
archives and generation record. A Git commit makes these files public even when
the reading site does not list them. The site's reader/review selection remains
controlled by `catalog.json` and separate editorial approval.

To suspend future automatic Git distribution, set `enabled` to `false` in the
versioned policy; the heartbeat then observes a no-op. The source worker and relay
submission authorization are separate systems. A new source, guide or translation
task is never authorized merely by this policy.
