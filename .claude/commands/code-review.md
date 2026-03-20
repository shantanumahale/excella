---
description: Review recent code changes for quality, security, and maintainability
---

Use the **code-reviewer** agent to review all recent code changes.

## Instructions

1. Run `git diff --staged` and `git diff` to gather changes
2. If reviewing Python files, also invoke **python-reviewer** agent
3. Apply the review checklist from CRITICAL to LOW severity
4. Only report findings with >80% confidence
5. Consolidate similar issues
6. End with a summary table and verdict (APPROVE / WARNING / BLOCK)
