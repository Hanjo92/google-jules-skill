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

## Fresh Checkout Validation / 새 checkout 검증

아래 명령은 이 저장소 루트의 fresh checkout에서 그대로 실행 가능해야 합니다. 실제 Jules 계정이나 target repository가 필요한 검증은 다음 섹션으로 분리합니다.
The commands below must run as-is from a fresh checkout of this repository root. Checks that require a real Jules account or target repository are separated into the next section.

```bash
python3 -m py_compile google-jules-control/scripts/jules_api.py
python3 -m unittest discover -s tests

python3 google-jules-control/scripts/jules_api.py --help >/tmp/google-jules-skill-help.txt
python3 google-jules-control/scripts/jules_api.py doctor --help >/tmp/google-jules-skill-doctor-help.txt
python3 google-jules-control/scripts/jules_api.py check-pr-readiness --help >/tmp/google-jules-skill-pr-help.txt
python3 google-jules-control/scripts/jules_api.py request-pr-rework --help >/tmp/google-jules-skill-rework-help.txt
python3 google-jules-control/scripts/jules_api.py cleanup-report --help >/tmp/google-jules-skill-cleanup-help.txt
python3 google-jules-control/scripts/jules_api.py close-ready-report --help >/tmp/google-jules-skill-close-ready-help.txt
```

Packaging checks / 패키징 점검:

```bash
test -f README.md
test -f google-jules-control/SKILL.md
test -f google-jules-control/agents/openai.yaml
test -f google-jules-control/.env.example
grep -qx '.env' .gitignore
grep -qx '.env' google-jules-control/.gitignore
test -z "$(git ls-files | grep -E '(^|/)\.env$' || true)"
```

## Live Account Validation / 실제 계정 검증

아래 명령은 실제 `JULES_API_KEY`, GitHub 인증, Jules에 연결된 target repository가 있을 때만 실행합니다.
Run these only when a real `JULES_API_KEY`, GitHub auth, and a Jules-connected target repository are available.

```bash
: "${OWNER_REPO:?Set OWNER_REPO as owner/repo before live checks}"

python3 google-jules-control/scripts/jules_api.py doctor --compact
python3 google-jules-control/scripts/jules_api.py gh-auth-check --compact

SOURCE="$(python3 google-jules-control/scripts/jules_api.py repo-to-source --repo "$OWNER_REPO" --compact)"
test -n "$SOURCE" || { echo "No Jules source found for $OWNER_REPO"; exit 1; }
printf '%s\n' "$SOURCE"

python3 google-jules-control/scripts/jules_api.py list-sources >/tmp/google-jules-skill-sources.json
python3 google-jules-control/scripts/jules_api.py cleanup-report --repo-filter "$OWNER_REPO" --compact
python3 google-jules-control/scripts/jules_api.py close-ready-report --repo-filter "$OWNER_REPO" --markdown
```

통과 기준: `doctor --compact`에 `dotenv=yes api_key=yes api_ready=yes`가 포함되어야 합니다. merge-aware reporting이나 cleanup을 검증하려면 `merge_ready=yes`도 필요합니다.
Pass criteria: `doctor --compact` must include `dotenv=yes api_key=yes api_ready=yes`. `merge_ready=yes` is also required before validating merge-aware reporting or cleanup.

Smoke session handoff / 스모크 세션 handoff:

- `docs/setup-and-test.md`의 `repo-to-source` -> `create-session` -> `summary` -> `export` -> cleanup 흐름을 한 번 실행 / Run the `repo-to-source` -> `create-session` -> `summary` -> `export` -> cleanup flow in `docs/setup-and-test.md` once
- long-running 상태는 `wait` 또는 반복 `summary`로 확인 / Inspect long-running states with `wait` or repeated `summary`
- 사람에게 보여줄 보고서는 `--markdown`, 자동화/보관용 결과는 JSON 또는 `export --output`으로 확인 / Use `--markdown` for human review and JSON or `export --output` for automation or archival checks

## Platform Guide Release Checks / 플랫폼 가이드 릴리즈 점검

- `Platform/README.md`의 공통 setup checks와 done criteria가 현재 명령 이름을 반영하는지 확인 / Confirm shared setup checks and done criteria in `Platform/README.md` reflect current command names
- `Platform/Codex.md`, `Platform/Claude-Code.md`, `Platform/Google-Antigravity.md`가 skill registration 또는 project-doc injection, `.env` 접근, long-running command 처리, markdown/JSON 출력 처리를 각각 다루는지 확인 / Confirm each platform guide covers skill registration or project-doc injection, `.env` access, long-running command handling, and markdown/JSON output handling
- full/strict 플랫폼 prompt 문서가 `doctor`, `repo-to-source`, `summary`, markdown report, concise JSON summary 흐름을 유지하는지 확인 / Confirm full and strict platform prompt docs preserve the `doctor`, `repo-to-source`, `summary`, markdown report, and concise JSON-summary flow

## Version-Specific Notes / 버전별 확인 이력

일반 릴리즈 절차와 분리해서 유지합니다. 새 버전에서만 필요한 수동 확인은 이 섹션에 추가하고, 다음 릴리즈에서 일반 절차로 승격할지 판단합니다.
Keep these separate from the general release procedure. Add one-off manual checks for a specific release here, then decide in the next release whether they should become general procedure.

`v0.2.0` focus / `v0.2.0` 중점 확인:

- `check-pr-readiness --help`와 `request-pr-rework --help`가 정상 출력되는지 확인 / Confirm `check-pr-readiness --help` and `request-pr-rework --help` both render correctly
- `close-ready-report --compact`가 `candidates`와 `caution` 요약을 정상 반환하는지 확인 / Confirm `close-ready-report --compact` returns the expected `candidates` and `caution` summary
- `cleanup-report --compact`가 merged, unmerged, without-PR 분류를 정상 반환하는지 확인 / Confirm `cleanup-report --compact` returns merged, unmerged, and without-PR classification
- API 제한 상황에서 quota 또는 rate-limit 오류 메시지가 명확하게 보이는지 확인 / Confirm quota or rate-limit failures surface a clear error message

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
