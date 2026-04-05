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
```

정상 예시 / Healthy example:

```text
dotenv=yes api_key=yes gh=yes gh_auth=yes merge_ready=yes jules_cli=no ready=yes
```

REST API만 쓴다면 `jules_cli=no`는 문제 아닙니다.  
`jules_cli=no` is acceptable if you only use the REST API path.

`ready=yes`는 API helper가 바로 실행 가능한 상태를 뜻합니다.  
`merge_ready=yes` means merge-aware reporting is also ready to use.

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

5. 테스트 세션 정리 / Clean up the test session

```bash
python3 google-jules-control/scripts/jules_api.py delete-session --session sessions/SESSION_ID
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

정리와 리포트 / Cleanup and reporting:

```bash
python3 google-jules-control/scripts/jules_api.py cleanup-report --repo-filter owner/repo --require-all-merged --markdown
python3 google-jules-control/scripts/jules_api.py close-ready-report --repo-filter owner/repo --require-all-merged --markdown
python3 google-jules-control/scripts/jules_api.py stale-session-report --repo-filter owner/repo --stale-after-hours 24
```

## 문제 해결 / Troubleshooting

- `ready=no`: `doctor`를 `--compact` 없이 실행해서 어떤 항목이 비었는지 확인합니다.  
  Run `doctor` without `--compact` to see the missing dependency.
- `merge_ready=no`: merge 기반 리포트 전에 `gh auth status`를 확인합니다.  
  Check `gh auth status` before using merge-aware reports.
- `JULES_API_KEY is required`: `.env` 위치와 키 이름을 다시 확인합니다.  
  Check `.env` placement and key name.
- `gh_auth=no`: `gh auth status` 후 다시 로그인합니다.  
  Run `gh auth status` and sign in again.
- `count: 0` from `repo-to-source`: Jules에 저장소가 연결되어 있는지 확인합니다.  
  Verify the repository is connected in Jules.
