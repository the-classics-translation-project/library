# Setup and GitHub deployment

## Current repository

The canonical public repository is
https://github.com/the-classics-translation-project/library.
The website is deployed at
https://the-classics-translation-project.github.io/library/.
Read [STATUS.md](../STATUS.md) for the actual current deployment, acquired
Gutenberg sources and outstanding work; the early bootstrap-ZIP documentation
is not the setup path for a new local working copy.

Clone the canonical repository on the Mac that will run local agents:

```sh
git clone https://github.com/the-classics-translation-project/library.git
cd library
./ctp validate
python3 -m unittest discover -s tests -v
node tests/review-core.cjs
node tests/annotation-core.cjs
./ctp build --demo --epub
```

Python 3.11+, Git and Pandoc 3.x support the normal Python/build commands.
Node 22+ supports JavaScript checks. No pip runtime dependencies or paid
model API keys are required for the repository. For browser inspection, serve
`dist/` over localhost and test relevant interactions in a real browser.
Fixtures built with `--demo` are not reader publications.

## Existing GitHub workflows (already operational)

- **Validate and build** runs on pushes/PRs.
- **Deploy catalogue and workbench** publishes GitHub Pages from the
  explicit `catalog.json` allowlist plus the public Admin interface.
- **Import work requests** accepts correctly structured, maintainer-authored
  GitHub Issues into `queue.json` and runs the deterministic US/Japan rights
  admission/acquisition fast path. A policy/evidence change can trigger
  reassessment. Holds are recorded with reasons; valid admitted packages
  are committed with original bytes and metadata.
- **Refresh Gutenberg catalogue** refreshes official metadata weekly.

No GitHub Actions job currently invokes Codex. GitHub Pages is public;
Admin is not an authentication boundary. Inspect actual workflow runs
before claiming a deployment or successful source import.

## Planned local macOS source-preparation automation

**Read [docs/local-source-automation.md](local-source-automation.md) before
implementation.** That brief specifies the command contract, work selection,
lock, retry ledger, isolated Git worktree, Codex CLI execution, rights-hold
research, source structuring, Git publishing and expandable Admin source tree.

The local agent should implement a per-user `launchd` LaunchAgent template
with `RunAtLoad` and an initial `StartInterval` of 1800 seconds (30 minutes).
Installation is an explicit, once-per-Mac owner action; merely cloning or
building this repository must not enable automatic model invocations. Add
tested install, disable, uninstall, dry-run and log-viewing commands.

Before enabling it, authenticate `gh` and `codex` as the intended owner, verify
CLI-supported flags and a **bounded live smoke test** using the local user
account. `codex exec --ephemeral --sandbox workspace-write` is the documented
starting point, not a promise that the installed binary/auth/network policy
will work without testing. Do not embed tokens in source, plists or logs.
Never use `--yolo` / sandbox bypass just to make unattended execution pass.

Source-preparation scheduling is separate from
[the proposed translation launcher](translation-runner.md).
The initial milestone must **not** run unattended literary translation,
modify `catalog.json` or publish an edition.

## First real acceptance exercise

The repository already contains original, admitted Gutenberg #36 and #41445
source packages with reversible blocks and rights evidence. Neither has a
canonical literary source tree yet. The local worker should identify them as
pending without duplicating target-language rows, structure one with the
reference-only plan, validate, safely push and confirm the Admin page shows
its expandable labels and nodes after an actual successful Pages deployment.

If a Mac is asleep/offline the GitHub queue remains durable; the next
successful local poll must catch up without duplicate model jobs or overwriting
prior source history.

### References

- [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Codex CLI flags](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
- [Apple: launch agents](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [Apple: scheduled jobs](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html)
