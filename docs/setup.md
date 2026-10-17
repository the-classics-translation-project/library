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

## Local macOS source-preparation automation (not installed)

**Read [docs/local-source-automation.md](local-source-automation.md) before
using the worker.** That brief specifies the command contract, work selection,
lock, retry ledger, isolated Git worktree, Codex CLI execution, rights-hold
research, source structuring, Git publishing and expandable Admin source tree.

The repository includes `tools/source_worker.py`, a scheduler-safe wrapper and
a per-user `launchd` helper. The template uses `RunAtLoad` and a 1800-second
interval. Installation is an explicit, once-per-Mac owner action; cloning or
building the repository does not enable model invocations.

```sh
./tools/run-source-worker.sh check --json
./tools/install-source-launch-agent.sh dry-run
./tools/install-source-launch-agent.sh status
# After a successful bounded real source run and inspection:
./tools/install-source-launch-agent.sh install
./tools/install-source-launch-agent.sh logs
./tools/install-source-launch-agent.sh uninstall
```

Run the installed job from a **clean local `main` checkout** with the canonical
HTTPS `origin`. The helper resolves paths for launchd. A running or unresolved
attempt is recorded outside Git in `~/Library/Application Support/CTP/source-worker/`;
inspect `status` and its run logs, then use
`./tools/run-source-worker.sh retry gutenberg-<id>` only when a deliberate retry
is justified. A held rights case is not retried merely because time passed.

Before enabling it, authenticate `gh` and `codex` as the intended owner, verify
CLI-supported flags and a **bounded live source run** using the local user
account. The older `/usr/local/bin/codex` (0.46.0) failed a read-only smoke test
with this account's configured model; the ChatGPT.app-bundled 0.162.0 CLI passed.
The worker prefers that bundled CLI, or an explicit `CTP_CODEX_BIN`, and requires
`--ephemeral`. Test access again after CLI/auth changes. Do not embed tokens in
source, plists or logs.
Never use `--yolo` / sandbox bypass just to make unattended execution pass.

Source-preparation scheduling is separate from
[the proposed translation launcher](translation-runner.md).
The initial milestone must **not** run unattended literary translation,
modify `catalog.json` or publish an edition.

## First real acceptance exercise — completed without scheduling

The repository contains original, admitted Gutenberg #36 and #41445 source
packages with reversible blocks and rights evidence. Both now have validated
reference-only source trees. A bounded worker run selected #41445, used Codex
once, validated and safely pushed its tree, and reconciled successful CI and
Pages deployment. A subsequent idle poll used no model. The live Admin data
serves both trees; their expand/collapse behavior still needs a real browser
interaction check. See [STATUS.md](../STATUS.md) for exact runs and limits.

If a Mac is asleep/offline the GitHub queue remains durable; the next
successful local poll must catch up without duplicate model jobs or overwriting
prior source history.

### References

- [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Codex CLI flags](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
- [Apple: launch agents](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [Apple: scheduled jobs](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html)
