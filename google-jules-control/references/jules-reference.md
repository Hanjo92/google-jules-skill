# Jules Reference

Use this file only when you need command selection, endpoint recall, or troubleshooting details while operating Google Jules.

## API vs CLI

Choose the control surface that best matches the task:

- REST API: best for automation, scripts, bots, and capturing structured JSON.
- Jules Tools CLI: best for interactive terminal usage, repo inference from the current directory, and pulling changes locally.

## REST API Essentials

Base URL:

```text
https://jules.googleapis.com/v1alpha
```

Authentication:

- Pass the API key in `x-goog-api-key`.
- Store the key in `JULES_API_KEY`.
- Prefer a local `.env` file with `JULES_API_KEY=...`. The bundled script auto-loads `.env` from the current working directory or the skill root.
- Generate the key in `https://jules.google.com/settings`.

Core resources:

- `GET /sources`
- `POST /sessions`
- `GET /sessions`
- `GET /sessions/{id}`
- `DELETE /sessions/{id}`
- `POST /sessions/{id}:sendMessage`
- `POST /sessions/{id}:approvePlan`
- `GET /sessions/{id}/activities`
- `GET /sessions/{id}/activities/{activityId}`

Important session fields:

- `sourceContext.source`: full source resource name such as `sources/github/OWNER/REPO`
- `sourceContext.githubRepoContext.startingBranch`: required branch name. This is the remote branch Jules starts from; it is not a local checkout path.
- `requirePlanApproval`: if true, execution pauses for approval
- `automationMode`: `AUTO_CREATE_PR` or omitted. `AUTO_CREATE_PR` asks Jules to create a pull request automatically when changes are ready.
- `state`: one of `QUEUED`, `PLANNING`, `AWAITING_PLAN_APPROVAL`, `AWAITING_USER_FEEDBACK`, `IN_PROGRESS`, `PAUSED`, `FAILED`, `COMPLETED`
- `url`: Jules web URL for the session

Practical note:

- There is no dedicated REST `resume` endpoint in the current public API. If a session is waiting, resume it by approving a pending plan or sending a follow-up message.
- There is no reversible REST `cancel` endpoint distinct from deletion. Deleting the session is the closest cancellation-style action.
- The public API does not document a reliable remaining-usage or quota-balance endpoint for end users. Handle quota failures explicitly, but do not guess a remaining amount.
- If the user does not specify a branch, check the repository default branch before using `--branch`; not every repository uses `main`.
- Use an existing feature branch only when the user wants Jules to continue that remote branch, and include scope notes that preserve the branch intent.
- Omit `AUTO_CREATE_PR` for investigation, smoke tests, plan-only sessions, existing PR rework, or workflows where a human should inspect the output before opening a PR.

Activity types to watch:

- `planGenerated`
- `agentMessaged`
- `progressUpdated`
- `planApproved`
- `sessionCompleted`
- `sessionFailed`

## CLI Essentials

Installation:

```bash
npm install -g @google/jules
```

Authentication:

```bash
jules login
```

Useful commands:

```bash
jules remote list --repo
jules remote list --session
jules remote new --repo . --session "write unit tests"
jules remote pull --session 123456
```

## Merged-work cleanup

The Jules REST API does not expose GitHub merge state directly. To close a session only after merge:

1. Read the session outputs and find pull request URLs.
2. Check GitHub merge state for those PRs.
3. Ask the user for confirmation.
4. Delete the Jules session only after confirmation.

The bundled `jules_api.py` script automates this with:

- `doctor --compact`
- `gh-auth-check --compact`
- `repo-to-source --repo owner/repo --compact`
- `cleanup-report --repo-filter owner/repo --require-all-merged`
- `close-ready-report --repo-filter owner/repo --require-all-merged --markdown`
- `list-active-sessions --repo-filter owner/repo --include-merge-status`
- `stale-session-report --repo-filter owner/repo --stale-after-hours 24`
- `list-merged-sessions --repo-filter owner/repo --require-all-merged`
- `list-unmerged-sessions --repo-filter owner/repo`
- `check-merge-status --session ...`
- `check-pr-readiness --session ...`
- `request-pr-rework --session ... --markdown`
- `notify-close-plan --session ... --markdown`
- `close-merged-session --session ... --confirm-close CLOSE_MERGED_SESSION`

Implementation detail:

- Merge status is checked through `gh pr view <url> --json state,mergedAt,...`.
- Merge readiness is checked through `gh pr view <url> --json mergeable,mergeStateStatus,reviewDecision,statusCheckRollup,...`.
- If `gh` is missing or unauthenticated, merge status falls back to `unknown` and close should not proceed automatically.
- `gh-auth-check` is the fast preflight check before any merge-aware report.
- `doctor` separates `api_ready`, `cli_ready`, and `merge_ready`. `ready=yes` means at least one control path is available.
- `close-ready-report` distinguishes between `candidates` and `cautionCandidates`. Treat caution entries as manual-review items, not automatic close targets.
- `close-merged-session` refuses `caution` sessions by default. Only use `--allow-caution-close` after explicit user approval.

Pagination contract:

- Aggregated list/report commands collect all pages by default.
- `--page-token` means “start aggregation from this token”, not “return a single raw page”.
- Aggregated JSON responses include a `pagination` object so the behavior is explicit.

## Troubleshooting

- `API key not valid`: regenerate the key, strip spaces, and verify `JULES_API_KEY` is exported in the current shell.
- `.env` not picked up`: verify the file is named exactly `.env` and placed either in the current working directory or the skill root.
- `Permission denied`: verify the Google account has Jules access and the GitHub repo is connected inside Jules.
- `Usage or rate limit exceeded`: retry later, reduce automation frequency, or check the Jules account/project limits. The script will fail clearly instead of estimating remaining usage.
- No matching source: install/connect the GitHub repository in Jules first, then re-run `list-sources`.
- Session appears stuck: inspect the latest activities and state before retrying. `AWAITING_PLAN_APPROVAL` and `AWAITING_USER_FEEDBACK` are usually waiting states, not failures.
- Need richer repo context: keep the repository `AGENTS.md` current so Jules can infer project-specific conventions.
- `gh pr view` fails: run `gh auth status` and authenticate the right GitHub account before using merge-status commands.
