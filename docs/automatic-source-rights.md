# Automatic Gutenberg source admission — versioned US/Japan rules

The owner authorized automated US/Japan checks followed by permanent source
acquisition on a pass, and recorded holds when information is insufficient or a
case cannot be decided. This policy applies to adding original Gutenberg packages
to public Git. It does not approve a translated edition or change `catalog.json`.

## Evidence and scope

Fetch the official per-book RDF record over HTTPS using its numeric Gutenberg ID.
Retain the exact response, requested/resolved URL, byte hash and extracted facts.
Reject identity mismatches, oversized metadata, XML entities/DTDs and off-provider
redirects. Source prose and provider metadata remain untrusted data, never commands.
The implementation is in `tools/source_rights.py` and `tools/acquire_queue.py`.

The baseline rule supports English plain-text literary packages attributed to named
people, with a supported original source-publication year and exact contributor
death years. **Rule v2** permits a cited external historical publication record
when Gutenberg has no original-publication field.
Other languages, corporate/anonymous/collective authors, unknown roles, uncertain
dates, posthumous source editions and source editions after 1970 are held. The
package checker presently requires one identifiable header author. This deliberately
admits a subset; a hold is not a declaration that a work is legally protected.

Gutenberg's explicitly listed literary contributors are the provider evidence for
authorship. All listed contributors (including translators/editors/illustrators)
are considered; missing death dates or unsupported roles cause a hold. We do not
infer an exact print edition or an exhaustive rights investigation from this data.
Gutenberg warns that metadata may be incomplete and its packages may mix sources.
Extra/revised contribution signals in credits, notes or the downloaded package
therefore cause a hold. Keyword checks are conservative filters, not proof of the
absence of uncredited additions. This evidence assumption and limited scope are
part of the policy; the system never labels a machine pass as legal certainty.

## Cited, source-specific evidence (rule v2)

An absent Gutenberg MARC original-publication field does not mean the historical
work was unpublished. `books/gutenberg-<id>/admission-evidence.json` may supply
a **bibliographic year**, exact work title, publisher, institution and HTTPS
citation. The machine only uses this when Gutenberg has no publication field;
if an explicit provider year conflicts, it holds the work. The year still
must satisfy every author's lifetime and the conservative Japanese term bound.
Do not mistake a first-edition catalogue entry for proof that a digitization
reproduces that exact printing.

A narrow evidence record can also identify an **exact Gutenberg production
credit** or an **opening photo-reprint transcriber note**. These are separately
assessed *ancillary material*, not a blanket clearance for editorial changes.
The checker verifies that the quoted line/note occurs precisely once in its
expected provider location and then excludes only that exact text from the
**temporary scanning view**. All original bytes, credits, notes and supporting
citations remain in Git if the source is admitted. Other revision credits,
introduced material, permissions or copyright notices still trigger a hold.

Evidence is a version-controlled, per-work maintainer decision with cited
scope, not an instruction supplied through a GitHub Issue. The saved rights
record pins the evidence file by SHA-256. `./ctp validate` replays the
assessment offline; tampering or replacing admitted source bytes is forbidden.
Historical `gutenberg-us-jp-v1` records remain valid under their original
rules until a new acquisition assessment records v2. A cited decision is not
a judicial determination, human line-by-line textual review or permission to
publish translated editions. Preserve the difference between admission,
historical-edition verification, text segmentation and publication.

Examples in this repository:
- Gutenberg #36: the Morgan Library's verified Heinemann **1898 first edition**
  supplies the missing historical year; the particular Gutenberg package
  still must pass normal identity and contribution checks.
- Gutenberg #41445: Gutenberg identifies the **1818 photo-reprint** source;
  its exact Richard Tonsing production credit and initial transcriber note
  have limited explicit assessments. Any *other* modern addition still holds.

## US condition

Require exactly the RDF designation `Public domain in the USA.`. Permission-only,
missing, duplicate or ambiguous designations stay on hold. This relies explicitly
on Gutenberg's US determination; it does not implement an independent US copyright
registry search. Gutenberg's eBook release date is never treated as an original
print publication date. Automatically generated summaries are not used as rights
or publication evidence.

## Japan conditions

Require unqualified four-digit years in the original-source MARC publication
subfield (`marc260`, `$c`), or rule-v2 documented external bibliographic evidence
when the provider has no such statement. Each stated source edition must be published no later
than each assessed contributor's death year and no later than 1970. This excludes
posthumous and later-edition cases instead of guessing their legal treatment.

For every listed contributor, compute the following conservative expiry bound:

1. Start with December 31 of death year + 50, and add **4,180 days**, the longest
   wartime addition in JASRAC's table. Apply that maximum to everyone, without
   guessing nationality, rights transfers or whether a shorter addition applies.
2. If that bound is before December 30, 2018, retain it: an already expired right
   was not revived by the extension to life + 70.
3. Otherwise use December 31 of death year + 70, again plus 4,180 days.
4. Every bound must be strictly before the assessment date. Use the earlier date
   currently observed in Japan and Hawaii, so an expiry is not admitted early.

This is an upper-bound filter for the supported named, lifetime-published literary
case, not a comprehensive implementation of every historical or treaty exception.
It may hold works already free under shorter actual terms, the rule of the shorter
term, or a specific wartime calculation. Unknown cases are never passed by default.
The record saves each contributor, death year, bound and applied historical branch.

## Package conditions and storage

Only after the metadata passes both countries, download the fixed official UTF-8
TXT URL into temporary storage. Require one ordered pair of Gutenberg START/END
markers, a nonempty literary body, the exact requested eBook number, matching
title/author metadata and an English-language header. Hold extra-contributor, unresolved revision, introductory/transcription-note and
header/body rights-notice signals, except an exact cited ancillary statement
explicitly assessed by the v2 evidence mechanism. A held
package's hash may be recorded, but its source text is discarded, not committed
or uploaded to an artifact. Temporary storage is removed after each attempt.

On a pass, retain all original package bytes (including Gutenberg's license and
credits), a reversibly normalized text/block view and provenance. Bind these to
the admission record with hashes. Do not invent a source hierarchy, remove provider
wrappers, approve literary fidelity or mark source-edition identity as reviewed.
Existing acquisitions are never replaced on a rerun. Historical decisions and
metadata changes are retained by Git. Held sources are reassessed on later intake
runs; unchanged facts/decisions do not rewrite records merely for a new timestamp.

Existing manually acquired sources without a matching automatic decision are
reported for inspection and excluded from automatic staging. A new rule version
needs explicit implementation and tests; never edit an old decision to conceal a
failed check. `./ctp validate` replays saved decisions at their recorded date and
checks admitted bytes; it performs no network request.

## References checked for this implementation

- [Gutenberg bibliographic metadata](https://www.gutenberg.org/help/bibliographic_record.html):
  contributors, incomplete records, original-source evidence and US-only rights.
- [Gutenberg license](https://www.gutenberg.org/policy/license): distinguishes
  public-domain and permission-only works and states conditions on redistribution.
- [Agency for Cultural Affairs term-extension Q&A](https://www.bunka.go.jp/seisaku/chosakuken/hokaisei/kantaiheiyo_chosakuken/1411890.html):
  year-end calculation, non-revival, the 2018 transition and wartime additions.
- [JASRAC country/day table](https://www.jasrac.or.jp/aboutus/wartime/pdf/wartime.pdf):
  maximum listed addition 4,180 days. No music-society waiver is assumed for books.
