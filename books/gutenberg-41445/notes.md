# Frankenstein — source notes

## Decisions

- 2026-10-18: First AI-assisted structure of the already admitted Gutenberg
  #41445 package. Keep a single work with its three internal volume divisions,
  four opening letters and 23 chapters (7, 9, 7), retaining numbering restarts.
  Metadata status is `imported`; no edition or translation was created.
- Use b000012–b000014 as the root title and b000015 as the first volume label.
  The second and third volume labels include their preceding repeated title
  blocks (b000322–b000325 and b000552–b000555). This asymmetry preserves the
  acquired title-page order without inventing a shorter label or moving a title
  after its volume designation. All labels are mechanically copied.
- Volume branches own their opening imprint/epigraph text. Volume I also retains
  the dedication, followed by the labeled preface. Preserve repeated half titles
  b000030–b000032 and b000109–b000111 as unlabeled body children in their original
  positions before the letters and chapters. Do not treat them as new volumes.
- Keep embedded letters, dates, quotations, verse and ornamental separators
  within their containing letter/chapter body. Letter IV retains its successive
  dated entries. Preserve b000321 and b000551 as unlabeled volume-end children.
- Treat b000806, `WALTON, _in continuation_.`, as a distinct labeled child of
  Volume III following Chapter VII. The preceding separator b000805 stays at
  the end of Chapter VII. Keep its dated entries together and b000865 as an
  unlabeled final `THE END.` child. This is a structural interpretation, not a
  claim of independent historical typography verification.
- Exclude only b000001–b000010 (provider header), b000011 (modern transcriber
  note) and b000866–b000917 (provider end marker/license/ancillary back matter).
  Reasons are in acquisition/plan.json; the complete package remains unchanged.

## Observations

- The saved provider RDF names Mary Wollstonecraft Shelley (1797–1851), English,
  and original publication in the United Kingdom by Lackington, Hughes, Harding,
  Mavor, & Jones, 1818. The three acquired title pages also print London, that
  publisher and 1818. These are source statements, not an independent collation.
- The package was retrieved 2026-10-17. Its electronic release is 2012-11-23 and
  header update is 2026-10-06; neither is the historical publication date.
- The provider's ancillary note says it was produced from a photo-reprint of the
  1818 edition. Existing admission-evidence.json separately assesses that note
  and the Richard Tonsing digitization revision credit. They are retained in
  acquisition, with neither promoted to authorial prose nor silently erased.
- No contents table is present in this normalized package. The repeated title
  pages and epigraphs are meaningful retained source matter, not distributor
  boilerplate. No additional modern essay or preface was identified in the
  retained span b000012–b000865.
- The closing journal has `September 12th.` at b000837 and `September 19th` in
  b000839 before a reference to the 11th. Preserve this apparent date anomaly;
  do not silently correct it in future work without documented source evidence.
- Existing rights.json records automatic US/Japan admission under
  `gutenberg-us-jp-v2`. Rights and acquisition evidence were left unchanged.
  This job used saved evidence and did not freshly consult external webpages.

## Unresolved questions

- The photo-reprint's bibliographic identity and exact historical print exemplar
  remain unverified. The provider's 1818 description is not independent proof
  of transcription identity or completeness against a physical edition.
- Independent structural review remains outstanding, including the treatment
  of Walton's continuation as a sibling of Chapter VII. Mechanical coverage
  proves block preservation/order, not literary fidelity or human review.
- No literary-release approval or remote deployment is established by this job.
