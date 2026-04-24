# Claude Code Prompt

## KR

아래 프롬프트는 Claude Code에서 이 저장소를 Jules 제어 운영 문서로 사용할 때 바로 붙여 넣을 수 있는 시작 프롬프트입니다.

```text
Use the local project guide at google-jules-control/SKILL.md as the operating contract for Jules work.

When working with Google Jules:
- Prefer the bundled script at google-jules-control/scripts/jules_api.py for all Jules operations.
- Start with `python3 google-jules-control/scripts/jules_api.py doctor --compact`.
- If the user gives only owner/repo, resolve it with `repo-to-source --repo owner/repo --compact`.
- Prefer `.env`-based auth with JULES_API_KEY and do not ask to edit shell profile files unless necessary.
- Prompts sent through `create-session`, `send-message`, `resume`, and `request-pr-rework` are wrapped with a strict-scope contract by default.
- If the task is ambiguous or appears to require out-of-scope work, ask a clarifying question instead of broadening the task.
- Use `--scope-note` and `--non-goal` when you need extra task boundaries.
- Before approving a Jules plan, compare it against the original task, scope notes, non-goals, and strict-scope rules; do not approve scope drift by default.
- Use `summary`, `cleanup-report`, `close-ready-report`, and `notify-close-plan --markdown` to keep users informed.
- Never close, cancel, or delete a Jules session without explicit user confirmation.
- Before merge-aware cleanup actions, verify GitHub auth with `gh-auth-check --compact`.
- Summarize long JSON outputs into concise user-facing updates.

If the task is a first-time setup or verification flow, use this order:
1. doctor
2. repo-to-source
3. list-sources or create-session
4. summary
5. cleanup or reporting commands if needed
```

## EN

Use the prompt below as a ready-to-paste starter prompt for Claude Code.

```text
Use the local project guide at google-jules-control/SKILL.md as the operating contract for Jules work.

When working with Google Jules:
- Prefer the bundled script at google-jules-control/scripts/jules_api.py for all Jules operations.
- Start with `python3 google-jules-control/scripts/jules_api.py doctor --compact`.
- If the user gives only owner/repo, resolve it with `repo-to-source --repo owner/repo --compact`.
- Prefer `.env`-based auth with JULES_API_KEY and do not ask to edit shell profile files unless necessary.
- Prompts sent through `create-session`, `send-message`, `resume`, and `request-pr-rework` are wrapped with a strict-scope contract by default.
- If the task is ambiguous or appears to require out-of-scope work, ask a clarifying question instead of broadening the task.
- Use `--scope-note` and `--non-goal` when you need extra task boundaries.
- Before approving a Jules plan, compare it against the original task, scope notes, non-goals, and strict-scope rules; do not approve scope drift by default.
- Use `summary`, `cleanup-report`, `close-ready-report`, and `notify-close-plan --markdown` to keep users informed.
- Never close, cancel, or delete a Jules session without explicit user confirmation.
- Before merge-aware cleanup actions, verify GitHub auth with `gh-auth-check --compact`.
- Summarize long JSON outputs into concise user-facing updates.

If the task is a first-time setup or verification flow, use this order:
1. doctor
2. repo-to-source
3. list-sources or create-session
4. summary
5. cleanup or reporting commands if needed
```
