---
name: google-jules-control
description: Control Google's Jules coding agent through the Jules REST API or the Jules Tools CLI. Use when the user wants Codex to ask Jules to do coding work, start or continue a Jules session, approve a Jules plan, check Jules status or activities, export Jules results, cancel a Jules run, or pull back work for a GitHub-connected repository. Typical triggers include requests such as "run this in Jules", "ask Jules to fix it", "continue the Jules session", "show the latest Jules activity", "approve the Jules plan", and "export the Jules session summary".
---

# Google Jules Control

Use this skill to delegate coding work to Google Jules from an agentic workflow. Prefer the bundled API helper for deterministic automation. Prefer the official `jules` CLI when the user wants repo inference from the current directory, an authenticated terminal workflow, or to pull changes locally.

## Quick Start

1. Verify one control path is available.
   - API path: put `JULES_API_KEY` in a `.env` file from `https://jules.google.com/settings`.
   - CLI path: install `@google/jules`, then run `jules login`.
   - API/CLI health check: run `python3 scripts/jules_api.py doctor --compact`.
   - API credential validation: run `python3 scripts/jules_api.py doctor --compact --validate-api`.
   - Merge-aware reporting health check: run `python3 scripts/jules_api.py gh-auth-check --compact`.
2. Discover the target repository/source.
   - API path: run `python3 scripts/jules_api.py repo-to-source --repo owner/repo --compact` or `python3 scripts/jules_api.py list-sources`.
   - CLI path: run `jules remote list --repo` or use `jules remote new --repo .` from the repo root.
3. Create a session with a concrete prompt and branch. By default the script wraps the prompt with a strict-scope contract so Jules stays narrow and asks questions when needed.
4. Poll session state or activities until Jules requests approval, feedback, or completes.
5. Approve the latest plan if the session enters `AWAITING_PLAN_APPROVAL`.
6. If needed, inspect open sessions with `list-active-sessions`.
7. For completed PR work, verify merge status before closing the Jules session.
8. Summarize results for the user, including session URL, current state, latest agent message, PR status, and whether the session is safe to close.

## Prompt Hardening Defaults

The API helper now wraps `create-session`, `send-message`, `resume`, and `request-pr-rework` prompts with a shared strict-scope contract by default.

Default behavior:

- Jules should interpret the task as narrowly as possible.
- Jules should not expand scope on its own.
- Jules should touch only what it must and clean up only its own mess.
- Jules should avoid unrelated cleanup, refactors, optimization, or restructuring unless explicitly requested.
- Jules should avoid improving adjacent code, comments, or formatting just because it noticed them.
- Every changed line should trace directly to the user's request.
- If Jules notices unrelated dead code, it should mention it instead of deleting it.
- If the request is ambiguous, or if work outside the stated scope appears necessary, Jules should stop and ask a clarifying question instead of choosing the broader path.
- Jules should prefer the smallest patch that satisfies the stated task.
- Jules should report what changed, what it intentionally did not change, what still needs clarification, and what verification it performed.

Optional prompt controls:

- `--scope-note "..."` adds an explicit scope guardrail. Repeat it for multiple notes.
- `--non-goal "..."` adds an explicit non-goal. Repeat it for multiple non-goals.
- `--no-strict-scope` disables the wrapper and sends the raw prompt. Prefer this only for unusual cases where the default contract would get in the way.

## Workflow

### API-first workflow

Use the bundled script for repeatable automation:

```bash
python3 scripts/jules_api.py list-sources

python3 scripts/jules_api.py repo-to-source --repo OWNER/REPO --compact

python3 scripts/jules_api.py doctor --compact

python3 scripts/jules_api.py create-session \
  --source sources/github/OWNER/REPO \
  --branch main \
  --title "Add regression tests" \
  --prompt "Add regression tests for the login redirect bug." \
  --scope-note "Stay within the login redirect flow and its tests." \
  --non-goal "Do not refactor unrelated auth helpers." \
  --require-plan-approval

python3 scripts/jules_api.py wait --session sessions/1234567890

python3 scripts/jules_api.py approve-plan --session sessions/1234567890

python3 scripts/jules_api.py send-message \
  --session sessions/1234567890 \
  --prompt "Keep the patch small and add one focused test." \
  --non-goal "Do not broaden into unrelated cleanup."

python3 scripts/jules_api.py resume \
  --session sessions/1234567890 \
  --prompt "Continue and keep the diff under 200 lines." \
  --scope-note "Only continue within the approved task."

python3 scripts/jules_api.py export \
  --session sessions/1234567890 \
  --kind summary \
  --output jules-session-summary.json

python3 scripts/jules_api.py list-active-sessions --repo-filter owner/repo --include-merge-status

python3 scripts/jules_api.py gh-auth-check --compact

python3 scripts/jules_api.py stale-session-report --repo-filter owner/repo --stale-after-hours 24

python3 scripts/jules_api.py cleanup-report --repo-filter owner/repo --require-all-merged --markdown

python3 scripts/jules_api.py list-merged-sessions --repo-filter owner/repo --require-all-merged

python3 scripts/jules_api.py close-ready-report --repo-filter owner/repo --require-all-merged --markdown

python3 scripts/jules_api.py list-unmerged-sessions --repo-filter owner/repo

python3 scripts/jules_api.py notify-close-plan --session sessions/1234567890 --markdown

python3 scripts/jules_api.py check-merge-status --session sessions/1234567890

python3 scripts/jules_api.py check-pr-readiness --session sessions/1234567890

python3 scripts/jules_api.py request-pr-rework --session sessions/1234567890 --markdown

python3 scripts/jules_api.py summary --session sessions/1234567890
```

Notes:

- `doctor --compact` separates `api_key`, `api_validated`, `api_ready`, `cli_ready`, and `merge_ready`.
- `api_key=yes` only means the key is present. Use `doctor --compact --validate-api` when you need to prove that the key can authenticate.
- Aggregated list/report commands collect all pages by default. `--page-token` is a starting point for aggregation, not a single-page mode.

### CLI workflow

Use the official CLI when it is already installed or when the current repo should be inferred automatically:

```bash
jules remote list --repo
jules remote new --repo . --session "Add regression tests for the login redirect bug"
jules remote list --session
jules remote pull --session 123456
```

## Practical Examples

### Example: Start a new fix in Jules

User intent:

```text
Ask Jules to fix the flaky login redirect test in owner/repo.
```

Suggested flow:

```bash
python3 scripts/jules_api.py doctor --compact
python3 scripts/jules_api.py list-sources

python3 scripts/jules_api.py create-session \
  --source sources/github/owner/repo \
  --branch main \
  --title "Fix flaky login redirect test" \
  --prompt "Investigate and fix the flaky login redirect test. Keep the patch focused and add or update tests." \
  --scope-note "Stay within the login redirect path and related tests." \
  --non-goal "Do not refactor unrelated auth code." \
  --require-plan-approval

python3 scripts/jules_api.py wait --session sessions/SESSION_ID
python3 scripts/jules_api.py summary --session sessions/SESSION_ID
```

What to report back:

- The Jules session URL
- Whether the session is planning, waiting for approval, in progress, or completed
- The latest plan or agent message

### Example: Approve a plan and let Jules continue

User intent:

```text
Approve the current Jules plan and let it continue.
```

Suggested flow:

```bash
python3 scripts/jules_api.py summary --session sessions/SESSION_ID
python3 scripts/jules_api.py approve-plan --session sessions/SESSION_ID
python3 scripts/jules_api.py wait --session sessions/SESSION_ID
```

Use `resume` instead when you want one helper command that can approve a pending plan automatically:

```bash
python3 scripts/jules_api.py resume --session sessions/SESSION_ID
```

### Example: Reply to a Jules clarification request

User intent:

```text
Tell Jules to keep the diff under 300 lines and avoid schema changes.
```

Suggested flow:

```bash
python3 scripts/jules_api.py summary --session sessions/SESSION_ID

python3 scripts/jules_api.py send-message \
  --session sessions/SESSION_ID \
  --prompt "Continue, keep the diff under 300 lines, and avoid schema changes." \
  --non-goal "Do not turn this into a broader cleanup."

python3 scripts/jules_api.py wait --session sessions/SESSION_ID
```

If the session is paused or explicitly waiting for feedback, `resume` can send the follow-up instruction in one step:

```bash
python3 scripts/jules_api.py resume \
  --session sessions/SESSION_ID \
  --prompt "Continue, keep the diff under 300 lines, and avoid schema changes." \
  --scope-note "Only continue within the approved plan."
```

### Example: Export the latest Jules result for another tool

User intent:

```text
Export the latest Jules session summary as JSON.
```

Suggested flow:

```bash
python3 scripts/jules_api.py export \
  --session sessions/SESSION_ID \
  --kind summary \
  --output jules-summary.json
```

Use `--kind activities` when another tool needs the full recent activity log. Use `--kind outputs` when the user only wants generated outputs such as PR-related metadata.

### Example: Stop a session that should not continue

User intent:

```text
Cancel the current Jules run.
```

Suggested flow:

```bash
python3 scripts/jules_api.py summary --session sessions/SESSION_ID
```

State clearly that cancel is implemented as session deletion and is not a reversible pause. After explicit user confirmation, run:

```bash
python3 scripts/jules_api.py cancel-session \
  --session sessions/SESSION_ID \
  --confirm-delete DELETE_JULES_SESSION
```

### Example: Check active sessions and close a merged one safely

User intent:

```text
Show active Jules sessions. If one already merged, ask me first and then close it.
```

Suggested flow:

```bash
python3 scripts/jules_api.py gh-auth-check --compact
python3 scripts/jules_api.py list-merged-sessions --repo-filter owner/repo --require-all-merged
python3 scripts/jules_api.py check-merge-status --session sessions/SESSION_ID
```

After that, ask the user for confirmation before closing. Only then run:

```bash
python3 scripts/jules_api.py notify-close-plan --session sessions/SESSION_ID --markdown

python3 scripts/jules_api.py close-merged-session \
  --session sessions/SESSION_ID \
  --confirm-close CLOSE_MERGED_SESSION
```

If the session can emit multiple PR URLs, prefer:

```bash
python3 scripts/jules_api.py close-merged-session \
  --session sessions/SESSION_ID \
  --require-all-merged \
  --confirm-close CLOSE_MERGED_SESSION
```

Do not skip the user-confirmation step. The command intentionally refuses to close without the explicit safety token.

### Example: Show all sessions whose work is not merged yet

User intent:

```text
Show me all Jules sessions whose PRs are not merged yet.
```

Suggested flow:

```bash
python3 scripts/jules_api.py list-unmerged-sessions --repo-filter owner/repo
```

If you also want sessions that never produced a PR URL yet:

```bash
python3 scripts/jules_api.py list-unmerged-sessions --repo-filter owner/repo --include-without-pr
```

Use this before cleanup so you do not accidentally close work that is still open on GitHub.

### Example: Show only closeable merged-session candidates

User intent:

```text
Show me Jules sessions that already finished through merged PRs.
```

Suggested flow:

```bash
python3 scripts/jules_api.py list-merged-sessions --repo-filter owner/repo --require-all-merged
```

Use this as the first step before asking the user which merged session should be closed.

`close-ready-report` may also include `cautionCandidates` when some PRs are merged but the session is not fully safe to close yet, for example because not all PRs are merged or GitHub status could not be resolved.
Do not close `cautionCandidates` by default. Use manual review first, and only use `--allow-caution-close` as an explicit override after user approval.

### Example: Generate one cleanup overview before taking action

User intent:

```text
Show me which Jules sessions are ready to close, which are still unmerged, and which never opened a PR.
```

Suggested flow:

```bash
python3 scripts/jules_api.py cleanup-report --repo-filter owner/repo --require-all-merged --markdown
```

Use this as the default operational overview before cleanup. It groups sessions into:

- `mergedCandidates`
- `cautionCandidates`
- `unmergedSessions`
- `withoutPullRequest`

Use `--compact` when another script only needs the counts.

### Example: Find stale open sessions

User intent:

```text
Show me open Jules sessions that have been stuck for more than a day.
```

Suggested flow:

```bash
python3 scripts/jules_api.py stale-session-report --repo-filter owner/repo --stale-after-hours 24
```

Add `--include-merge-status` when you also want to know whether those stale sessions already produced merged PRs.

Use `--repo-filter owner/repo` on reporting commands whenever the user is asking about one repository, not the full Jules account.

### Example: Generate a user confirmation message before closing

User intent:

```text
Prepare the confirmation message for closing this merged Jules session.
```

Suggested flow:

```bash
python3 scripts/jules_api.py notify-close-plan --session sessions/SESSION_ID
```

Use the returned `message` as the user-facing confirmation text. Only run `close-merged-session` after the user clearly approves it.

### Example: Ask Jules to rework a PR that is not merge-ready

User intent:

```text
Check whether the PR is merge-ready. If not, prepare a follow-up message for Jules.
```

Suggested flow:

```bash
python3 scripts/jules_api.py check-pr-readiness --session sessions/SESSION_ID
python3 scripts/jules_api.py request-pr-rework \
  --session sessions/SESSION_ID \
  --non-goal "Do not broaden beyond the current PR blockers." \
  --markdown
```

If you already want to send the rework request back to Jules:

```bash
python3 scripts/jules_api.py request-pr-rework \
  --session sessions/SESSION_ID \
  --extra-instruction "Keep the fix minimal and preserve the existing branch." \
  --scope-note "Only make the minimum changes needed for this PR." \
  --send
```

### Example: Check GitHub auth before merge-aware reports

User intent:

```text
Make sure merge checks will work before we run cleanup.
```

Suggested flow:

```bash
python3 scripts/jules_api.py gh-auth-check --compact
```

If authentication is missing, fix `gh` login before relying on merged/unmerged session reports.

### Example: Show only closeable sessions with ready-to-send close messages

User intent:

```text
Show me close-ready Jules sessions and the exact confirmation text to send.
```

Suggested flow:

```bash
python3 scripts/jules_api.py close-ready-report --repo-filter owner/repo --require-all-merged --markdown
```

## Decision Rules

- Prefer the API helper for non-interactive automation, scripting, or when the session id and source name must be captured programmatically.
- Prefer the CLI for human-driven terminal workflows, quick repo inference from the current directory, or pulling a completed patch into the local checkout.
- Use `summary` or `list-activities` before responding so the user gets the latest agent-visible state, not just the initial session creation response.
- Treat Jules as asynchronous. After `create-session`, `send-message`, or `approve-plan`, poll for updated activities instead of assuming immediate textual output.
- Prompts sent through the API helper are strict-scope by default. Use that default unless there is a clear reason to opt out.
- Treat strict-scope as both a simplicity rule and a surgical-change rule: minimum necessary patch, minimum necessary blast radius.
- If the user gives only an owner/repo pair and not a Jules source resource name, resolve it with `list-sources` first.
- If `AWAITING_PLAN_APPROVAL` appears, surface the plan and explicitly approve it only when the user asked to continue or the task clearly implies execution should proceed.
- If the session reaches `AWAITING_USER_FEEDBACK`, send a concise clarifying instruction instead of creating a new session.
- Use `resume` as a convenience helper only. It is not a first-class Jules API verb; it infers the right next step from the session state.
- Use `--scope-note` when a file area, subsystem, or execution boundary must be stated explicitly.
- Use `--non-goal` when you need to forbid refactors, cleanup, dependency changes, schema changes, or other adjacent work.
- If the task is ambiguous, prefer a follow-up question over a broader instruction.
- Prefer goal-driven follow-ups with explicit verification targets over vague “improve this” style prompts.
- Treat `delete-session` and `cancel-session` as destructive. They map to irreversible session deletion, not a reversible pause, and require explicit user confirmation plus `--confirm-delete DELETE_JULES_SESSION`.
- For merged-work cleanup, always follow this order: inspect session, verify merged PR status, ask the user, then run `close-merged-session`.
- Use `--require-all-merged` when the session output contains more than one pull request URL.
- Use `list-unmerged-sessions` when the user wants a single view of work that is still open on GitHub.
- Use `list-merged-sessions --require-all-merged` when the user wants a shortlist of closeable cleanup candidates.
- Use `cleanup-report --require-all-merged` when the user wants one report that separates closeable sessions, still-open work, and sessions without PR output.
- Use `stale-session-report` when the user wants to find open sessions that may need follow-up or manual cleanup.
- Use `notify-close-plan` before `close-merged-session` so the user sees a precise confirmation message with merged PR evidence.
- Prefer `--repo-filter owner/repo` on reporting commands when the request is scoped to one GitHub repository.
- Use `gh-auth-check` before merge-aware cleanup commands when GitHub authentication might be missing or stale.
- Use `close-ready-report` when the user wants close candidates plus ready-made close confirmation text in one step.
- Prefer `--markdown` for human review and `--compact` for scripting or automation chaining.
- Prefer a local `.env` file over shell profile edits for `JULES_API_KEY`. The script auto-loads `.env` from the current working directory or the skill root.
- Use `doctor` before the first live run to inspect `.env`, `JULES_API_KEY`, `gh`, and `jules` CLI readiness in one place. Add `--validate-api` when API credential validity matters.
- Use `repo-to-source` when the user gives only `owner/repo` and you need the exact Jules source resource name.
- Use `check-pr-readiness` before cleanup when you need to know whether a PR is actually merge-ready, not just merged or open.
- Use `request-pr-rework` when GitHub reports blockers such as merge conflicts, failed checks, or requested changes and you want a follow-up message for Jules.
- If Jules returns quota or rate-limit errors, report the failure clearly. Do not invent a remaining-usage number when the API does not provide one.
- Treat `cautionCandidates` as review-required items. They are not safe close targets by default.

## Script Reference

The bundled script lives at `scripts/jules_api.py` and supports:

- `list-active-sessions`
- `gh-auth-check`
- `stale-session-report`
- `cleanup-report`
- `close-ready-report`
- `list-merged-sessions`
- `list-unmerged-sessions`
- `list-sources`
- `list-sessions`
- `delete-session`
- `cancel-session`
- `get-session`
- `create-session`
- `send-message`
- `approve-plan`
- `list-activities`
- `get-activity`
- `resume`
- `wait`
- `summary`
- `export`
- `check-merge-status`
- `check-pr-readiness`
- `request-pr-rework`
- `notify-close-plan`
- `close-merged-session`

Run `python3 scripts/jules_api.py --help` or `python3 scripts/jules_api.py <command> --help` for flags.

Destructive commands intentionally require safety tokens:

- `delete-session` and `cancel-session`: `--confirm-delete DELETE_JULES_SESSION`
- `close-merged-session`: `--confirm-close CLOSE_MERGED_SESSION`

## Credential Setup

Create a `.env` file and add:

```text
JULES_API_KEY=your_jules_api_key
```

You can start from `.env.example`.

`.gitignore` excludes `.env`, so the real key file is less likely to be committed by accident.

The script auto-loads `.env` from the current working directory first, then from the skill root.

## Read More Only When Needed

- Read `references/jules-reference.md` when you need the API/CLI mapping, common states, or troubleshooting guidance.
