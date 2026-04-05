# Issue Workflow / 이슈 운영 방식

## Rule / 원칙

앞으로 이 저장소의 비사소한 보강사항은 먼저 GitHub issue로 등록한 뒤 처리합니다.  
From now on, non-trivial improvements in this repository should be registered as GitHub issues before implementation.

적용 대상 / This applies to:

- 기능 보강 / feature improvements
- 안정화 작업 / hardening work
- 운영성 개선 / operational improvements
- 테스트 보강 / test coverage improvements
- 문서 정리 / documentation improvements

## Templates / 템플릿

- `Improvement / 보강 요청`
- `Hardening / 안정화 보강`

권장 기준 / Recommended usage:

- 사용자 경험, 기능, 문서, 워크플로 개선은 `Improvement`
- 안전성, 품질, 릴리즈 리스크, 회귀 방지는 `Hardening`

## Workflow / 처리 순서

1. 보강사항을 발견하면 먼저 issue를 생성합니다.  
   Create an issue first when an improvement is identified.
2. 문제, 가치, 제안 변경, 완료 기준을 채웁니다.  
   Fill in the problem, value, proposed change, and acceptance criteria.
3. 구현 브랜치나 PR에서 해당 issue를 연결합니다.  
   Link the issue from the implementation branch or PR.
4. 구현 후 검증 결과를 PR 또는 이슈에 남깁니다.  
   Record verification results in the PR or issue after implementation.
5. 릴리즈 노트가 필요한 경우 관련 버전에 연결합니다.  
   Link the change to the relevant release when release notes matter.

## Practical Rules / 실무 규칙

- 작은 오탈자 수준이 아닌 이상, 바로 고치기보다 먼저 issue를 남깁니다.  
  Unless it is a tiny typo-level fix, prefer creating an issue first.
- 코드 변경이 들어가면 가능한 한 테스트 또는 검증 명령을 함께 남깁니다.  
  When code changes are involved, include tests or verification commands whenever possible.
- 문서나 운영 규칙이 바뀌면 관련 가이드도 같이 업데이트합니다.  
  If docs or process change, update the related guides as well.
- PR에는 반드시 연결 이슈를 적습니다.  
  Every PR should include a linked issue.

## Suggested Labels / 추천 라벨

필수는 아니지만 아래 라벨 조합을 권장합니다.  
These are optional, but recommended.

- `improvement`
- `hardening`
- `docs`
- `tests`
- `ops`
- `release`
