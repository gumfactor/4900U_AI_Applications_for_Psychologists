# Prompt: Question Answering Over Selected Notes

Recommended model: `Gemini 2.5 Flash-Lite`

Use this prompt with a small set of notes.

```text
Answer the question using only the notes below.

Rules:
- If the notes do not contain enough information, say so explicitly.
- Distinguish direct support from inference.
- Quote note titles when referring to evidence.
- End with a short list of which notes were most important.

Question:
[PASTE QUESTION HERE]

Notes:
[PASTE 2 TO 5 NOTES HERE]
```
