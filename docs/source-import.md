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

## Automatic US/Japan source admission

After accepting Issues, the intake workflow runs `./ctp acquire-queued`. It also
processes existing queue candidates on manual dispatch. This is deterministic
standard-library code: no model, paid API, agent invocation or per-book owner
confirmation is required. See [automatic rights policy](automatic-source-rights.md)
for the exact supported cases and evidence assumptions.

- **Both territories pass, and the package passes identity/contribution checks:**
  preserve and commit `books/<id>/acquisition/{acquired.txt,normalized.txt,blocks.json,provenance.json}`,
  `rights.json` and `rights-metadata.rdf`. Keep the complete Gutenberg package,
  including its license/credits; no literary content is stripped or regenerated.
- **Missing information, unsupported cases or unresolved contributions:** record
  the reasons in `books/<id>/rights.json` and retain received RDF evidence. Do not
  commit the source text or create a source tree. Admin displays the hold reasons;
  `./ctp task` lists them and chooses actionable work ahead of held requests.
- **Provider/download errors:** persist a hold with the error, continue other
  works, save successes and then fail the workflow visibly. Ordinary rights holds
  are expected outcomes, not workflow failures. Rerun intake to retry held works.

The workflow commits only the validated file allowlist from that run, not whole
work directories. Passing acquisitions are permanent Git files, not expiring
Actions artifacts. Unchanged holds produce no new commit. Existing acquisitions
are validated and never overwritten or silently redownloaded; an existing manual
acquisition without an automatic record is reported for inspection, not staged.
Original evidence and decisions remain in Git history when a held request is
reassessed. A source changed by the provider does not replace an admitted package.

For a local run:

```sh
./ctp acquire-queued
./ctp validate
# Review build/source-downloads/report.json and the exact files before committing.
./ctp stage-acquisitions
```

`rights.json` admits a particular original package under the project's US/Japan
policy. It is not human/legal review, worldwide clearance, confirmation of an
exact historical print edition, translation generation, or reader-release approval.
`source_edition_verified` stays false; automated rights assessment and byte/tree
integrity are separate facts. `work.json`, source-tree interpretation and literary
translation follow separately. `catalog.json` is never changed by acquisition.
The manual `source-fetch` command above remains a local acquisition tool and does
not grant automatic admission or authorize staging unassessed source text.

## Local source preparation (code available, not scheduled)

[docs/local-source-automation.md](local-source-automation.md) specifies the
per-user local worker. Its code calls Codex only for selected source work,
handles supported rights holds through research/cited evidence, and uses
`source-apply` for first-import literary trees. Existing Gutenberg acquisitions
are never re-downloaded or overwritten. The LaunchAgent is installed from a
dedicated checkout under Application Support; its first scheduled tick was idle.
#36 was structured through the executor and validator in an isolated worktree;
a bounded full worker run structured and published #41445. CI, Pages and ledger
reconciliation succeeded, and an idle poll made no model call.

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
