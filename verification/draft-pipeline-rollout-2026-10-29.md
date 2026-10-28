# Bounded draft-pipeline rollout — 2026-10-29

## Canonical code and local activation

PR [#29](https://github.com/the-classics-translation-project/library/pull/29)
merged as `ac5d9a5`. Main-branch [validation](https://github.com/the-classics-translation-project/library/actions/runs/40720456789)
and [Pages deployment](https://github.com/the-classics-translation-project/library/actions/runs/40720457146)
passed. The owner's Documents checkout was clean and fast-forwarded to that
commit. The pre-existing 30-minute **Import completed Classics relay results**
app heartbeat was updated in place from the saved
`prompts/relay-result-import.md` prompt and confirmed ACTIVE. No new scheduler
was installed. The first timed run on this updated prompt and sleep/restart
behavior have not yet been observed.

The exact new sequence was run manually after updating the checkout:
`./ctp draft-publish` published nothing; `./ctp relay-dispatch` prepared and
submitted nothing with `policy_enabled: false`; coordinator and direct
reconciliation imported nothing; `./ctp validate` passed (4 works, 4 editable
editions, 4 frozen snapshots, 3 generation runs); final `./ctp draft-publish`
published nothing. There was no model call, relay queue mutation, draft push or
reader-catalogue change.

## One prepared v2 Issue pilot

A real local Chrome Admin interaction selected Wells Japanese chapter III
(`n0006`) with an empty Applied list and showed a v2 request URL retaining
`materials: []`. This was a browser-only check; it submitted no Issue.

The authenticated maintainer subsequently opened
[Issue #30](https://github.com/the-classics-translation-project/library/issues/30)
for the same chapter with an ordered list of editorial policy, Wells work
reference and Wells Japanese guide. GitHub intake accepted it in `1515581`.
The local dispatcher prepared exactly one private translation attempt,
`attempt-7195ba9ade6345339ac6dc167b4b44a8`. Its request ZIP is
`ctp-translation-issue-30-28bea917e40f.zip`, SHA-256
`6950b9894337441ad9f2c3dca60380f0929ddb818fed9a2cddc46ecd418cb696`;
the manifest job hash is
`e04c3102148ce4883d7745419fd0f3f605e1140ae2b9ed44743d048651501df3`.
The requested model is `6 Extra High`, the sole output fields are `n0006` label
and text, and the expected return is
`ctp-translation-issue-30-28bea917e40f-result.zip`. The assembled input is
49,919 UTF-8 bytes. The archived request was validated against the current
source. It was initially `prepared`, `authorization: null`, and absent from
relay input. Those were pre-authorization observations, not a completed job.

The Issue intake's own [site job](https://github.com/the-classics-translation-project/library/actions/runs/40720821029)
failed in the new dispatcher fixture: it expected only synthetic Issue #62 in
the copied request queue, but the real accepted Issue #30 was also present.
The intake itself and request commit succeeded. The follow-up change clears
the copied queue inside that fixture; the focused test and full 210-test suite
passed locally. [PR #31](https://github.com/the-classics-translation-project/library/pull/31)
merged as `572c36e`; its main [validation](https://github.com/the-classics-translation-project/library/actions/runs/40722434726)
and [Pages deployment](https://github.com/the-classics-translation-project/library/actions/runs/40722434723)
passed with Issue #30 in the queue.

## One exact authorized delivery

The owner explicitly authorized one submission of this exact Issue #30 ZIP
in the chat on 2026-10-29. Immediately before delivery, the archive was still
`prepared`, `authorization: null`, and validated against current source;
its SHA-256 matched the proposed
`6950b9894337441ad9f2c3dca60380f0929ddb818fed9a2cddc46ecd418cb696`.
`./ctp relay-coordinator submit` recorded the bound authorization and copied
the ZIP once into the existing relay's watched `input/` folder. The input file
hash was rechecked and matched exactly; local main stayed clean. The attempt
state is `delivered` as of 2026-10-28 16:08 UTC. No relay job ID, model receipt,
result ZIP or import has been verified yet. The repository's standing
`model-submission-policy.json` remains disabled with zero authorized automatic
submissions; this individual authorization does not enable future jobs.

## Remaining decisions and checks

Verify relay registration and its actual model label, exact
request/result identity, unified return ZIP, draft provenance and import. A
standing automatic-submission policy is still disabled and needs a separate
bounded owner decision after the live pilot. Translation quality and reader
release have not been approved.
