# Contributor reading and annotation

Read naturally. There is no required quota, correction form or sequence of review
states. The owner may use the workbench, an EPUB or ordinary HTML and give an AI
agent direct instructions instead of filing Issues.

Open a **particular revision** from the Workbench. Select words or paragraphs to
open the nearby comment box. Save to attach a highlight and a compact margin note.
The title, ancestor/section headings and author credit are selectable too. A source
body that includes an epigraph or footnotes can be annotated like other body text.
The optional Original panel is reference evidence, not a separately editable field.

Text selection can span paragraphs inside a field. A selection spanning a title
and its body is not one field; use two notes or the menu's Section note. Several
notes may overlap. Click a margin note or marked text to read/edit/remove it. Nearby
notes are stacked with connector lines. A note is clamped to two lines but retains
its complete text. Margins can be hidden from the menu; phone-width layouts use
highlights and the notebook instead of forcing horizontal scrolling.

Navigation does not discard saved notes. The notebook combines observations from
all sections of this revision. Export JSON for a backup. Notes are browser-local,
not automatically shared between devices or revisions. Browser/site data deletion
can remove them. A storage error is shown explicitly and new notes remain in memory.

Prepare an Issue after selecting which notes to include. Review/copy the generated
body, or attach the JSON for a larger report, and submit through GitHub. Opening a
form or copying data is not submission; notes are not silently cleared. The static
site carries no GitHub access token. Synthetic fixtures disable the outgoing Issue
link so tests cannot accidentally report fictional translation problems.

Each report includes the frozen revision, node field, exact selected text and
position/context. That is evidence of what was read, not a requested permanent
sentence ID. Later complete rewrites remain possible. The maintainer and AI decide
what to do, and do not mechanically apply comments as patches.

The UI is intentionally quiet; explanation and revision hashes belong in Help or
reports rather than above every paragraph. Actual iPad/Safari selection behavior
still needs testing on the device. The automated browser checks performed during
bootstrap used Chromium's isolated DOM and explicitly simulated storage, not a
claim of real device or cross-device persistence testing.
