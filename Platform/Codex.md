# Codex

## KR

### 현재 기준 플랫폼

이 저장소는 현재 Codex 기준으로 가장 잘 맞춰져 있습니다.

### 어떻게 연결되는가

- 저장소 운영 문서: `README.md`
- 스킬 본문: `google-jules-control/SKILL.md`
- 실행 스크립트: `google-jules-control/scripts/jules_api.py`

### Codex에서의 권장 사용 방식

- 프로젝트 루트에서 실행
- `.env` 자동 로드 사용
- 긴 작업은 `summary`, `wait`, `cleanup-report` 중심으로 운영
- 사용자에게 보이는 메시지는 `notify-close-plan --markdown`으로 생성

### Codex용 운영 패턴

```bash
python3 google-jules-control/scripts/jules_api.py doctor --compact
python3 google-jules-control/scripts/jules_api.py repo-to-source --repo owner/repo --compact
python3 google-jules-control/scripts/jules_api.py create-session ...
python3 google-jules-control/scripts/jules_api.py summary --session sessions/SESSION_ID
```

### Setup checks와 완료 기준

- `$google-jules-control` 또는 `google-jules-control/SKILL.md`가 Codex 컨텍스트에서 발견되는지 확인
- Codex shell에서 `doctor --compact`가 `.env`와 `JULES_API_KEY`를 읽는지 확인. 통과 기준은 `dotenv=yes api_key=yes api_ready=yes`
- long-running 세션은 `wait` 또는 반복 `summary`로 상태를 갱신
- 사용자 보고에는 `cleanup-report --markdown`, `close-ready-report --markdown`, `notify-close-plan --markdown` 사용
- 구조화된 결과가 필요할 때만 JSON 원문이나 `export --output` 사용

완료 기준: Codex가 source 해석, 세션 생성, 세션 요약, markdown 보고를 사용자에게 간결하게 전달하고, JSON 원문이나 `export --output`은 구조화/보관 용도로만 사용할 수 있어야 합니다.

## EN

### Current Reference Platform

This repository is currently optimized for Codex.

### Main Integration Points

- Repository operations: `README.md`
- Skill instructions: `google-jules-control/SKILL.md`
- Execution script: `google-jules-control/scripts/jules_api.py`

### Recommended Usage in Codex

- Run from the repository root
- Rely on automatic `.env` loading
- Use `summary`, `wait`, and `cleanup-report` for long-running work
- Use `notify-close-plan --markdown` for user-facing close confirmation

### Codex Operating Pattern

```bash
python3 google-jules-control/scripts/jules_api.py doctor --compact
python3 google-jules-control/scripts/jules_api.py repo-to-source --repo owner/repo --compact
python3 google-jules-control/scripts/jules_api.py create-session ...
python3 google-jules-control/scripts/jules_api.py summary --session sessions/SESSION_ID
```

### Setup Checks And Done Criteria

- Confirm `$google-jules-control` or `google-jules-control/SKILL.md` is discoverable in the Codex context
- Confirm Codex shell execution can read `.env` and `JULES_API_KEY` with `doctor --compact`; pass only when it includes `dotenv=yes api_key=yes api_ready=yes`
- Monitor long-running sessions with `wait` or repeated `summary`
- Use `cleanup-report --markdown`, `close-ready-report --markdown`, and `notify-close-plan --markdown` for user-facing reports
- Use raw JSON or `export --output` only when structured output is needed

Done criteria: Codex can resolve a source, create a session, summarize the session, present markdown reports concisely, and reserve raw JSON or `export --output` for structured or archival use.
