# Platform Guides

## KR

이 폴더는 `google-jules-control` 스킬과 운영 흐름을 다른 에이전트 플랫폼으로 옮겨 쓸 때 참고하는 문서 모음입니다.

대상 플랫폼:

- `Platform/Codex.md`
- `Platform/Codex-Prompt.md`
- `Platform/Codex-Prompt-Minimal.md`
- `Platform/Codex-Prompt-Strict-Ops.md`
- `Platform/Claude-Code.md`
- `Platform/Claude-Code-Prompt-Minimal.md`
- `Platform/Claude-Code-Prompt-Strict-Ops.md`
- `Platform/Google-Antigravity.md`
- `Platform/Google-Antigravity-Prompt-Minimal.md`
- `Platform/Google-Antigravity-Prompt-Strict-Ops.md`
- `Platform/Migration-Guide.md`
- `Platform/Claude-Code-Prompt.md`
- `Platform/Google-Antigravity-Prompt.md`

이 문서들의 목적:

- 현재 저장소의 운영 개념을 플랫폼별 용어로 바꾸기
- 프롬프트, 도구 호출, 인증, 작업 흐름 차이를 정리하기
- 동일한 Jules 제어 운영 절차를 다른 에이전트에서도 재현하기

공통 setup checks:

- 스킬 등록 또는 프로젝트 문서 주입 경로가 명확한지 확인
- `.env`의 `JULES_API_KEY`를 해당 플랫폼의 실행 컨텍스트에서 읽을 수 있는지 `doctor --compact`로 확인. 통과 기준은 `dotenv=yes api_key=yes api_ready=yes`
- `repo-to-source --repo owner/repo --compact` 결과를 다음 명령에 넘길 수 있는지 확인
- long-running 작업은 `wait` 또는 반복 `summary`로 갱신 상태를 보여줄 수 있는지 확인
- 사람 검토용 출력은 `--markdown`, 자동화용 출력은 JSON 또는 `export --output`으로 처리할 수 있는지 확인

완료 기준:

- 플랫폼 가이드만 보고 `doctor`, `repo-to-source`, `create-session`, `summary` 순서를 재현할 수 있음
- `.env`나 JSON 원문을 사용자에게 노출하지 않고 필요한 상태만 요약할 수 있음
- 삭제, close, cancel 같은 destructive action 전에 사용자 확인을 요구함

## EN

This folder contains platform adaptation guides for using the `google-jules-control` workflow beyond Codex.

Target platforms:

- `Platform/Codex.md`
- `Platform/Codex-Prompt.md`
- `Platform/Codex-Prompt-Minimal.md`
- `Platform/Codex-Prompt-Strict-Ops.md`
- `Platform/Claude-Code.md`
- `Platform/Claude-Code-Prompt-Minimal.md`
- `Platform/Claude-Code-Prompt-Strict-Ops.md`
- `Platform/Google-Antigravity.md`
- `Platform/Google-Antigravity-Prompt-Minimal.md`
- `Platform/Google-Antigravity-Prompt-Strict-Ops.md`
- `Platform/Migration-Guide.md`
- `Platform/Claude-Code-Prompt.md`
- `Platform/Google-Antigravity-Prompt.md`

Goals:

- Translate this repository's operating model into platform-specific terms
- Clarify prompt, tool, auth, and workflow differences
- Preserve the same Jules control workflow across multiple agent environments

Shared setup checks:

- Confirm the skill registration or project-document injection path is explicit
- Confirm the platform execution context can read `JULES_API_KEY` from `.env` with `doctor --compact`; pass only when it includes `dotenv=yes api_key=yes api_ready=yes`
- Confirm `repo-to-source --repo owner/repo --compact` output can be handed to the next command
- Confirm long-running work can be monitored with `wait` or repeated `summary`
- Confirm human review uses `--markdown`, while automation uses JSON or `export --output`

Done criteria:

- A user can reproduce the `doctor`, `repo-to-source`, `create-session`, `summary` sequence from the platform guide alone
- The platform can summarize status without exposing `.env` contents or dumping raw JSON by default
- Destructive actions such as delete, close, or cancel require user confirmation first
