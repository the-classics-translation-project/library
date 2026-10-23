# The Classics Translation Project

Enjoyable public-domain classics, translated or modernized for contemporary
readers. This is an informal, solo literary project with an evolving toolchain.

**The GitHub repository and Pages site are live. There is no approved
reader publication or actual translation yet.** See [STATUS.md](STATUS.md)
for the verified current state.

- [GitHub repository](https://github.com/the-classics-translation-project/library)
- [Reader catalogue and site](https://the-classics-translation-project.github.io/library/)
- [Admin catalogue and work queue](https://the-classics-translation-project.github.io/library/admin/)

## Start in an existing or new local checkout

Read [AGENTS.md](AGENTS.md), [STATUS.md](STATUS.md) and the
[maintainer workflow](docs/maintainer-workflow.md). Clone the current
repository rather than using an obsolete starter ZIP:

```sh
git clone https://github.com/the-classics-translation-project/library.git
cd library
./ctp validate
python3 -m unittest discover -s tests -v
node tests/review-core.cjs
node tests/annotation-core.cjs
./ctp build --demo --epub
```

Python 3.11+, Pandoc 3.x and Git are used for source/build tasks; Node 22+
is used for JavaScript checks. The demo is a synthetic UI fixture, not a
published classic. See [setup](docs/setup.md) for local inspection.

## How works move through the project

A public, token-free Admin page searches the full cached Gutenberg catalogue
and prepares a GitHub Issue. Authorized requests enter `queue.json`. An
existing GitHub Actions workflow performs deterministic US/Japan source-admission
checks, preserves passing Gutenberg packages in Git and records explicit
holds for uncertain ones.

The repository now includes a deterministic worker, a macOS LaunchAgent
installer and an Admin source-tree view. The worker is designed to poll cheaply
and invoke Codex only for actionable work: researching supported evidence
holds and producing canonical source trees from admitted Gutenberg bytes.
See the
[implementation brief](docs/local-source-automation.md) and
[agent prompt](prompts/source-preparation.md).

**A per-user LaunchAgent is installed for 30-minute source-work polls.** Its
first scheduled tick found no pending work and made no model call. Gutenberg
#36 (*The War of the Worlds*, Japanese target) and #41445 (*Frankenstein*,
English candidate) both have validated source trees in the repository. A bounded
live worker run published #41445. CI and Pages passed, and the live Admin
manifest serves both trees. The expandable tree still needs a real browser
interaction check.

A later milestone will let the owner check individual nodes in Admin, file
translation-request Issues and run separate fresh-context local translation
sessions. See [translation runner design](docs/translation-runner.md).

The ordered source tree has mechanically allocated, stable opaque IDs, optional
labels and body text on nodes, and arbitrary children; there is no mandatory
sentence/paragraph alignment. Edited/retranslated prose is tracked with
versioned prompts, notes, provenance records and immutable snapshots.
No GitHub Issue or mechanical quality check silently approves a literary
release. `catalog.json` is an explicit reader/review distribution allowlist.

## Repository map

```text
AGENTS.md      authoritative agent entry point
STATUS.md      what has actually been implemented, tested and deployed
docs/          workflow, rights, structures, implementation briefs
prompts/       reproducible model/task instructions
books/         admitted source packages, canonical trees, editions and notes
queue.json     authorized requests; progress derived from actual files
catalog.json   explicit reader/review distribution allowlist (currently empty)
data/          cached full Gutenberg metadata catalogue
tools/         deterministic validators, importers and site builder
site/          Admin, reader and annotation-workbench UI
tests/         mechanical/annotation/browser tests
revisions/     immutable frozen examples and future literary snapshots
.github/       CI, Pages, catalogue refresh, authorized Issue intake
```

[Editorial policy](docs/editorial-policy.md) ·
[Local source automation](docs/local-source-automation.md) ·
[Source import](docs/source-import.md) ·
[Source structure](docs/source-structure.md) ·
[Provenance](docs/provenance.md) ·
[Rights](RIGHTS.md)

No blanket license has been selected for code or new editorial material.
The repository is public, but that is not an authorization to distribute
new translations or to submit anything to KDP.

## Local translation through ChatGPT relay

Prepare a bounded ZIP with `./ctp relay-package`, then validate and save its returned
result with `./ctp relay-import`. The adapter supports Markdown glossaries and
captures exact submitted context in generation records. Packaging does not submit
or publish. See [relay usage](docs/chatgpt-relay.md) for the existing local relay,
commands, result contract and recovery. Offline tests cover this adapter; a live
translation trial remains outstanding.

## Translation requests and ZIP exchange

The [Admin page](https://the-classics-translation-project.github.io/library/admin/)
also supports selecting source nodes for translation and retranslation,
choosing a Git-versioned translation recipe and specifying whether to
include notes or an earlier frozen translation. The generated Issue is
registered only when submitted on GitHub by an authorized maintainer.

The repository's deterministic ZIP tools work with the owner's existing
ChatGPT ZIP relay; they do not make AI calls:

```sh
./ctp translation-pending
./ctp translation-export 123 --output build/translation-123.zip
./ctp translation-import build/return-123.zip
./ctp guide-export gutenberg-36 ja --output build/guide-ja.zip
./ctp guide-import build/guide-ja-return.zip
```

Replace `123` with an accepted translation Issue number. Translation
imports remain drafts, with revision history preserved and no publication.
For schemas and safety constraints, see
[translation ZIP workflow](docs/translation-zip-workflow.md).

### Whole-work translation guides

Admin also has a **Whole-work glossary and translation guide** request
control. Choose the work and target language, submit its GitHub Issue, then
process a ZIP via the existing local relay:

```sh
./ctp guide-pending
./ctp guide-export --issue 123 --output build/guide-123.zip
./ctp guide-import build/guide-123-return.zip
```

The guide prompt is ordinary Git-versioned Markdown at
`prompts/whole-work-guide.md`. Resulting work-wide references and
target-language terminology guidance are **organized Markdown, not a
structured term database**. The output ZIP has a strict outer schema
only so it can be imported safely. Earlier guide versions are preserved;
repeating a request does not publish text or invoke a model in the repo.
See [ZIP workflow](docs/translation-zip-workflow.md).
