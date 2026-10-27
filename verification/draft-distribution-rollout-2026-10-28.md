# Imported-draft distribution rollout — 2026-10-28

This records the first live use of the standing public-Git draft-distribution
policy. The implementation merged in [PR #25](https://github.com/the-classics-translation-project/library/pull/25)
as `157a648df06ae2546243b9c834ef7f0f999f3678`.

In the owner's Documents `main` checkout, `./ctp validate` passed and
`./ctp draft-publish` pushed [commit `0b2e62ca1134c3ebc631a6a4fe38f9362376a07a`](https://github.com/the-classics-translation-project/library/commit/0b2e62ca1134c3ebc631a6a4fe38f9362376a07a)
to canonical `main`. The commit contains exactly nine guide, pointer, receipt
and provenance files from imported coordinator attempts
`attempt-d626c1b31c8e44548aa32e0bae88d103` (Wells combined guide) and
`attempt-dd72147c7f9d46b98a8534531ffc077b` (Frankenstein work analysis).
It contains no `catalog.json` change, held result or new model output. The
checkout was clean and equal to `origin/main` afterward.

The push-triggered [validation run](https://github.com/the-classics-translation-project/library/actions/runs/40545278652)
and [Pages run](https://github.com/the-classics-translation-project/library/actions/runs/40545278692)
both passed. `./ctp build --demo --epub` passed locally after the push; Admin
metadata contained three public guide IDs: `guide.work.gutenberg-36`,
`guide.target.gutenberg-36.ja`, and `guide.work.gutenberg-41445`.

The existing 30-minute **Import completed Classics relay results** app
heartbeat was updated in place and confirmed ACTIVE with
`prompts/relay-result-import.md`. A manual pass of its command sequence ran
coordinator sync (zero prepared jobs, zero model calls, zero relay submissions),
reconciled imports (no new import), `./ctp validate` (pass), and
`./ctp draft-publish` (no-op: no new commit or push). The Frankenstein
standalone target-guide attempt remained `needs_review`; the direct Wells
chapter-II attempt had no exact return ZIP. Neither was resubmitted.

A real Chrome visit to the deployed
[Admin](https://the-classics-translation-project.github.io/library/admin/)
showed the Frankenstein work reference, Wells work reference and Wells Japanese
guide in Available materials. Clicking the Wells work reference and Add moved
it into Applied as material 1, with hash prefix `62c909253fca`. No Issue was
submitted. This checks deployed metadata and material selection, not a
translation, literary review or physical Safari/iPad behavior.

An actual timed run of the updated heartbeat and sleep/restart recovery have
not yet been observed. The two held ZIP results still need separate recovery
or diagnosis. Reader distribution remains governed by `catalog.json` and
separate editorial approval.
