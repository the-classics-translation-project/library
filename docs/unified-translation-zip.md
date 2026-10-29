# Unified translation return ZIP, version 2

New v2 Issue requests ask for this contract. A direct `relay-package` can opt
in with `--unified-return`. The same strict result reader serves both adapters;
earlier Issue `response.json` and direct `result.json` version 1 archives remain
importable for their original packages. This format has offline tests **and a live Issue-based ChatGPT return**:
Wells Japanese Issue #30 was imported as a draft on 2026-10-28, with the exact
v2 request/result hashes, translation receipt and run record recorded in
`translation-results/issue-30.json`. Its actual displayed model remains
`unknown`, and the result has not undergone human literary review. The direct
`--unified-return` variant remains unverified in a live ChatGPT job.

The ZIP contains `result.json` and exactly the files named by its `nodes` and
`auxiliary` entries. The JSON has exactly these fields:

```json
{
  "schema_version": 2,
  "kind": "translation",
  "adapter": "issue",
  "request_id": "123",
  "input_sha256": "<64 lowercase hex characters>",
  "status": "complete",
  "model_label": "unknown",
  "nodes": {
    "n0005": {
      "label": "text/n0005.label.md",
      "text": "text/n0005.md"
    }
  },
  "auxiliary": {}
}
```

For an Issue, `request_id` is its decimal number as text and `input_sha256`
is `input/manifest.json.job_sha256`. `auxiliary` is empty. For a direct ZIP,
`adapter` is `direct`, `request_id` is the exact attempt ID,
`input_sha256` is `manifest.json.job_sha256`, and `auxiliary` is exactly
`{"glossary":"glossary.md","notes":"notes.md"}`. The direct request manifest
is version 2 and hashes itself excluding its `job_sha256` field. Each requested
label uses one UTF-8 line; each prose field uses complete UTF-8 Markdown.

The importer checks the exact request identity, source/job hash, node and field
coverage, fixed safe filenames, member set, bounded sizes, UTF-8 and nonempty
contents before editing an edition. Automatic coordinator import records the
observed model as `unknown` unless independently visible; a model-written label
does not prove the Chat UI model. A valid ZIP is still an unreviewed draft.
The two existing storage paths and historical archives are preserved.
