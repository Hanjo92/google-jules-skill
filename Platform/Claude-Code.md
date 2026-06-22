# Claude Code

## KR

### 전환 개념

Claude Code에서는 이 저장소의 핵심 자산을 “프로젝트 문서 + 실행 스크립트” 조합으로 가져가는 것이 가장 안전합니다.

### 권장 이식 방식

- 프로젝트 루트에 이 저장소 문서를 둠
- Claude Code에게 `google-jules-control/SKILL.md`를 프로젝트 운영 문서처럼 참조시키기
- 실제 Jules 제어는 여전히 `google-jules-control/scripts/jules_api.py`로 수행

### Claude Code용 적응 포인트

- 스킬이라는 개념이 직접적으로 같지 않을 수 있으므로, `SKILL.md`를 작업 규약 문서처럼 사용
- `doctor`, `repo-to-source`, `cleanup-report`를 먼저 익히게 하는 프롬프트가 좋음
- 긴 JSON 출력은 요약해서 사용자에게 전달하도록 지시

### 시작 프롬프트 예시

```text
Use the local project guide at google-jules-control/SKILL.md. Prefer the bundled Jules control script for all Jules operations. Start with doctor, resolve the repo to a Jules source, then continue with session creation or reporting.
```

### Setup checks와 완료 기준

- Claude Code 프로젝트 문서나 프롬프트가 `google-jules-control/SKILL.md`를 참조하는지 확인
- Claude Code shell에서 `doctor --compact`가 `.env`와 `JULES_API_KEY`를 읽는지 확인. 통과 기준은 `dotenv=yes api_key=yes api_ready=yes`
- long-running 명령은 중간 상태를 `summary`로 요약하고 필요하면 `wait`를 사용
- 긴 JSON 출력은 사용자에게 그대로 붙이지 말고 핵심 상태만 요약
- 사용자 검토에는 `--markdown`, 파일 보관이나 자동화에는 `export --output` 사용

완료 기준: Claude Code가 이 문서와 `SKILL.md`만 보고 source 해석, 세션 생성, 세션 요약, markdown/JSON 출력 선택을 수행할 수 있어야 합니다.

## EN

### Adaptation Model

In Claude Code, the safest migration model is to treat this repository as a combination of project docs plus an execution script.

### Recommended Porting Pattern

- Keep these documents in the project root
- Point Claude Code to `google-jules-control/SKILL.md` as the operating guide
- Keep actual Jules control in `google-jules-control/scripts/jules_api.py`

### Claude Code Adaptation Notes

- The skill concept may not map one-to-one, so use `SKILL.md` as a project operating contract
- Prefer prompts that teach Claude Code to start with `doctor`, `repo-to-source`, and `cleanup-report`
- Instruct it to summarize long JSON outputs before responding to users

### Starter Prompt Example

```text
Use the local project guide at google-jules-control/SKILL.md. Prefer the bundled Jules control script for all Jules operations. Start with doctor, resolve the repo to a Jules source, then continue with session creation or reporting.
```

### Setup Checks And Done Criteria

- Confirm Claude Code project docs or prompts point to `google-jules-control/SKILL.md`
- Confirm Claude Code shell execution can read `.env` and `JULES_API_KEY` with `doctor --compact`; pass only when it includes `dotenv=yes api_key=yes api_ready=yes`
- Summarize intermediate state for long-running commands with `summary`, and use `wait` when appropriate
- Do not paste long raw JSON to users; summarize the operational state first
- Use `--markdown` for human review and `export --output` for archived or automated JSON

Done criteria: Claude Code can use only this guide and `SKILL.md` to resolve a source, create a session, summarize it, and choose markdown versus JSON output correctly.
