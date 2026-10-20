# Working data contracts

Metadata is UTF-8 JSON; prose and editorial notes are Markdown. Duplicate JSON keys
and non-finite numbers are rejected. The tools use standard-library parsers, not a
model-dependent runtime. The contracts below describe implemented v0.1 behavior.

## Project, catalogue and queue (schema 1)

`project.json` contains the project/repository name, configured maintainers, and
allowed target-language IDs/labels. `queue.json` contains source IDs, additive
requested targets and Issue number/author/body-hash evidence. Queue status is derived
from files. It does not store a subjective percentage of literary readiness.

`data/gutenberg-catalogue.json` distinguishes a small `seed` from a `full-csv` import,
with source and retrieval/hash information. The CSV parser expects Gutenberg's
Text#, Title, Authors and Language columns. A supplied local CSV is identified as
local, not falsely claimed to be a live download.

`catalog.json.revisions` records exact snapshot hashes, work/edition, audience
`review` or `readers`, `listed`, `approved_by` and `approval_note`. A reader entry
requires a complete, `ready` edition. **Every entry is built**, including an entry
with `listed:false`; that flag removes the directory listing, not public access to
its revision URL. To withhold a snapshot from Pages, omit its entry. Public Git
history can still expose committed material; see RIGHTS.md.

`examples/catalog.json` is an additional allowlist used only with `--demo`.

## Automatic source-rights record (schema 1)

`books/<id>/rights.json` records `rule_version`, work/Gutenberg identity,
`evaluated_on`, exact metadata URL/hash, extracted `evidence`, country calculations,
`eligible`, `status` (`acquired`/`held`), coded reasons and policy references.
`rights-metadata.rdf` preserves the received metadata when available. Parsing and
country decisions are replayed by validation; a changed hash or fabricated pass
fails validation. The evaluation date uses the earlier current date in Japan and
Hawaii, avoiding early admission at territory/date boundaries.

Acquired records bind `package_sha256` and the raw/blocks hashes to the exact
retained package. A held package that failed post-download checks records its hash
but does not retain its prose. `provenance.json` references `../rights.json` and
sets `rights_checked:true` for automatically admitted packages;
`source_edition_verified:false` remains separate. Neither flag is human review.

A held record includes concrete reasons and does not count as an imported work.
Queue progress exposes `rights_status` and `rights_reasons`; task discovery skips
held requests when selecting actionable work. A provider failure can leave no
usable RDF evidence; the saved record then explicitly has no extracted evidence.
For v2, an optional `books/<id>/admission-evidence.json` contains a cited
original-publication record and/or narrowly scoped Gutenberg production-credit
or photo-reprint-note decisions. The rights record pins its bytes by SHA-256.
Validation replays both the original v1 rules and v2 with exact evidence.
External bibliographic dates do not override conflicting Gutenberg statements;
exempted ancillary lines remain in exact acquired bytes.

See [automatic rights policy](automatic-source-rights.md).

## Source-tree view in Admin

The static Admin manifest is derived exclusively from the validated
`work.json` and `structure.json` of admitted, structured queued works, with
source IDs, opaque node IDs, optional labels, ordered children and accurate
status. It must not invent fixed chapters or expose unapproved translated
content. It is distinct from the `catalog.json` reader distribution allowlist.
See [local source-preparation brief](local-source-automation.md). Its source-tree
manifest uses existing source IDs and has no dependency on the reader catalogue.

## Source work and tree (schema 2)

`work.json`: `schema_version`, `id`, `language`, `author`, `source_edition`,
`source_provenance`, `rights_note`, `status` (`imported`/`reviewed`), `source` object,
and `structure:"structure.json"`. `fixture:true` identifies synthetic examples.
The source metadata is provenance, not a sales-product model.

The structure object contains recursively nested nodes with `id`, optional `label`,
`text`, `children`, and importer-produced `source_refs`. IDs match `n[0-9]{4,}` and
are unique. Body paths are resolved inside their work, not as arbitrary URLs or
external files. The source tree has its own provenance/checks, not a semantic ID
naming scheme. See [source structure](source-structure.md).

## Editable edition (schema 2)

`edition.json` contains `id`, language/direction, kind (`translation`/`modernization`),
status (`draft`/`ready`), description, rights note, a `production` object and `nodes`:

```json
{"n0001":{"label":"Translated book title"},
 "n0002":{"label":"Translated heading","text":"text/n0002.md"}}
```

The actual file also contains `schema_version:2`. The node map cannot introduce
labels or bodies absent from the source. Drafts may omit fields. A nonempty body
file proves only that a field is present, not that all meaning has been translated.
`author_credit` can override bibliographic display credit and is annotatable.

`production.runs` references files in `runs/`. Run schema 1 stores captured prompt/
notes, hashes, model/interface, scope through output paths and source fingerprint.
See [provenance](provenance.md). These are records, not job schedules.

## Frozen edition (schema 2; old schema 1 preserved)

`revisions/<work>/<edition>/<full-sha256>.json` stores work/edition metadata, the
source tree, source and target node fields, missing-field inventory, provenance
records, renderer information and Git context. Its identifier hashes canonical JSON.
Body fields contain Markdown, its hash, rendered safe HTML and exact plain text.
Labels are independent fields. Do not regenerate old snapshot rendering in place.

v1 flat-section snapshots and reports are read by the retained legacy module. New
source trees use v2; compatibility does not manufacture a migration history.

## Annotation report (schema 2)

A report identifies repository, work, edition, revision, report ID and creation
time. Each annotation has its own ID, `node`, `field` (`label`, `text`, or root
`credit`), `comment`, scope, and optional anchor. A text anchor includes UTF-16 code
unit start/end, exact text, prefix and suffix. Bounds cannot split a surrogate pair.
A whole-field note uses `scope:"field"` and a null anchor.

Offsets refer to the frozen field's text, not Markdown bytes, whole-page DOM text,
or a future translation. Multiple overlapping notes and multi-section reports are
valid. A selection may span paragraphs within one field; crossing fields needs
separate notes or a whole-field observation. `./ctp check-review` verifies identity,
quotes and positions. It never applies the comment or judges its literary merits.

## Translation request and ZIP exchange (schema 1)

`translation-requests.json` is the immutable, maintainer-authorized Issue
queue. Each accepted entry preserves the exact versioned recipe text and
request body hash. The request contains work ID, target language, selected
source node IDs (a parent includes its entire subtree), exact source fingerprint,
prompt ID/sha256, translation scope (`all` or `missing`),
reference setting (`none`, `notes`, or `text` with a frozen revision),
and bounded optional instructions.

`translation-export` produces a README, `input/job.json` with exact source
fields and fully expanded prompt/context, and `input/manifest.json` with a
SHA-256 job identity and expected translated fields. The relay must return a
ZIP containing only `response.json` with the matching job hash, displayed
model label and exactly those translated node fields. The importer validates,
records a provenance run and creates an immutable edition snapshot. Each
`translation-results/issue-N.json` prevents conflicting re-imports.
Guide jobs similarly exchange one `response.json` and retain content-addressed
work-level and target-level Markdown guides under `reference/`.
See [translation ZIP workflow](translation-zip-workflow.md).
