# Prompts

`structure-source.md`, `translate.md`, `review.md` and `next-task.md` are starting
points for interactive agents. The earlier `translation-start.md` is retained as a
reference, not a separate policy. No prompt fixes a model or requires an API.

Git tracks reusable versions. `./ctp record-run` captures the exact visible prompt,
material session instructions, model label, source and editorial note context used
for a substantial translation/rewrite. See [provenance](../docs/provenance.md).

Do not silently replace a minimal literary policy with elaborate prompt rules.
Record work-specific discoveries in notes so they outlive a particular model.
Never store private transcripts or credentials by default.

## Selectable translation recipes

New language-independent or target-specific Markdown recipes belong under
`translation/`. The basename is the stable recipe ID, the first H1 is
the Admin dropdown label, and the supported placeholders are
`{{target_language}}`, `{{target_language_code}}`,
`{{source_language}}` and `{{work_title}}`. No expressions,
includes or arbitrary code are evaluated. A push to GitHub rebuilds Admin's
prompt selection. Existing accepted translation Issues retain the precise
prompt bytes at acceptance. See [translation ZIP workflow](../docs/translation-zip-workflow.md).
