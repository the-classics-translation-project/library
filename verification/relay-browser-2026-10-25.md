# Browser and local runtime checks — 2026-10-25

Observed with the connected Chrome profile through actual browser interaction.
These checks used no simulated storage and did not submit new test Issues.

## Deployed Admin

URL: https://the-classics-translation-project.github.io/library/admin/

- Expanded the Wells root and Book One: chapter controls became visible.
- Selected chapter n0004: one node selected and a translation Issue link appeared.
- Changed scope to missing-only and references to notes: inspected the generated
  link's decoded JSON; it contained n0004, ja, scope=missing and reference=notes.
- Selected Book One: all 17 chapter checkboxes plus the parent were selected,
  and the UI reported 18 nodes. No GitHub Issue was submitted by this check.
- Previous-text/revision controls were disabled with no approved revisions.
- Guide-generation links carried work/target, source and prompt identities.

## Local workbench with synthetic sample

Built with `./ctp build --demo --epub` and served on a loopback-only temporary HTTP
server. Opened the tree-work/en-modern sample in the actual Chrome browser.
Saved a section note explicitly labeled as a browser persistence test. The
note and count survived page reload and navigation to another section and back.
This verifies actual Chrome local-origin storage/navigation for the synthetic
sample, not production-origin persistence, native text selection or cross-device
synchronization. Screenshots were retained privately with the live attempt files.
No test annotation was transmitted to GitHub or applied to a real novel.

## Source worker observation

The existing installed LaunchAgent reported 317 runs, last exit code 0 and a
1,800-second interval. Its recent stdout contained pending=[] and model_called=false;
its log was last modified at 2026-10-25 01:46:39 JST. The dedicated checkout was
clean at 5b64630. This establishes repeated idle execution beyond RunAtLoad,
not a successful headless model invocation, sleep/restart recovery or source review.

## Wells live relay trial

The external relay submitted the exact Issue #12 ZIP to a new ordinary Chat,
recorded as transport job 21. The visible model control showed Extra High.
The Chat subsequently reported completion after 13m43s, but the browser showed
“This response couldn’t load.” A reload exposed no downloadable output and its
response Copy control returned empty text. The original request and private
browser evidence were retained. The project attempt was stopped for review;
no transport queue state was changed and no duplicate model request was sent.
No generated guide was available to validate or import. Frankenstein's separate
work-analysis package was delivered second and remains awaiting relay pickup.

## Remaining

Physical Safari/iPad selection, responsive device interaction, production-origin
annotation storage and independent source-edition/structural inspection remain
unverified. Model/relay trial results belong in STATUS and the automation roadmap;
queue delivery alone does not establish completion.
