# Source acquisition and AI-assisted structuring

The first importer supports UTF-8 TXT/Markdown. HTML/PDF/image acquisition needs an
explicit conversion preserving the received original; there is no general-purpose
OCR, illustration or complex-layout importer in v0.1.

## Acquisition

```sh
./ctp source-fetch 41445
# Or, for bytes acquired through another documented route:
./ctp source-prepare /path/to/received.txt books/gutenberg-41445
```

`source-fetch` requests one official UTF-8 Gutenberg text URL. It fails explicitly
on network/provider errors and does not fall back to a differently identified
edition. It records URL, retrieval time and byte hash and leaves edition/rights
verification false. A metadata search result alone is not an imported source.
Direct Gutenberg network downloads were unavailable in the initial build session.

The acquisition directory retains `acquired.txt`, `normalized.txt` and `blocks.json`.
The only normalization is UTF-8 BOM removal and newline normalization. Blocks retain
all normalized text, including boilerplate and whitespace; exact raw bytes are kept
separately. The reported `blocks_sha256` binds a proposed plan to that source.

Before public commits, check the source edition and rights in the intended
territories. Distinguish old prose from later editorial additions. Record provenance
in `work.json`, and substantive source observations in `notes.md`. Do not silently
import material merely because its title appears in the catalogue.

## Automatic acquisition from the queue

The intake workflow runs `./ctp acquire-queued` after accepting requests. It also
processes existing queue candidates on manual dispatch. No AI/model call is made.
Each missing UTF-8 source is downloaded and prepared independently. A failure does
not discard other successful downloads; the workflow preserves successes and then
fails visibly with a report. Rerun the intake workflow to retry.

Downloaded `books/<id>/acquisition/` packages and `report.json` are retained in a
GitHub Actions artifact for 90 days (subject to repository retention settings).
Only `books/<id>/acquisition-receipt.json` is committed to Git. It records the URL,
retrieval time, source hash, artifact location and an estimated retention deadline.
This adds the acquired source to project tracking without automatically committing
unverified source prose to the public repository. Artifacts require GitHub access;
they are not a private archive and must not contain credentials. They are temporary
storage, not a permanent source archive or source-rights approval.

The queue distinguishes acquisition awaiting verification from sources not yet
acquired. `./ctp task` includes the artifact link. Download the artifact and unpack
its `books/` directory into the checkout, then validate the preserved bytes:

```sh
python3 -c 'import sys; sys.path.insert(0,"tools"); from pathlib import Path; from source_import import validate_blocks; validate_blocks(Path("books/gutenberg-36/acquisition"))'
```

Compare `raw_sha256` in `blocks.json` with the committed receipt as well. Complete
edition/rights checks before committing prose, record the evidence, and continue
with the block plan below. This automation does not create a literary tree,
`work.json`, translated text, or catalogue approval. Existing local acquisitions
are checked and never overwritten. A receipt with fewer than ten days remaining
is refreshed on the next intake run; deleted artifacts can be recovered by locally
removing their receipt before running `acquire-queued`, or by downloading explicitly
with `source-fetch` in a checkout without that acquisition. There is no scheduled
acquisition worker. Expired receipts are shown as needing acquisition again.

## AI proposes references; code copies text

Give the numbered blocks to an agent with `prompts/structure-source.md`. The plan
uses `label_blocks`, `text_blocks` and `children`. A reference is a block ID or an
inclusive two-ID range. It contains no retyped source prose or manually chosen IDs.

```json
{
  "blocks_sha256":"<hash reported by source-prepare>",
  "tree":{
    "label_blocks":["b000003"],
    "children":[{"label_blocks":["b000004"],"text_blocks":[["b000005","b000020"]]}]
  },
  "excluded":[{"blocks":[["b000001","b000002"]],"reason":"Provider wrapper, inspected separately"}]
}
```

This abbreviated example works only for a source with exactly those 20 blocks.
Every actual block must occur once in either the tree or an explicit exclusion.
Exclusion reasons are evidence to inspect, not proof that excluding the text is
editorially legitimate. Table-of-contents duplicates, illustration notices and
prefaces must be considered rather than silently discarded.

```sh
./ctp source-apply books/gutenberg-41445 build/structure-plan.json
```

The compiler validates ownership and order, assigns opaque node IDs and writes
`structure.json`, exact body files, the plan and a coverage audit. Branch prose is
read before descendants; use unlabeled children for interleaved prose. The command
will not overwrite a prior structure. Store ambiguous hierarchy decisions and the
exposed model/prompt used for analysis in an acquisition analysis note/record.
There is not yet a dedicated CLI for source-analysis generation records.

## Register metadata and validate

Create `work.json` using [the template](../templates/work/work.json), matching the
work directory's ID and recording the actual source/rights evidence. Create source
and edition notes. The agent may do this directly; the owner need not edit JSON.

```sh
./ctp validate
```

The validator proves mechanical block coverage, source preservation and tree/data
consistency. It does not prove that a chapter heading was correctly interpreted,
that a source edition was identified correctly, or that a translation is complete
in meaning. Independently inspect uncertain structure; do not relabel a mechanical
coverage check as human or literary review.
