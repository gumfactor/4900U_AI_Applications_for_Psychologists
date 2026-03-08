# Workshop Workflow

## Build Sequence

1. Add or create a small source in `sources/`.
2. Copy a note template into `notes/`.
3. Fill the required frontmatter.
4. Use one AI prompt on a bounded input.
5. Paste the draft output into the note.
6. Review and edit the note manually.
7. Update `status`, `updated`, and `human_reviewed`.
8. Log the AI interaction in `logs/`.
9. Commit a meaningful milestone.

## Human Review Rule

AI may draft a summary, tags, or related links. Humans decide:

- what is true enough to keep
- which links are meaningful
- whether the note is ready to mark as `reviewed` or `final`

## Minimal Git Routine

Suggested command sequence:

```powershell
git init
git add .
git commit -m "Initial scaffold"
```

After students add notes:

```powershell
git add .
git commit -m "Add first notes from source material"
```

After AI enrichment and review:

```powershell
git add .
git commit -m "Add AI-assisted enrichment"
git add .
git commit -m "Review notes and finalize links"
```

If Git is not configured on a student machine, the note workflow should still continue. Versioning can be demonstrated by the instructor or deferred until setup is complete.
