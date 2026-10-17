# Source structure and node IDs — implemented schema v2

One acquired provider package is one work by default. Internal Book/Volume/Part
labels are content, not new product identities. The default complete edition is
one HTML/EPUB. Exceptional packaging can be considered when an actual book needs it.

`structure.json` is one ordered rooted tree. Each node has an ID and may have a
`label`, a `text` file path and `children`. None is mandatory except the ID. A node
can have both prose and descendants. There is no fixed chapter/volume taxonomy.
A defensive depth limit of 128 protects the implementation, not a literary rule.

```json
{"id":"n0001","label":"A book","children":[
  {"id":"n0002","label":"Part One","text":"source/n0002.md","children":[
    {"id":"n0003","children":[
      {"id":"n0004","label":"A heading","text":"source/n0004.md"}
    ]}
  ]}
]}
```

First-time import assigns IDs mechanically in traversal order. After assignment,
IDs are identities, **not positions**: do not renumber after inserting, moving or
retitling something. The v0.1 importer deliberately refuses to overwrite an existing
tree; correcting an established structure needs an explicit, not yet implemented,
migration that preserves IDs and historical snapshots. Do not rerun import and
pretend unchanged sequence numbers identify the same nodes.

`source_refs` records the source-block ownership of each generated label/body.
The importer checks exact coverage/order and keeps the original bytes. The label
field is copied from its original block (outer whitespace removed); it is not an
AI reconstruction. See [source import](source-import.md).

An edition's `nodes` map uses the same IDs and optional `label`/`text` fields. Every
existing source label/body needs a translation before the edition can be `ready`.
Missing fields are permitted in a draft. A missing source label is not a request to
invent one. The work title is simply the root label when present. Bibliographic
credits remain metadata and may have an edition-specific `author_credit`.

Reading order is a node's own prose followed by its children. When the source has
prose interleaved between child sections, use additional unlabeled child nodes at
those positions rather than reordering the prose. File paths need not mirror nesting.

Bodies may be rewritten completely; no stable sentence IDs or forced paragraph
alignment. The tree describes the work, not the AI's batch size. Translation and
checking may involve several nodes at once when context requires it.

HTML and EPUB navigation use translated labels. An unlabeled body may receive a
clearly navigational `Section …` entry without adding that heading to the prose.
Unlabeled grouping nodes do not create blank EPUB spine pages. The full source tree
remains in snapshots even when navigation simplifies a grouping's presentation.

Schema-v1 flat snapshots remain readable through `tools/legacy_v1.py`. Their hashes
and reports have not been rewritten to look like schema v2.
