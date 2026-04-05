# Release Checklist / 배포 체크리스트

공유하거나 배포하기 전에 아래 항목을 확인합니다.  
Use this checklist before sharing or publishing the skill.

## 사전 점검 / Pre-Release

- 비사소한 보강사항이 구현 전에 issue로 등록되어 있는지 확인 / Confirm non-trivial improvements were registered as issues before implementation
- `google-jules-control/SKILL.md`가 현재 명령 셋을 반영하는지 확인 / Confirm `google-jules-control/SKILL.md` reflects the current command set
- `google-jules-control/agents/openai.yaml`이 스킬 이름과 목적에 맞는지 확인 / Confirm `google-jules-control/agents/openai.yaml` still matches the skill name and purpose
- `google-jules-control/.env.example`에 실제 키가 없는지 확인 / Confirm `google-jules-control/.env.example` contains placeholders only
- `google-jules-control/.gitignore`에 `.env`가 포함되는지 확인 / Confirm `google-jules-control/.gitignore` excludes `.env`
- 저장소 루트 `.gitignore`에 `.env`가 포함되는지 확인 / Confirm the repository-root `.gitignore` excludes `.env`
- 저장소 루트와 스킬 폴더에 실제 시크릿이 추적되지 않는지 확인 / Ensure no real secrets are tracked in the repository root or skill folder

## 검증 / Validation

```bash
python3 -m py_compile google-jules-control/scripts/jules_api.py
python3 -m unittest discover -s tests
python3 /path/to/quick_validate.py google-jules-control
```

`v0.2.0` focus / `v0.2.0` 중점 확인:

- `check-pr-readiness --help`와 `request-pr-rework --help`가 정상 출력되는지 확인 / Confirm `check-pr-readiness --help` and `request-pr-rework --help` both render correctly
- `close-ready-report --compact`가 `candidates`와 `caution` 요약을 정상 반환하는지 확인 / Confirm `close-ready-report --compact` returns the expected `candidates` and `caution` summary
- `cleanup-report --compact`가 merged, unmerged, without-PR 분류를 정상 반환하는지 확인 / Confirm `cleanup-report --compact` returns merged, unmerged, and without-PR classification
- API 제한 상황에서 quota 또는 rate-limit 오류 메시지가 명확하게 보이는지 확인 / Confirm quota or rate-limit failures surface a clear error message

## 라이브 점검 / Live Checks

```bash
python3 google-jules-control/scripts/jules_api.py doctor --compact
python3 google-jules-control/scripts/jules_api.py repo-to-source --repo owner/repo --compact
python3 google-jules-control/scripts/jules_api.py list-sources
python3 google-jules-control/scripts/jules_api.py close-ready-report --compact
python3 google-jules-control/scripts/jules_api.py cleanup-report --compact
```

권장 / Recommended:

- `--require-plan-approval`로 스모크 테스트 세션 1회 생성 / Create one smoke-test session with `--require-plan-approval`
- 해당 세션에서 `summary` 확인 / Verify `summary` works for that session
- 테스트 세션 또는 기존 세션으로 `check-pr-readiness`를 1회 확인 / Run `check-pr-readiness` once against a test or existing session
- merge 불가 PR이 있다면 `request-pr-rework --markdown` 출력이 사용자에게 바로 전달 가능한지 확인 / If a PR is not merge-ready, confirm `request-pr-rework --markdown` produces a user-ready follow-up message
- 테스트 후 세션 삭제 / Delete the smoke-test session afterward

## 배포 판단 / Deployment Judgment

배포 가능 / Ready to ship:

- 검증 통과 / Validation passes
- `doctor` 상태 정상 / `doctor` shows the expected healthy state
- 실제 키로 Jules API 호출 성공 / Jules API calls succeed with a real key
- 최소 한 개 실제 저장소에서 source 해석 성공 / Source resolution works for at least one real repository
- 세션 생성과 정리를 최소 1회 end-to-end로 확인 / Session creation and cleanup have been tested end to end at least once
- merge-aware 보고서와 close safety 흐름이 실제 계정에서 오류 없이 동작 / Merge-aware reports and close-safety flows run cleanly against a real account

배포 보류 / Hold release if:

- 추적 파일에 시크릿 존재 / Secrets are present in tracked files
- merge 기반 명령을 안내하지만 `gh` 인증이 깨져 있음 / `gh` authentication is broken while merge-aware commands are advertised
- 실제 계정에서 repo lookup 또는 reporting 실패 / Repo lookup or reporting commands fail against a real account
- PR readiness 또는 rework 명령이 잘못된 `gh` 상태로 오탐하거나 빈 결과를 반환 / PR readiness or rework commands misreport due to broken `gh` state or empty GitHub metadata
