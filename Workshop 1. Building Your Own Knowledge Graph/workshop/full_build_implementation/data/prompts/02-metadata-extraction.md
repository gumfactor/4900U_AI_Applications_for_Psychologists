You are helping structure a note for a personal knowledge base.

Based only on the supplied text:
- choose a note kind only if it clearly fits one of these: synthesis, reflection, method-note, brainstorming
- suggest short topics
- suggest short tags
- list people mentioned
- list named sources or works mentioned
- list projects mentioned
- list source_refs only if explicit file paths or references are present

Return the result in YAML only with exactly these keys:
- note_kind
- topics
- people
- sources
- projects
- tags
- source_refs

Use `null` for `note_kind` if none clearly applies. Use lists for every other field. Do not invent file paths.
