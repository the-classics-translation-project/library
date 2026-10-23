# Translation and whole-work guide ZIP exchange

**Status:** Repository-side deterministic implementation. This workflow does
**not** call a model or install a translation scheduler. The owner processes
exported ZIP files using their existing local ChatGPT relay, then imports
the returned ZIP. GitHub Pages/Issues do not execute arbitrary AI requests.

## Planned shared prompt/reference selection (not implemented)

The current Issue-based translation form selects **one translation recipe**
and a coarse previous-reference setting; the ZIP importer uses its existing
`response.json` protocol. A proposed replacement uses **two pools**:
all applicable materials (general, target language, work, work+target language)
and a **user-ordered Applied** list. Versioned instruction and reference
documents—including generated Markdown guides—would be freely added,
removed and reordered, with full assembled-input preview and a separate
protocol-owned final output contract.

The full proposal, including reconciliation with the currently different
`relay-package` / `relay-import` ZIP return contract, is in
[ordered translation materials](translation-materials-design.md).
These changes are **not yet implemented**; the commands and formats below
remain current.

## End-to-end workflow

1. Add or revise a Markdown translation recipe under
   `prompts/translation/<id>.md`. Its first H1 is the Admin title and the
   lowercase filename is its recipe ID. A push to `main` triggers the existing
   GitHub Pages build, which publishes the updated prompt catalogue.
2. In [Admin](https://the-classics-translation-project.github.io/library/admin/),
   expand the source tree, select one or more nodes, choose target language,
   prompt, scope (`all` including retranslations / `missing` only), and prior
   reference (`none`, `notes`, or exact `text` from a frozen revision). Optional
   instructions are bounded to 4,000 characters. Checking a parent includes
   its whole subtree (own fields plus descendants).
3. Click **Prepare translation Issue** and submit the prefilled form on GitHub.
   The existing Issue intake workflow accepts requests only from configured
   maintainers, pins the exact prompt text, and appends immutable evidence to
   `translation-requests.json`. The public Admin form is not authentication.
4. In a current local checkout, fetch `main` and run:

   ```sh
   ./ctp translation-pending
   ./ctp translation-export 123 --output build/translation-123.zip
   ```

   Replace `123` with the accepted Issue number. The ZIP contains a README,
   input/job.json, and input/manifest.json. It is suitable for handing to the
   existing local ZIP-to-ChatGPT relay. The package includes exact source fields,
   the expanded prompt, selected notes/guides, and optionally a frozen prior
   translation. No hidden conversation or separately billed API is required.
5. Have ChatGPT return a ZIP containing **only** `response.json`, following the
   README in the request ZIP. Its `job_sha256` must match the input manifest and
   its `translations` must supply exactly the requested node/field set.
6. Import locally, inspect the result, and commit as appropriate:

   ```sh
   ./ctp translation-import build/return-123.zip
   ./ctp validate
   git status --short
   ```

   Import creates/updates a draft edition, preserves a frozen snapshot of the
   preceding draft when present, captures the displayed model name and fully
   expanded instructions through `record-run`, freezes the resulting draft,
   and records an idempotent result under `translation-results/issue-123.json`.
   Reusing the same return ZIP is a no-op; different results for the same Issue
   are rejected. **Nothing is added to `catalog.json` automatically.**

## Prompt variables

Supported simple literal substitutions are:

| Placeholder | Example |
| --- | --- |
| `{{target_language}}` | Japanese |
| `{{target_language_code}}` | ja |
| `{{source_language}}` | en |
| `{{work_title}}` | The War of the Worlds |

Unknown or malformed template placeholders are errors. There is no arbitrary
expression evaluation, includes, or nested templating. A language-specific prompt
can simply contain fixed instructions and be saved as a separate recipe. The
request stores the prompt content hash, and accepted Issues also retain its
exact source text so later changes cannot silently alter a pending request.

## Request format

The Admin page emits a machine-readable payload following
`<!-- ctp:translation-request:v1 -->`:

```json
{
  "schema_version": 1,
  "work": "gutenberg-36",
  "target": "ja",
  "nodes": ["n0005"],
  "source_fingerprint": "<64-digit SHA-256>",
  "scope": "all",
  "prompt": {"id": "contemporary", "sha256": "<64-digit SHA-256>"},
  "reference": {"mode": "none", "revision": null},
  "instructions": ""
}
```

The request and the selected source tree must match exactly, including source
fingerprint. Accepted requests are immutable; correcting a request requires
a new Issue. `scope=all` allows an independent retranslation even if a field
already exists. `scope=missing` excludes already present fields. Reference
`mode=text` requires a real frozen same-source/same-language revision;
`mode=notes` supplies work, target and glossary guidance without old prose.
A single source node may have a label and body text, so both are tracked
independently. No forced sentence alignment is introduced.

## Whole-work translation guides / glossary

The guide text is deliberately **organized Markdown rather than a structured
terminology database**. The prompt in `prompts/whole-work-guide.md` suggests
readable sections for characters/names, recurring terms, style/voice, and open
questions. Tables, prose, bullet points and cited node IDs are all acceptable.
A term may have context-dependent alternatives, and provisional suggestions
must not be confused with adopted editorial decisions. The importer only
validates the outer ZIP/JSON envelope and that the two guide strings are
nonempty, bounded Markdown; it does not parse individual glossary entries.

### From Admin and an authorized GitHub Issue

1. Open [Admin](https://the-classics-translation-project.github.io/library/admin/),
   find a structured work, select the desired target language under
   **Whole-work glossary and translation guide**, and click
   **Prepare guide-generation Issue**. The UI shows whether a work-wide
   reference or target-language guide has already been saved. Generating
   again is permitted; old content-hashed versions remain in Git.
2. Submit the prepared GitHub Issue. The maintainer-authorized intake workflow
   strictly parses the `ctp:guide-request:v1` marker, pins the prompt text, and
   records the request under `guide-requests.json`. No model is invoked.
3. In a current checkout, fetch `main` and export the accepted request:

   ```sh
   ./ctp guide-pending
   ./ctp guide-export --issue 123 --output build/guide-123.zip
   ```

   Replace `123` with the accepted **guide Issue** number.
   This ZIP includes the entire structured source, existing notes, pinned
   instructions, a README and a job/manifest hash. Hand it to your existing
   ZIP-to-ChatGPT relay.
4. ChatGPT returns a ZIP containing **only** `response.json`. Its
   `work_guide` and `target_guide` values are ordinary Markdown strings.
   It must also include the matching integer `issue`, `job_sha256` and
   the actual visible `model_label` (or `unknown`).
   If a large work cannot be analyzed in full, disclose the limitation,
   rather than claiming a complete reference.
5. Import, inspect, validate and commit:

   ```sh
   ./ctp guide-import build/guide-123-return.zip
   ./ctp validate
   git status --short
   ```

   The importer stores both documents under their exact SHA-256 names,
   updates their `reference/current.json` pointers, retains a guide
   generation record with the model/source/job/response fingerprints, and
   writes an idempotent `guide-results/issue-123.json` receipt. Returning
   the same ZIP twice is harmless; conflicting output for an accepted
   Issue is rejected. No reader release or model invocation is implied.

The guide request payload after its strict GitHub Issue marker is:

```json
{
  "schema_version": 1,
  "work": "gutenberg-36",
  "target": "ja",
  "source_fingerprint": "<64-digit SHA-256>",
  "prompt_sha256": "<64-digit SHA-256>"
}
```

Only this request envelope is machine-readable. It pins the source and
instructions at acceptance. The Markdown guide contents remain deliberately
unconstrained by any per-term record schema.

### Manual ZIP preparation (no Issue needed)

The existing direct commands remain available:

```sh
./ctp guide-export gutenberg-36 ja --output build/guide-ja.zip
# Process the ZIP with your existing ChatGPT relay.
./ctp guide-import build/guide-ja-return.zip
./ctp validate
```

This mode also uses the Markdown prompt when present. It does not produce an
Issue receipt, but still retains content-hashed Markdown and a generation
record. Translate nodes later using `reference=notes` (or `reference=text`)
so the corresponding work and target guides are included. These guides are
editorial memory, not mechanically enforced one-to-one terminology.

## Admin history versus repository history

The Admin tree displays **coverage metadata** from the current editable
draft and offers a version viewer for snapshots explicitly approved in
`catalog.json`. This distinction matters: Git contains unfinished historical
drafts, but GitHub Pages must not expose unapproved literary text merely
because it exists in `revisions/`. Once a revision has explicit review/reader
approval, the Admin viewer can load its existing published snapshot on demand
and display any chosen node's historical text. Users may still request
retranslation of any source node regardless of coverage.

## Boundaries and verification

- Source packages must have passed recorded source admission and must have a
  validated canonical source tree.
- Issue content is parsed as strictly structured data and authorized by
  GitHub user login, never executed as shell commands.
- A return ZIP cannot contain unexpected entries, redirects, executable
  instructions or files outside the expected schema.
- Imports require exact job identity, complete requested field coverage,
  nonempty bounded text, real model attribution or `unknown`, and valid edition
  metadata. Test and commit from a clean worktree for safe rollback on failure.
- The ZIP importer **does not** merge arbitrary GitHub branches, auto-publish
  a draft, run a model, or claim literary quality or human review.
- The public site is static. Node-selection requests open GitHub's own Issue
  form; opening the form is not submitting it.
- A prior version is preserved as an immutable edition snapshot, not as a
  mutable second copy of the same source node. Public history viewing is
  restricted to explicitly approved snapshots.

See [provenance](provenance.md),
[source structure](source-structure.md),
[translation runner design](translation-runner.md) and
[quality/publication checkpoints](quality-and-publication.md).
