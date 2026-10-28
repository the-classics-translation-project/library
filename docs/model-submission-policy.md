# Bounded model submission policy

`model-submission-policy.json` is the owner-controlled gate for unattended
delivery of new ZIPs to the existing ChatGPT relay. Delivery to the relay's
watched `input/` folder is a model submission. The policy is committed with
`enabled: false`; implementing or testing the dispatcher does not authorize a
live job. No model API or new scheduler is required.

`./ctp relay-dispatch` prepares immutable guide attempts from accepted
work/language requests and translation/combined-guide attempts from accepted
maintainer Issues. Repeated runs reuse attempts; an imported result or a stopped
attempt is never silently regenerated. With the policy disabled, no ZIP is
delivered. The existing result-import heartbeat can run this command to prepare
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

The current first activation proposal is one Wells Japanese chapter task with
one submission total and one in flight, after a real v2 Issue-based return ZIP
has been verified. This is a proposal, not an active authorization. The exact
request and owner-approved policy revision should be reviewed together. Reader
release and `catalog.json` remain outside this policy.
