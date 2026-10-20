Translation recipes in this directory are selectable in Admin. Each Markdown
file is one language-independent recipe. The title is its first H1 heading and
its filename is its stable ID. Supported placeholders are:

- {{target_language}}
- {{target_language_code}}
- {{source_language}}
- {{work_title}}

To create a target-specific recipe, simply write its instructions with an
explicit language and give it a different filename. Prompt edits trigger a
Pages rebuild; existing accepted requests retain a pinned copy of their prompt.
