#!/usr/bin/env bash
# Explicit, opt-in bootstrap. No force push and no credentials in project files.
set -euo pipefail
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
repo='the-classics-translation-project/library'
if [[ "${1:-}" != '--publish' || "$#" != 1 ]]; then
  cat <<PLAN
Plan only; nothing has been changed.
  1. Restore the packaged local Git history, when necessary.
  2. Validate the project and require a clean main branch.
  3. Use your existing gh login to create public $repo if absent.
  4. Push main without force; refuse unrelated/non-ancestor remote history.
  5. Configure GitHub Pages (Actions), then request site and catalogue builds.
Run: ./tools/publish-github.sh --publish
Prerequisites: Git, Python 3.11+, GitHub CLI (gh), and gh auth login.
This creates a public repository and enables deterministic GitHub workflows.
It does not publish a book to KDP or run any model/API translation jobs.
PLAN
  exit 0
fi
for cmd in git python3 gh; do command -v "$cmd" >/dev/null || { echo "Missing: $cmd" >&2; exit 1; }; done
gh auth status >/dev/null
./ctp validate
if [[ ! -d .git ]]; then
  [[ ! -e .git && -f bootstrap.bundle ]] || { echo 'Clone the supplied bundle or run from the packaged library directory.' >&2; exit 1; }
  git init -b main
  git bundle verify bootstrap.bundle
  git fetch bootstrap.bundle main
  # Populate only the index; preserve all extracted working files and detect edits.
  git reset --mixed FETCH_HEAD
fi
[[ "$(git rev-parse --show-toplevel)" == "$PWD" ]] || { echo 'Wrong Git root.' >&2; exit 1; }
[[ "$(git branch --show-current)" == main ]] || { echo 'Switch to main after reviewing local branches.' >&2; exit 1; }
[[ -z "$(git status --porcelain)" ]] || { echo 'Local changes exist. Review and commit them before publishing.' >&2; exit 1; }
if ! gh repo view "$repo" --json nameWithOwner >/dev/null 2>&1; then
  # Failure (including an existing inaccessible repo) stops here; nothing is overwritten.
  gh repo create "$repo" --public --description 'Public-domain classics translated and modernized for contemporary readers'
fi
if git remote get-url origin >/dev/null 2>&1; then
  remote=$(git remote get-url origin)
  case "$remote" in
    "https://github.com/$repo"|"https://github.com/$repo.git"|"git@github.com:$repo.git") ;;
    *) echo "Unexpected origin: $remote. Refusing to change it." >&2; exit 1 ;;
  esac
else
  git remote add origin "https://github.com/$repo.git"
fi
# gh configures its normal authenticated Git helper. No token is copied here.
gh auth setup-git
if [[ -n "$(git ls-remote --heads origin main)" ]]; then
  git fetch origin main
  git merge-base --is-ancestor FETCH_HEAD HEAD || { echo 'Remote main is not an ancestor. Fetch/reconcile it manually; no force push was attempted.' >&2; exit 1; }
fi
git push --set-upstream origin main
# Do not silently replace an existing branch-based Pages configuration.
if type=$(gh api "repos/$repo/pages" --jq .build_type 2>/dev/null); then
  [[ "$type" == workflow ]] || { echo 'Existing Pages uses another build type. Review it before switching to Actions.' >&2; exit 1; }
else
  gh api --method POST "repos/$repo/pages" -f build_type=workflow >/dev/null
fi
gh variable set CTP_PAGES_ENABLED --repo "$repo" --body true
gh workflow run pages.yml --repo "$repo" --ref main
gh workflow run catalogue.yml --repo "$repo" --ref main
printf '\nPushed %s and requested builds. Inspect their actual outcomes:\n' "$repo"
printf '  gh run list --repo %s\n' "$repo"
printf 'Expected Pages address after a successful deployment: https://the-classics-translation-project.github.io/library/\n'
