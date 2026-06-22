# Google Antigravity Prompt

## KR

아래 프롬프트는 Google Antigravity에서 이 저장소를 Jules 운영 가이드로 사용할 때 바로 붙여 넣을 수 있는 시작 프롬프트입니다.

```text
Read google-jules-control/SKILL.md first and treat it as the operating guide for Google Jules control.

Use the bundled script at google-jules-control/scripts/jules_api.py for Jules session management, reporting, and cleanup.

Operational rules:
- Start with `python3 google-jules-control/scripts/jules_api.py doctor --compact`.
- Resolve owner/repo with `repo-to-source --repo owner/repo --compact` before creating a session.
- Use `.env` with JULES_API_KEY as the default auth path.
- Prompts sent through `create-session`, `send-message`, `resume`, and `request-pr-rework` are wrapped with a strict-scope contract by default.
- If the task is ambiguous or appears to require out-of-scope work, ask a clarifying question instead of broadening the task.
- Use `--scope-note` and `--non-goal` when you need extra task boundaries.
- Before approving a Jules plan, compare it against the original task, scope notes, non-goals, and strict-scope rules; do not approve scope drift by default.
- Prefer `summary`, `cleanup-report --markdown`, and `close-ready-report --markdown` for human-readable updates.
- Use `notify-close-plan --markdown` when preparing a user confirmation message before closure.
- Require explicit user confirmation before running `close-merged-session` or any delete-style command.
- Check `gh-auth-check --compact` before merge-aware reporting or cleanup.
- Keep user-facing updates short and operationally clear.

Suggested operating sequence:
1. doctor
2. repo-to-source
3. create-session or reporting command
4. summary
5. merge-aware cleanup only after confirmation
```

## EN

Use the prompt below as a ready-to-paste starter prompt for Google Antigravity.

```text
Read google-jules-control/SKILL.md first and treat it as the operating guide for Google Jules control.

Use the bundled script at google-jules-control/scripts/jules_api.py for Jules session management, reporting, and cleanup.

Operational rules:
- Start with `python3 google-jules-control/scripts/jules_api.py doctor --compact`.
- Resolve owner/repo with `repo-to-source --repo owner/repo --compact` before creating a session.
- Use `.env` with JULES_API_KEY as the default auth path.
- Prompts sent through `create-session`, `send-message`, `resume`, and `request-pr-rework` are wrapped with a strict-scope contract by default.
- If the task is ambiguous or appears to require out-of-scope work, ask a clarifying question instead of broadening the task.
- Use `--scope-note` and `--non-goal` when you need extra task boundaries.
- Before approving a Jules plan, compare it against the original task, scope notes, non-goals, and strict-scope rules; do not approve scope drift by default.
- Prefer `summary`, `cleanup-report --markdown`, and `close-ready-report --markdown` for human-readable updates.
- Use `notify-close-plan --markdown` when preparing a user confirmation message before closure.
- Require explicit user confirmation before running `close-merged-session` or any delete-style command.
- Check `gh-auth-check --compact` before merge-aware reporting or cleanup.
- Keep user-facing updates short and operationally clear.

Suggested operating sequence:
1. doctor
2. repo-to-source
3. create-session or reporting command
4. summary
5. merge-aware cleanup only after confirmation
```
