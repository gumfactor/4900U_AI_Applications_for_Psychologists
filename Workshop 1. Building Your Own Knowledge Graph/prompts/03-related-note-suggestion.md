# Prompt: Related Note Suggestion

Recommended model: `Gemini 2.5 Flash-Lite`

Use this prompt with two to five notes at a time.

```text
You are helping connect notes in a personal knowledge base.

Using only the notes below:
- identify meaningful links between them
- label each link using only: related_to, supports, contradicts, applies_to, mentions
- explain each link in one sentence
- suggest at most 5 links total

Do not invent notes that are not provided.

Return format:
- Source note -> relationship -> target note: explanation

Notes:
[PASTE 2 TO 5 NOTES HERE]
```
