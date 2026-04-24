# Setup And Test / 설정 및 테스트

## 준비물 / Prerequisites

- Python 3
- [Jules settings](https://jules.google.com/settings)에서 발급한 Jules API 키 / A Jules API key from [Jules settings](https://jules.google.com/settings)
- merge 기반 정리 명령을 쓰려면 `gh` 설치 및 인증 / `gh` installed and authenticated for merge-aware cleanup commands
- 선택 사항: 공식 CLI 흐름까지 쓰려면 `jules` CLI / Optional: `jules` CLI for the official terminal workflow

## 자격 증명 설정 / Credential Setup

`.env` 파일에 아래처럼 넣습니다.  
Put this in `.env`.

```text
JULES_API_KEY=your_jules_api_key
```

권장 위치 / Recommended locations:

1. 저장소 루트 `.env` / Repository root `.env`
2. 스킬 루트 `google-jules-control/.env` / Skill root `google-jules-control/.env`

스크립트는 현재 작업 디렉토리를 먼저 보고, 없으면 스킬 루트를 봅니다.  
The script checks the current working directory first, then the skill root.

## 상태 점검 / Readiness Check

```bash
python3 google-jules-control/scripts/jules_api.py doctor --compact
python3 google-jules-control/scripts/jules_api.py doctor --compact --validate-api
```

검증 포함 정상 예시 / Healthy example with API validation:

```text
dotenv=yes api_key=yes api_validated=yes api_status=ok api_ready=yes gh=yes gh_auth=yes merge_ready=yes jules_cli=no jules_cli_auth=not_installed cli_ready=no ready=yes
```

REST API만 쓴다면 `jules_cli=no`는 문제 아닙니다.  
`jules_cli=no` is acceptable if you only use the REST API path.

기본 `doctor --compact`는 네트워크 API 호출을 하지 않습니다. 이 경우 `api_key=yes`는 키가 있다는 뜻이고, `api_ready=yes`는 아닙니다.
Plain `doctor --compact` does not make a network API call. In that mode, `api_key=yes` means the key is present, not that `api_ready=yes`.

`api_ready=yes`는 `--validate-api` probe가 성공해서 현재 키로 Jules API 인증이 확인됐다는 뜻입니다.
`api_ready=yes` means the `--validate-api` probe succeeded and the current key authenticated with the Jules API.

`cli_ready=yes`는 Jules CLI 경로도 바로 쓸 수 있다는 뜻입니다.  
`cli_ready=yes` means the Jules CLI path is also ready to use.

`merge_ready=yes`는 merge-aware reporting이 준비된 상태를 뜻합니다.  
`merge_ready=yes` means merge-aware reporting is ready to use.

`ready=yes`는 API path 또는 CLI path 중 적어도 하나가 준비됐다는 뜻입니다.  
`ready=yes` means at least one control path is ready.

## 기본 스모크 테스트 / Basic Smoke Test

1. 소스 목록 확인 / Verify source listing

```bash
python3 google-jules-control/scripts/jules_api.py list-sources
```

2. 저장소를 source로 해석 / Resolve a repository

```bash
python3 google-jules-control/scripts/jules_api.py repo-to-source --repo owner/repo --compact
```

3. 가벼운 테스트 세션 생성 / Create a lightweight test session

```bash
python3 google-jules-control/scripts/jules_api.py create-session \
  --source sources/github/owner/repo \
  --branch main \
  --title "Smoke test" \
  --prompt "Smoke test only: inspect the repository at a high level and summarize the top-level structure without making code changes." \
  --require-plan-approval
```

4. 세션 확인 / Check the session

```bash
python3 google-jules-control/scripts/jules_api.py summary --session sessions/SESSION_ID
```

`AWAITING_PLAN_APPROVAL` 상태라면 plan이 smoke-test 범위에 머무는지 먼저 확인합니다. 코드 변경, 리팩터링, 의존성 변경이 포함되면 승인하지 않습니다.
If the session is `AWAITING_PLAN_APPROVAL`, review that the plan stays inside the smoke-test scope before approval. Do not approve plans that include code changes, refactors, or dependency changes.

5. 테스트 세션 정리 / Clean up the test session

이 단계는 되돌릴 수 없는 세션 삭제입니다. 테스트 세션을 삭제해도 된다고 확인한 뒤 실행합니다.
This is irreversible session deletion. Run it only after confirming the test session can be deleted.

```bash
python3 google-jules-control/scripts/jules_api.py delete-session \
  --session sessions/SESSION_ID \
  --confirm-delete DELETE_JULES_SESSION
```

## 자주 쓰는 명령 / Common Commands

상태 점검과 탐색 / Health and discovery:

```bash
python3 -m unittest discover -s tests
python3 google-jules-control/scripts/jules_api.py doctor --compact
python3 google-jules-control/scripts/jules_api.py gh-auth-check --compact
python3 google-jules-control/scripts/jules_api.py repo-to-source --repo owner/repo --compact
```

세션 제어 / Session control:

```bash
python3 google-jules-control/scripts/jules_api.py create-session ...
python3 google-jules-control/scripts/jules_api.py summary --session sessions/SESSION_ID
python3 google-jules-control/scripts/jules_api.py resume --session sessions/SESSION_ID --prompt "Continue."
python3 google-jules-control/scripts/jules_api.py approve-plan --session sessions/SESSION_ID
```

`approve-plan`과 `AWAITING_PLAN_APPROVAL` 세션을 승인할 수 있는 `resume`은 plan scope review 후에만 실행합니다.
Run `approve-plan`, and `resume` when it would approve an `AWAITING_PLAN_APPROVAL` session, only after reviewing the generated plan against the task scope.

정리와 리포트 / Cleanup and reporting:

```bash
python3 google-jules-control/scripts/jules_api.py cleanup-report --repo-filter owner/repo --require-all-merged --markdown
python3 google-jules-control/scripts/jules_api.py close-ready-report --repo-filter owner/repo --require-all-merged --markdown
python3 google-jules-control/scripts/jules_api.py stale-session-report --repo-filter owner/repo --stale-after-hours 24
```

페이지네이션 메모 / Pagination note:

- `list-*`, `cleanup-report`, `close-ready-report`, `repo-to-source`, `list-sources` 같은 집계형 명령은 기본적으로 모든 페이지를 수집합니다.  
  Aggregated commands such as `list-*`, `cleanup-report`, `close-ready-report`, `repo-to-source`, and `list-sources` collect all pages by default.
- `--page-token`은 단일 페이지 응답을 요청하는 옵션이 아니라, “이 토큰부터 끝까지” 수집을 시작하는 시작점입니다.  
  `--page-token` is a starting point for aggregation, not a raw single-page mode.

## 문제 해결 / Troubleshooting

- `ready=no`: `doctor`를 `--compact` 없이 실행해서 어떤 항목이 비었는지 확인합니다.  
  Run `doctor` without `--compact` to see the missing dependency.
- `api_ready=no`: `api_key`, `api_validated`, `api_status`를 함께 봅니다. 검증이 필요하면 `doctor --compact --validate-api`를 실행합니다.
  Check `api_key`, `api_validated`, and `api_status` together. Run `doctor --compact --validate-api` when you need credential validation.
- `cli_ready=no`: CLI 경로를 쓰려면 `jules login` 또는 CLI 인증 상태를 확인합니다.  
  If you want the CLI path, check `jules login` or the CLI authentication state.
- `merge_ready=no`: merge 기반 리포트 전에 `gh auth status`를 확인합니다.  
  Check `gh auth status` before using merge-aware reports.
- `JULES_API_KEY is required`: `.env` 위치와 키 이름을 다시 확인합니다.  
  Check `.env` placement and key name.
- `gh_auth=no`: `gh auth status` 후 다시 로그인합니다.  
  Run `gh auth status` and sign in again.
- `count: 0` from `repo-to-source`: Jules에 저장소가 연결되어 있는지 확인합니다.  
  Verify the repository is connected in Jules.
