# The Classics Translation Project

Enjoyable public-domain classics, translated or modernized for contemporary readers.
A solo, informal literary project with an evolving software toolkit.

**Version 0.1.0 is a runnable local repository, not a live deployment.** The initial
GitHub upload and Pages deployment have not been performed. There is no published
literary edition yet. See [STATUS.md](STATUS.md) for precisely what was tested.

## Start locally

Install Python 3.11+, Pandoc 3.x and Git. Node 22+ is used for JavaScript tests.
There are no runtime Python packages, frontend framework, paid API calls or secrets.

```sh
./ctp validate
python3 -m unittest discover -s tests -v
node tests/review-core.cjs
node tests/annotation-core.cjs
./ctp build --demo --epub
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Open `http://localhost:8000/`. The **Workbench** includes a small English/Japanese
synthetic example with nested and unlabeled sections. It is a software fixture,
not a published classic. The **Admin** page includes a three-record metadata seed
and a Gutenberg-number fallback; the full catalogue still needs downloading.
The **Library** lists only approved reader editions, and is initially empty.

`./ctp build --epub` excludes examples. The build output is `dist/`, not Git-tracked
publication evidence. Each reading/review HTML is self-contained; serve the site
on localhost or HTTPS for sustained reviewing. Export notes for backup.

## How the project works

One source package is one work. Its ordered tree has opaque, mechanically assigned
IDs and optional labels, prose and children. Translate labels as well as prose;
keep the larger structure, not its sentence or paragraph boundaries. Whole new
translations are ordinary revisions. Read the deliberately short
[editorial policy](docs/editorial-policy.md).

The contributor page is a reader with optional annotations: select text, comment
in a nearby popup, then see a compact margin note. Titles and headings can be
annotated too. Reports cite an immutable revision and exact text, and may contain
observations from several sections. They are observations, not automatic patches.

The administrator selects a Gutenberg record and target languages, then submits
a prefilled GitHub Issue. Authorized requests are merged into `queue.json` by the
intake workflow. The queue records intentions; source and translation files record
progress. `./ctp task` prepares the next bounded task for an interactive agent.
There is no unattended model runner, subscription automation or paid API dependency.

Prompts are ordinary version-controlled Markdown. Substantial generation records
capture the model label, prompt text, source fingerprint, notes and output hashes.
Work-specific and edition-specific notes outlive individual translation attempts.

## Publish the repository

The downloadable ZIP includes `bootstrap.bundle`, which preserves the local Git
history. With GitHub CLI installed and authenticated as an authorized owner:

```sh
./tools/publish-github.sh           # print the plan; change nothing
./tools/publish-github.sh --publish # explicitly create/push/configure the public project
```

The script targets `the-classics-translation-project/library`, refuses unrelated
remote history, never force-pushes, and requests Pages/catalogue workflows. It does
not assert they succeeded. Initial deployment requires GitHub write/admin access;
that access was unavailable in the build session. See [setup](docs/setup.md).

## Repository map

```text
books/        acquired source packages, canonical trees, notes, editable editions
revisions/    immutable source/translation snapshots, including captured rendering
prompts/      reusable prompts; generation records pin their exact contents
catalog.json explicit distribution allowlist, separate review and reader audiences
queue.json   requested works/target languages and accepted Issue evidence
data/        cached catalogue metadata (currently only three seed records)
site/        reader, contributor and administrator interfaces
tools/       import, validation, snapshot, build, intake and publish commands
tests/       source, provenance, annotation, build and browser checks
examples/    opt-in synthetic fixtures; preserved legacy v1 example
reviews/     optional maintainer dispositions linked to reports and revisions
templates/   schema-v2 metadata and editorial note starting points
docs/        operating guidance, decisions, data contracts and rights checkpoints
.github/    validation, Pages, catalogue refresh and authorized Issue intake
```

## Documentation

[Agent instructions](AGENTS.md) · [Contributor guide](CONTRIBUTING.md) ·
[Source import](docs/source-import.md) · [Source structure](docs/source-structure.md) ·
[Maintainer workflow](docs/maintainer-workflow.md) · [Provenance](docs/provenance.md) ·
[Data formats](docs/data-formats.md) · [Architecture](docs/architecture.md) ·
[Decisions](docs/decisions.md) · [Rights](RIGHTS.md)

No blanket license has been selected for code or new editorial material. Public
repository visibility is not a licensing decision. No KDP upload is implemented.
