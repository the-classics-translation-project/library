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

The next development milestone is **local automatic source preparation**.
The repository now includes a deterministic worker, a macOS LaunchAgent
installer and an Admin source-tree view. The worker is designed to poll cheaply
and invoke Codex only for actionable work: researching supported evidence
holds and producing canonical source trees from admitted Gutenberg bytes.
See the
[implementation brief](docs/local-source-automation.md) and
[agent prompt](prompts/source-preparation.md).

**The LaunchAgent has not been installed, and the full worker publishing path
has not run live.** Gutenberg #36 (*The War of the Worlds*, Japanese target)
has a validated source tree in the repository. Gutenberg #41445
(*Frankenstein*, English candidate) is acquired but unstructured. A live Admin
deployment and browser interaction check for #36 remain to be confirmed.

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
