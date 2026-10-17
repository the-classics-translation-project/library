# The War of the Worlds — source notes

## Decisions

- 2026-10-18: First AI-assisted structure of the existing admitted Gutenberg #36
  package. Keep one work with the two printed Book divisions and their 17 and 10
  chapters. Use the actual body headings, including their punctuation, as labels;
  the contents entries are not substitute chapter headings.
- Keep the byline and Kepler epigraph (b000011–b000012) as root prose and the
  complete contents table (b000013–b000017) as a front-matter child before Book
  One. This preserves the acquired order and the duplicate contents information.
- Exclude distributor header b000001–b000008 and back matter b000930–b000981
  from the literary tree, with reasons in acquisition/plan.json. The complete
  original package, including license and credits, remains in acquisition/.
- Exclude b000009, a lone slash before the title, as an apparent formatting
  artifact. Its origin is uncertain; it has not been deleted from the acquisition.
- Metadata status is `imported`, not `reviewed`. No edition or translation was
  created; the requested Japanese target remains future work.

## Observations

- The source title is b000010. Book One starts at b000018, Book Two at b000621;
  the final epilogue heading is b000916 and its last prose block is b000929.
  All narrative blocks remain within their chapters, including quoted newspaper
  headlines and dialogue; these are not new structural headings.
- The package header identifies H. G. Wells and an electronic release date of
  2004-10-01, last updated 2026-03-30. Those are electronic-edition dates, not
  historical publication dates. Acquisition occurred 2026-10-17.
- Existing rights-metadata.rdf identifies Wells (1866–1946), English, and
  Gutenberg's US public-domain designation. Its automatically generated synopsis
  is catalogue ancillary material and is not part of this acquired novel's tree.
- Existing admission-evidence.json cites the Morgan Library's first-edition
  record (PML 147397), https://www.themorgan.org/printed-books/371751, for 1898,
  London: William Heinemann. This job used the saved evidence; it did not freshly
  verify that webpage or identify Gutenberg's exact print exemplar.
- Existing rights.json records automatic US/Japan admission under
  `gutenberg-us-jp-v2`. The rights and acquisition evidence were left unchanged.

## Open questions

- The exact historical printing underlying this Gutenberg transcription remains
  unverified; the 1898 citation does not establish transcription identity.
- The lone slash's origin remains uncertain. Reconsider it against a verified
  exemplar if available; do not silently reimport the established tree.
- AI analysis and mechanical block coverage do not establish human structural
  review or literary fidelity. Independent structural review remains outstanding.
