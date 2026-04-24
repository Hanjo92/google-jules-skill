# Google Antigravity Prompt Strict Ops

## KR

```text
Read google-jules-control/SKILL.md first and treat it as the operating guide for Google Jules control.

Rules:
- Use google-jules-control/scripts/jules_api.py for Jules session management, reporting, and cleanup.
- Start with `python3 google-jules-control/scripts/jules_api.py doctor --compact`.
- Resolve owner/repo with `repo-to-source --repo owner/repo --compact` before session creation.
- Use `.env` with JULES_API_KEY as the default auth path.
- Prompts sent through `create-session`, `send-message`, `resume`, and `request-pr-rework` are strict-scope by default.
- If the task is ambiguous or appears to require out-of-scope work, ask a clarifying question instead of broadening the task.
- Use `--scope-note` and `--non-goal` when extra boundaries matter.
- Before approving a Jules plan, compare it against the original task, scope notes, non-goals, and strict-scope rules; do not approve scope drift by default.
- Prefer `summary`, `cleanup-report --markdown`, `close-ready-report --markdown`, and `notify-close-plan --markdown` for human review.
- Run `gh-auth-check --compact` before merge-aware reporting or cleanup.
- Require explicit user confirmation before any delete-style command or `close-merged-session`.
- Keep responses operationally concise and avoid dumping raw JSON unless requested.

Sequence:
1. doctor
2. repo-to-source
3. create-session or reporting command
4. summary
5. cleanup only after confirmation
```

## EN

```text
Read google-jules-control/SKILL.md first and treat it as the operating guide for Google Jules control.

Rules:
- Use google-jules-control/scripts/jules_api.py for Jules session management, reporting, and cleanup.
- Start with `python3 google-jules-control/scripts/jules_api.py doctor --compact`.
- Resolve owner/repo with `repo-to-source --repo owner/repo --compact` before session creation.
- Use `.env` with JULES_API_KEY as the default auth path.
- Prompts sent through `create-session`, `send-message`, `resume`, and `request-pr-rework` are strict-scope by default.
- If the task is ambiguous or appears to require out-of-scope work, ask a clarifying question instead of broadening the task.
- Use `--scope-note` and `--non-goal` when extra boundaries matter.
- Before approving a Jules plan, compare it against the original task, scope notes, non-goals, and strict-scope rules; do not approve scope drift by default.
- Prefer `summary`, `cleanup-report --markdown`, `close-ready-report --markdown`, and `notify-close-plan --markdown` for human review.
- Run `gh-auth-check --compact` before merge-aware reporting or cleanup.
- Require explicit user confirmation before any delete-style command or `close-merged-session`.
- Keep responses operationally concise and avoid dumping raw JSON unless requested.

Sequence:
1. doctor
2. repo-to-source
3. create-session or reporting command
4. summary
5. cleanup only after confirmation
```
