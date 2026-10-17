# Setup and GitHub deployment

## Local environment

Python 3.11+, Git and Pandoc 3.x are required for normal work. Node 22+ runs the
JavaScript checks. There are no runtime pip packages; Playwright is an optional
development dependency for browser tests. Do not add a model API key for setup.

```sh
./ctp validate
python3 -m unittest discover -s tests -v
node tests/review-core.cjs
node tests/annotation-core.cjs
./ctp build --demo --epub
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
```

The packaged `dist/` is an opt-in example build for local inspection. Normal builds
and Pages exclude examples. Export local annotations rather than relying solely on
browser storage. Files are self-contained, but local/HTTPS serving is preferable.

## Recovering Git history

The source ZIP contains `library/bootstrap.bundle`. The publishing helper restores
it into a new `.git` without overwriting extracted working files, and refuses to
publish uncommitted differences. Alternatively clone the separately provided bundle:

```sh
git clone /path/to/classics-library-v0.1.bundle library
cd library
```

The bootstrap commit is attributed to a software-building agent, not falsely signed
as the owner. Configure your own Git identity before making subsequent commits.

## First GitHub publication

Install GitHub CLI and authenticate through its normal `gh auth login` flow using
an account authorized to create repositories/Pages in the organization. Do not paste
tokens into chat or project files. Review the [rights policy](../RIGHTS.md) and files
before publishing them. Then:

```sh
./tools/publish-github.sh
./tools/publish-github.sh --publish
```

The first command is a no-change plan. The second targets the fixed public repository
`the-classics-translation-project/library`, creates it if absent, restores/checks
local Git, pushes `main`, configures Actions-based Pages, sets the repository variable
`CTP_PAGES_ENABLED=true`, and requests Pages and catalogue builds. It refuses a different
origin, local changes, a non-main branch, unrelated remote history and a conflicting
Pages build type. It never force-pushes, deletes the remote, publishes KDP books or
calls a model API. Authentication, network, branch protection and organization policy
can stop it. A later failure may leave earlier successful setup steps in place;
inspect the reported state before retrying.

```sh
gh run list --repo the-classics-translation-project/library
```

Check actual workflow results. The expected successful site address is
`https://the-classics-translation-project.github.io/library/`; no deployment to that
address was performed during the local build. The GitHub connector in that session
was read-only and reported no accessible repositories under the organization.

## Included workflows

- **Validate and build**: read-only push/PR checks and an opt-in sample artifact.
- **Deploy catalogue and workbench**: manual/reusable Pages build of `catalog.json`.
- **Import work requests**: Issues opened/edited/reopened or manual run; rescans open
  requests, validates author/JSON and commits only the additive queue.
- **Refresh Gutenberg catalogue**: one official CSV fetch weekly or on manual request,
  then commits only the cached metadata.

Intake and catalogue refresh share a writer concurrency group and do not force-push
on a race with a person editing main. A failed push needs a fresh rerun/reconciliation.
Rejected requests are reported in workflow output; the initial implementation does
not post acknowledgement comments or close Issues automatically. Set
`CTP_PAGES_ENABLED=false` to stop their follow-up deployment without stopping intake.
A normal code push runs checks but does not automatically deploy Pages.

GitHub's repository-token pushes do not trigger another push workflow, so the two
state-writing workflows explicitly call the reusable Pages workflow when enabled.
See the official [workflow-trigger documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
and [Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
Repository/organization policies can require additional approval; none were modified
from the build session.

## Optional browser tests

Build examples, install Playwright and a local Chromium in your development
environment, then run `python3 tests/browser_v2.py`. The script defaults to
`/usr/bin/chromium`; adjust that local executable path if necessary. For environments
where navigation is administratively blocked, `--dom` explicitly tests a fresh
isolated DOM with simulated in-memory Storage. That mode cannot certify real storage,
URLs, network operations, Safari/iPad selection or remote GitHub submission. No test
submits an Issue or calls a model.
