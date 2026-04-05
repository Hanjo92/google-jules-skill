# google-jules-skill

![Google Jules Control Banner](./assets/jules-control-banner.png)


Google Jules를 LLM 에이전트에서 제어하기 위한 스킬 저장소입니다.  
This repository contains a skill for controlling Google Jules from an LLM agent.

## 포함 스킬 / Included Skill

- `google-jules-control`
  Google Jules REST API와 Jules CLI를 통해 세션 생성, 상태 조회, 후속 지시, 정리 리포트, merge 확인, 세션 종료를 수행합니다.  
  Controls Google Jules sessions through the Jules REST API and Jules CLI, including session creation, status checks, follow-up instructions, cleanup reports, merge checks, and session closure.

## 저장소 구조 / Repository Layout

```text
google-jules-skill/
├── README.md
├── docs/
│   ├── setup-and-test.md
│   └── release-checklist.md
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

1. `google-jules-control/.env.example`를 바탕으로 `.env`를 준비합니다.  
   Create a `.env` file from `google-jules-control/.env.example`.
2. `.env`에 `JULES_API_KEY`를 넣습니다.  
   Put your `JULES_API_KEY` into `.env`.
3. 준비 상태를 확인합니다.  
   Run a readiness check.

```bash
python3 google-jules-control/scripts/jules_api.py doctor --compact
```

4. 저장소를 Jules source로 해석합니다.  
   Resolve a repository to a Jules source.

```bash
python3 google-jules-control/scripts/jules_api.py repo-to-source --repo owner/repo --compact
```

5. 자세한 사용법은 `google-jules-control/SKILL.md`를 참고합니다.  
   Read `google-jules-control/SKILL.md` for the full operating guide.

## 가이드 / Guides

- `docs/setup-and-test.md`
- `docs/release-checklist.md`
- `Platform/README.md`

## 메모 / Notes

- 실제 시크릿은 `.env`에만 넣고 `.env.example`에는 넣지 않습니다.  
  Put real secrets in `.env`, not in `.env.example`.
- `google-jules-control/.gitignore`는 스킬 폴더 안의 `.env`를 제외합니다.  
  `google-jules-control/.gitignore` excludes `.env` inside the skill folder.
- 루트 `.gitignore`도 저장소 루트 `.env`를 제외합니다.  
  The repository-root `.gitignore` also excludes the root `.env`.
- 로컬 테스트에서는 저장소 루트 `.env`도 사용할 수 있습니다.  
  The repository root `.env` also works for local testing.
