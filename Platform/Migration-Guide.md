# Migration Guide

## KR

### 목적

이 문서는 `google-jules-control` 운영 방식을 Codex 이외의 플랫폼으로 옮길 때 공통 기준으로 사용합니다.

### 공통적으로 유지해야 하는 것

- Jules API 제어는 `google-jules-control/scripts/jules_api.py`를 단일 진실 원천으로 유지
- 인증은 `.env`의 `JULES_API_KEY` 기준으로 유지
- merge 확인은 `gh` 기반으로 유지
- 세션 종료는 항상 사용자 확인 후 실행

### 플랫폼 전환 체크포인트

1. 프롬프트 주입 방식
   - 시스템 지시
   - 프로젝트 문서
   - 세션 시작 프롬프트
2. 도구 실행 방식
   - 로컬 셸 명령 허용 여부
   - 장기 실행 명령 처리
   - JSON 출력 소비 방식
3. 파일 참조 방식
   - 절대 경로 링크 지원 여부
   - markdown 렌더링 품질
4. 운영 안전장치
   - 삭제 전 사용자 확인
   - merge 상태 확인
   - `.env` 파일 노출 방지

### 권장 이식 순서

1. `doctor`
2. `repo-to-source`
3. `create-session`
4. `summary`
5. `cleanup-report`
6. `notify-close-plan`
7. `close-merged-session`

## EN

### Purpose

Use this document as the shared baseline when adapting the `google-jules-control` workflow to platforms other than Codex.

### Keep These Invariants

- Keep `google-jules-control/scripts/jules_api.py` as the single source of truth for Jules API control
- Keep `.env` and `JULES_API_KEY` as the primary auth path
- Keep merge checks based on `gh`
- Keep session close, cancel, and delete actions behind explicit user confirmation

### Platform Migration Checkpoints

1. Prompt injection model
   - system instructions
   - project documentation
   - session-start prompts
2. Tool execution model
   - local shell access
   - long-running command handling
   - JSON output consumption
3. File reference model
   - support for absolute-path links
   - markdown rendering behavior
4. Operational safety
   - user confirmation before close, cancel, or delete
   - merge-state verification
   - protection against leaking `.env`

### Recommended Migration Order

1. `doctor`
2. `repo-to-source`
3. `create-session`
4. `summary`
5. `cleanup-report`
6. `notify-close-plan`
7. `close-merged-session`
