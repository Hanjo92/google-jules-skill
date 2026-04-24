# google-jules-skill

![Google Jules Control Banner](./assets/jules-control-banner.png)


Google Jules를 LLM 에이전트에서 제어하기 위한 스킬 저장소입니다.  
This repository contains a skill for controlling Google Jules from an LLM agent.

## 포함 스킬 / Included Skill

- `google-jules-control`
  Google Jules REST API와 Jules CLI를 통해 세션 생성, 상태 조회, 후속 지시, 정리 리포트, merge 확인, 세션 종료를 수행합니다.  
  Controls Google Jules sessions through the Jules REST API and Jules CLI, including session creation, status checks, follow-up instructions, cleanup reports, merge checks, and session closure.

## 설치 및 등록 / Installation And Registration

- 스킬을 등록하려면 `SKILL.md`가 들어 있는 `google-jules-control/` 폴더를 에이전트의 skills 디렉터리에 둡니다. Codex에 수동으로 로컬 스킬을 설치할 때는 보통 `${CODEX_HOME:-$HOME/.codex}/skills/google-jules-control` 위치를 사용합니다.
  To register the skill, place the `google-jules-control/` folder that contains `SKILL.md` in the agent skills directory. For manual local Codex skill installs, this usually means `${CODEX_HOME:-$HOME/.codex}/skills/google-jules-control`.
- `google-jules-control/agents/openai.yaml`은 이 manifest를 지원하는 OpenAI 계열 에이전트가 표시 이름, 짧은 설명, 기본 프롬프트를 읽을 때 쓰는 파일입니다. Python helper가 실행 중에 읽는 설정 파일은 아닙니다.
  `google-jules-control/agents/openai.yaml` is for OpenAI-style agents that support this manifest and need the display name, short description, and default prompt. The Python helper does not read it at runtime.
- 등록 확인은 새 에이전트 컨텍스트에서 `$google-jules-control`을 호출해 `doctor --compact` 실행을 요청하는 방식으로 확인합니다. 인식되지 않으면 설치 위치와 `SKILL.md`의 `name: google-jules-control`을 확인합니다.
  Verify discoverability by invoking `$google-jules-control` in a fresh agent context and asking it to run `doctor --compact`. If it is not recognized, check the install location and the `name: google-jules-control` front matter in `SKILL.md`.

## 저장소 구조 / Repository Layout

```text
google-jules-skill/
├── README.md
├── docs/
│   ├── setup-and-test.md
│   ├── release-checklist.md
│   └── issue-workflow.md
├── tests/
│   └── test_jules_api.py
├── Platform/
│   ├── README.md
│   ├── Migration-Guide.md
│   └── ...
└── google-jules-control/
    ├── .env.example
    ├── .gitignore
    ├── SKILL.md
    ├── agents/openai.yaml
    ├── references/jules-reference.md
    └── scripts/jules_api.py
```

## 빠른 시작 / Quick Start

1. 이 스킬 저장소 clone의 루트에서 시작합니다.
   Start from the root of this skill repository clone.

```bash
cd google-jules-skill
```

2. `google-jules-control/.env.example`를 `google-jules-control/.env`로 복사합니다.
   Copy `google-jules-control/.env.example` to `google-jules-control/.env`.

```bash
cp google-jules-control/.env.example google-jules-control/.env
```

3. `.env`에 `JULES_API_KEY`를 넣습니다. 저장소 루트 `.env`가 이미 있으면 스크립트가 그 파일을 먼저 읽으므로, 그 파일에도 `JULES_API_KEY`가 있어야 합니다.
   Put your `JULES_API_KEY` into `.env`. If a repository-root `.env` already exists, the script reads that file first, so it must also contain `JULES_API_KEY`.
4. 준비 상태를 확인합니다.
   Run a readiness check.

```bash
python3 google-jules-control/scripts/jules_api.py doctor --compact
```

5. 저장소를 Jules source로 해석합니다.
   Resolve a repository to a Jules source.

```bash
python3 google-jules-control/scripts/jules_api.py repo-to-source --repo owner/repo --compact
```

6. 복사해서 따라갈 수 있는 smoke test는 `docs/setup-and-test.md`를 참고합니다.
   For a copy-paste smoke test, read `docs/setup-and-test.md`.
7. 자세한 사용법은 `google-jules-control/SKILL.md`를 참고합니다.
   Read `google-jules-control/SKILL.md` for the full operating guide.

## 가이드 / Guides

- `docs/setup-and-test.md`
- `docs/release-checklist.md`
- `docs/issue-workflow.md`
- `Platform/README.md`

## 운영 원칙 / Working Rule

- 보강사항은 먼저 GitHub issue로 등록한 뒤 처리합니다.  
  Register non-trivial improvements as GitHub issues before implementation.

## 메모 / Notes

- 실제 시크릿은 `.env`에만 넣고 `.env.example`에는 넣지 않습니다.  
  Put real secrets in `.env`, not in `.env.example`.
- `google-jules-control/.gitignore`는 스킬 폴더 안의 `.env`를 제외합니다.  
  `google-jules-control/.gitignore` excludes `.env` inside the skill folder.
- 루트 `.gitignore`도 저장소 루트 `.env`를 제외합니다.  
  The repository-root `.gitignore` also excludes the root `.env`.
- 로컬 테스트에서는 저장소 루트 `.env`도 사용할 수 있습니다.  
  The repository root `.env` also works for local testing.
