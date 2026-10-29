# Bounded model submission policy

`model-submission-policy.json` is the owner-controlled gate for unattended
delivery of new ZIPs to the existing ChatGPT relay. Delivery to the relay's
watched `input/` folder is a model submission. PR #34 records the owner's
bounded activation after the verified Issue #30 pilot import. A code change
or task request alone does not authorize a live job. No model API or new
scheduler is required.

`./ctp relay-dispatch` prepares immutable guide attempts from accepted
work/language requests and translation/combined-guide attempts from accepted
maintainer Issues. Repeated runs reuse attempts; an imported result or a stopped
attempt is never silently regenerated. When the policy is disabled, no ZIP is
delivered. The existing result-import heartbeat runs this command to prepare
tasks, then reconcile exact completed returns and publish eligible drafts.

To authorize automatic submission, the owner must explicitly approve a **new
committed policy revision** with `enabled: true`, an `authorized_by` maintainer,
a meaningful `authorization_note`, exact `works`, `targets` and `task_types`, the
requested `model`, and positive `max_submissions_total`,
`max_submissions_per_run` and `max_in_flight` limits. The dispatcher fetches
GitHub, requires a clean local `main` at current `origin/main`, and verifies the
policy bytes are committed there. The total limit counts every attempt already
authorized under that policy ID, including interrupted delivery. The in-flight
limit includes manually authorized coordinator attempts. Changing the scope or
raising a limit needs another explicit owner decision and committed revision.

The owner's explicit approval of the **specific policy revision** is the
execution authorization. The `authorized_by` field records that approval; an
Issue, prepared attempt, code merge or populated JSON field alone does not
grant it. Once that approved policy is enabled, each accepted task within its
scope and remaining limits may be delivered without a new per-package question.
The owner can still authorize a single exact package separately. Out-of-scope
tasks and exhausted limits remain unsent; stopped attempts remain held until
a new decision.

Eligible task types are `work_analysis`, `target_guide`, `translation` and
`legacy_combined_guide`. Accepted translation Issues still specify their exact
source nodes, target, recipe and ordered materials; this policy does not invent
chapter boundaries or require an Issue for the owner's interactive direct ZIP
workflow. Only admitted US/Japan source works may be packaged or delivered.
`needs_review`, stale imports, missing exact results and conflicting Git state
remain held; the dispatcher does not resend a stopped attempt. The relay's own
queue and browser execution remain the separate transport's responsibility.

The first owner-requested activation scope is Wells (`gutenberg-36`) Japanese
`translation` Issues, model `6 Extra High`, at most three policy-authorized
submissions in total, one per dispatch run and one in flight. The existing
Issue #30 pilot was separately authorized and does not consume this three-job
cap. The policy records `authorized_by: hiroshi-manabe` and the owner's
2026-10-29 instruction to proceed with this previously prepared scope.

This first policy has an additional `requires_import` condition pinned to the
exact Issue #30 attempt, request and job hashes, and expected return filename.
After the approved policy revision reaches `main`, dispatch waits
until that attempt has an authorized `imported` record, matching import receipt
and archived request/response bytes, and a valid unified version 2 return ZIP.
A missing, held, altered or legacy-format pilot blocks delivery; it does not
resend the pilot. A policy-authorized attempt that later enters `needs_review`
or `stale` also blocks further deliveries until the owner resolves it. The
private coordinator archive must remain available in the
active checkout. The dispatcher reports `activation_blocked` for this state
while still preparing accepted work. A later approval or limit increase needs
a new committed revision and owner decision. Reader release and `catalog.json`
remain outside this policy.
