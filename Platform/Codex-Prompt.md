# Codex Prompt

## KR

아래 프롬프트는 Codex에서 이 저장소를 Jules 운영 가이드로 사용할 때 바로 붙여 넣을 수 있는 시작 프롬프트입니다.

```text
Use google-jules-control/SKILL.md as the primary operating guide for Google Jules work in this repository.

When handling Jules-related tasks:
- Prefer the bundled script at google-jules-control/scripts/jules_api.py for all Jules API operations.
- Start with `python3 google-jules-control/scripts/jules_api.py doctor --compact`.
- If the user only gives owner/repo, resolve it with `repo-to-source --repo owner/repo --compact`.
- Use `.env` with JULES_API_KEY as the default auth path.
- Prompts sent through `create-session`, `send-message`, `resume`, and `request-pr-rework` are wrapped with a strict-scope contract by default.
- If the task is ambiguous or appears to require out-of-scope work, ask a clarifying question instead of broadening the task.
- Use `--scope-note` and `--non-goal` when you need extra task boundaries.
- Use `summary`, `cleanup-report --markdown`, `close-ready-report --markdown`, and `notify-close-plan --markdown` for user-facing updates.
- Before merge-aware cleanup, run `gh-auth-check --compact`.
- Never close, cancel, or delete a Jules session without explicit user confirmation.
- Prefer concise operational summaries over raw JSON unless the user asks for structured output.

Suggested operating sequence:
1. doctor
2. repo-to-source
3. create-session or reporting command
4. summary
5. cleanup only after confirmation
```

## EN

Use the prompt below as a ready-to-paste starter prompt for Codex.

```text
Use google-jules-control/SKILL.md as the primary operating guide for Google Jules work in this repository.

When handling Jules-related tasks:
- Prefer the bundled script at google-jules-control/scripts/jules_api.py for all Jules API operations.
- Start with `python3 google-jules-control/scripts/jules_api.py doctor --compact`.
- If the user only gives owner/repo, resolve it with `repo-to-source --repo owner/repo --compact`.
- Use `.env` with JULES_API_KEY as the default auth path.
- Prompts sent through `create-session`, `send-message`, `resume`, and `request-pr-rework` are wrapped with a strict-scope contract by default.
- If the task is ambiguous or appears to require out-of-scope work, ask a clarifying question instead of broadening the task.
- Use `--scope-note` and `--non-goal` when you need extra task boundaries.
- Use `summary`, `cleanup-report --markdown`, `close-ready-report --markdown`, and `notify-close-plan --markdown` for user-facing updates.
- Before merge-aware cleanup, run `gh-auth-check --compact`.
- Never close, cancel, or delete a Jules session without explicit user confirmation.
- Prefer concise operational summaries over raw JSON unless the user asks for structured output.

Suggested operating sequence:
1. doctor
2. repo-to-source
3. create-session or reporting command
4. summary
5. cleanup only after confirmation
```
