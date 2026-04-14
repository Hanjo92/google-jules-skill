# Codex Prompt Strict Ops

## KR

```text
Use google-jules-control/SKILL.md as the operating contract for all Jules work.

Rules:
- Use google-jules-control/scripts/jules_api.py for Jules operations.
- Start with `python3 google-jules-control/scripts/jules_api.py doctor --compact`.
- Resolve owner/repo with `repo-to-source --repo owner/repo --compact` before creating sessions.
- Use `.env` with JULES_API_KEY as the default auth path.
- Prompts sent through `create-session`, `send-message`, `resume`, and `request-pr-rework` are strict-scope by default.
- If the task is ambiguous or appears to require out-of-scope work, ask a clarifying question instead of broadening the task.
- Use `--scope-note` and `--non-goal` when extra boundaries matter.
- Before merge-aware reporting or cleanup, run `gh-auth-check --compact`.
- Use `summary`, `cleanup-report --markdown`, `close-ready-report --markdown`, and `notify-close-plan --markdown` for user-facing updates.
- Do not close, cancel, or delete a Jules session without explicit user confirmation.
- Prefer concise summaries over raw JSON unless structured output is requested.

Sequence:
1. doctor
2. repo-to-source
3. create-session or reporting command
4. summary
5. cleanup only after confirmation
```

## EN

```text
Use google-jules-control/SKILL.md as the operating contract for all Jules work.

Rules:
- Use google-jules-control/scripts/jules_api.py for Jules operations.
- Start with `python3 google-jules-control/scripts/jules_api.py doctor --compact`.
- Resolve owner/repo with `repo-to-source --repo owner/repo --compact` before creating sessions.
- Use `.env` with JULES_API_KEY as the default auth path.
- Prompts sent through `create-session`, `send-message`, `resume`, and `request-pr-rework` are strict-scope by default.
- If the task is ambiguous or appears to require out-of-scope work, ask a clarifying question instead of broadening the task.
- Use `--scope-note` and `--non-goal` when extra boundaries matter.
- Before merge-aware reporting or cleanup, run `gh-auth-check --compact`.
- Use `summary`, `cleanup-report --markdown`, `close-ready-report --markdown`, and `notify-close-plan --markdown` for user-facing updates.
- Do not close, cancel, or delete a Jules session without explicit user confirmation.
- Prefer concise summaries over raw JSON unless structured output is requested.

Sequence:
1. doctor
2. repo-to-source
3. create-session or reporting command
4. summary
5. cleanup only after confirmation
```
