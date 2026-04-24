# Claude Code Prompt Strict Ops

## KR

```text
Use google-jules-control/SKILL.md as the project operating contract for Jules work.

Rules:
- Use google-jules-control/scripts/jules_api.py for all Jules operations.
- Start with `python3 google-jules-control/scripts/jules_api.py doctor --compact`.
- Resolve owner/repo with `repo-to-source --repo owner/repo --compact` when only a repo name is provided.
- Prefer `.env` auth with JULES_API_KEY.
- Prompts sent through `create-session`, `send-message`, `resume`, and `request-pr-rework` are strict-scope by default.
- If the task is ambiguous or appears to require out-of-scope work, ask a clarifying question instead of broadening the task.
- Use `--scope-note` and `--non-goal` when extra boundaries matter.
- Before approving a Jules plan, compare it against the original task, scope notes, non-goals, and strict-scope rules; do not approve scope drift by default.
- Use `summary`, `cleanup-report --markdown`, `close-ready-report --markdown`, and `notify-close-plan --markdown` for user-facing communication.
- Check `gh-auth-check --compact` before merge-aware cleanup.
- Never delete or close a Jules session without explicit user confirmation.
- Summarize long JSON outputs into concise operational messages.

Sequence:
1. doctor
2. repo-to-source
3. list-sources or create-session
4. summary
5. cleanup only after confirmation
```

## EN

```text
Use google-jules-control/SKILL.md as the project operating contract for Jules work.

Rules:
- Use google-jules-control/scripts/jules_api.py for all Jules operations.
- Start with `python3 google-jules-control/scripts/jules_api.py doctor --compact`.
- Resolve owner/repo with `repo-to-source --repo owner/repo --compact` when only a repo name is provided.
- Prefer `.env` auth with JULES_API_KEY.
- Prompts sent through `create-session`, `send-message`, `resume`, and `request-pr-rework` are strict-scope by default.
- If the task is ambiguous or appears to require out-of-scope work, ask a clarifying question instead of broadening the task.
- Use `--scope-note` and `--non-goal` when extra boundaries matter.
- Before approving a Jules plan, compare it against the original task, scope notes, non-goals, and strict-scope rules; do not approve scope drift by default.
- Use `summary`, `cleanup-report --markdown`, `close-ready-report --markdown`, and `notify-close-plan --markdown` for user-facing communication.
- Check `gh-auth-check --compact` before merge-aware cleanup.
- Never delete or close a Jules session without explicit user confirmation.
- Summarize long JSON outputs into concise operational messages.

Sequence:
1. doctor
2. repo-to-source
3. list-sources or create-session
4. summary
5. cleanup only after confirmation
```
