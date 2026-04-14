#!/usr/bin/env python3
"""Minimal CLI for the Jules REST API."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_BASE_URL = os.environ.get("JULES_API_BASE_URL", "https://jules.googleapis.com/v1alpha")
DEFAULT_TIMEOUT_SECONDS = 60 * 20
ACTIVE_STATES = {"QUEUED", "PLANNING", "IN_PROGRESS", "PAUSED"}
WAITING_STATES = {"AWAITING_PLAN_APPROVAL", "AWAITING_USER_FEEDBACK"}
TERMINAL_STATES = {"FAILED", "COMPLETED"}
OPEN_STATES = ACTIVE_STATES | WAITING_STATES
PR_URL_RE = re.compile(r"https://github\.com/[^/\s]+/[^/\s]+/pull/\d+")
CLOSE_CONFIRM_TOKEN = "CLOSE_MERGED_SESSION"
SUCCESSFUL_CHECK_CONCLUSIONS = {"SUCCESS", "NEUTRAL", "SKIPPED"}
FAILED_CHECK_CONCLUSIONS = {"FAILURE", "TIMED_OUT", "CANCELLED", "STARTUP_FAILURE", "ACTION_REQUIRED", "STALE"}
PENDING_CHECK_STATUSES = {"EXPECTED", "IN_PROGRESS", "PENDING", "QUEUED", "REQUESTED", "WAITING"}
ENV_FILE_CANDIDATES = [
    Path.cwd() / ".env",
    Path(__file__).resolve().parent.parent / ".env",
]


def fail(message: str, exit_code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(exit_code)


def find_dotenv_path() -> Path | None:
    for candidate in ENV_FILE_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


def load_dotenv() -> None:
    dotenv_path = find_dotenv_path()
    if dotenv_path is None:
        return
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = value


def get_api_key() -> str:
    api_key = os.environ.get("JULES_API_KEY", "").strip()
    if not api_key:
        fail("JULES_API_KEY is required. Put it in a .env file or export it in the shell first.")
    return api_key


def normalize_session_name(value: str) -> str:
    value = value.strip()
    if not value:
        fail("Session identifier is required.")
    if value.startswith("sessions/"):
        return value
    return f"sessions/{value}"


def normalize_repeated_argument(values: Any) -> list[str]:
    if not values:
        return []
    if isinstance(values, str):
        values = [values]
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        item = value.strip()
        if item:
            normalized.append(item)
    return normalized


def build_strict_scope_prompt(
    user_prompt: str,
    *,
    scope_notes: list[str] | None = None,
    non_goals: list[str] | None = None,
    continue_existing_scope: bool = False,
    limit_to_current_pr: bool = False,
) -> str:
    task = user_prompt.strip()
    if not task:
        fail("Prompt text is required.")

    lines = [
        "You are working under a strict scoped task.",
        "",
        "Primary task:",
        task,
        "",
        "Operating rules:",
    ]

    if continue_existing_scope:
        lines.append("- Continue only within the existing approved task scope.")
    if limit_to_current_pr:
        lines.append("- Only make the minimum changes required to make the current pull request merge-ready.")

    lines.extend(
        [
            "- Interpret the request as narrowly as possible.",
            "- Do not expand scope on your own.",
            "- Do not do unrelated cleanup, refactoring, optimization, or restructuring unless explicitly requested.",
            "- If a change outside the stated scope appears necessary, stop and ask a question first.",
            "- If multiple interpretations are possible, do not choose the broader one. Ask a question.",
            "- Prefer the smallest patch that satisfies the stated task.",
            "- Keep existing behavior unchanged outside the requested area.",
        ]
    )

    normalized_scope_notes = normalize_repeated_argument(scope_notes)
    if normalized_scope_notes:
        lines.extend(["", "Scope notes:"])
        lines.extend([f"- {note}" for note in normalized_scope_notes])

    normalized_non_goals = normalize_repeated_argument(non_goals)
    if normalized_non_goals:
        lines.extend(["", "Non-goals:"])
        lines.extend([f"- {item}" for item in normalized_non_goals])

    lines.extend(
        [
            "",
            "Before finishing, report:",
            "- What changed",
            "- What you intentionally did not change",
            "- What needs clarification or follow-up",
        ]
    )
    return "\n".join(lines)


def build_prompt_from_args(
    args: argparse.Namespace,
    prompt: str,
    *,
    continue_existing_scope: bool = False,
    limit_to_current_pr: bool = False,
    extra_scope_notes: list[str] | None = None,
    extra_non_goals: list[str] | None = None,
) -> str:
    if getattr(args, "strict_scope", True) is False:
        return prompt

    scope_notes = normalize_repeated_argument(getattr(args, "scope_note", None))
    non_goals = normalize_repeated_argument(getattr(args, "non_goal", None))
    scope_notes.extend(normalize_repeated_argument(extra_scope_notes))
    non_goals.extend(normalize_repeated_argument(extra_non_goals))
    return build_strict_scope_prompt(
        prompt,
        scope_notes=scope_notes,
        non_goals=non_goals,
        continue_existing_scope=continue_existing_scope,
        limit_to_current_pr=limit_to_current_pr,
    )


def build_url(path: str, query: dict[str, Any] | None = None) -> str:
    path = path if path.startswith("/") else f"/{path}"
    url = f"{DEFAULT_BASE_URL}{path}"
    if query:
        filtered = {key: value for key, value in query.items() if value not in (None, "", False)}
        if filtered:
            url = f"{url}?{urllib.parse.urlencode(filtered)}"
    return url


def api_request(method: str, path: str, *, payload: dict[str, Any] | None = None, query: dict[str, Any] | None = None) -> Any:
    headers = {
        "x-goog-api-key": get_api_key(),
        "Accept": "application/json",
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(build_url(path, query), data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read().decode("utf-8").strip()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace").strip()
        fail(build_api_error_message(exc.code, body or str(exc.reason)))
    except urllib.error.URLError as exc:
        fail(f"Jules API request failed: {exc.reason}")

    if not raw:
        return {}
    return json.loads(raw)


def build_api_error_message(status_code: int, raw_body: str) -> str:
    parsed_message = raw_body
    parsed_status = None
    parsed_details = None

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        payload = None

    if isinstance(payload, dict):
        error = payload.get("error", {})
        if isinstance(error, dict):
            parsed_message = error.get("message") or parsed_message
            parsed_status = error.get("status")
            parsed_details = error.get("details")

    normalized = f"{status_code} {parsed_status or ''} {parsed_message}".lower()

    if status_code == 429 or "resource_exhausted" in normalized or "quota" in normalized or "rate limit" in normalized:
        return (
            "Jules API request failed due to usage or rate limits. "
            "The current public Jules API does not expose a reliable remaining-usage value here, "
            "so this command is failing safely instead of guessing. "
            f"HTTP {status_code}: {parsed_message}"
        )

    if status_code == 403 and any(token in normalized for token in ["permission", "access", "forbidden", "denied"]):
        return (
            "Jules API request was denied. Check that the current Google account has Jules access, "
            "that the repository is connected in Jules, and that the API key is valid for this account. "
            f"HTTP {status_code}: {parsed_message}"
        )

    if status_code == 401:
        return (
            "Jules API request was unauthorized. Check the JULES_API_KEY value in .env or the current shell. "
            f"HTTP {status_code}: {parsed_message}"
        )

    if status_code == 404:
        return f"Jules API request failed because the requested resource was not found. HTTP {status_code}: {parsed_message}"

    if parsed_details:
        return f"Jules API request failed: HTTP {status_code}: {parsed_message} | details={parsed_details}"
    return f"Jules API request failed: HTTP {status_code}: {parsed_message}"


def collect_paginated_resources(
    path: str,
    *,
    page_size: int,
    resource_key: str,
    page_token: str | None = None,
    extra_query: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    resources: list[dict[str, Any]] = []
    next_token = page_token
    first_iteration = True

    while first_iteration or next_token:
        first_iteration = False
        query = {"pageSize": page_size}
        if next_token:
            query["pageToken"] = next_token
        if extra_query:
            query.update(extra_query)
        response = api_request("GET", path, query=query)
        resources.extend(response.get(resource_key, []))
        next_token = response.get("nextPageToken")

    return resources, next_token


def collect_session_activities(
    session_name: str,
    *,
    page_size: int,
    page_token: str | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    return collect_paginated_resources(
        f"/{session_name}/activities",
        page_size=page_size,
        resource_key="activities",
        page_token=page_token,
    )


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False))


def print_text(value: str) -> None:
    print(value.rstrip())


def parse_rfc3339(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return dt.datetime.fromisoformat(normalized)
    except ValueError:
        return None


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def order_activities(activities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    minimum = dt.datetime.min.replace(tzinfo=dt.timezone.utc)

    def sort_key(item: tuple[int, dict[str, Any]]) -> tuple[dt.datetime, int]:
        index, activity = item
        created_at = parse_rfc3339(activity.get("createTime"))
        if created_at is None:
            return minimum, index
        return created_at.astimezone(dt.timezone.utc), index

    return [activity for _, activity in sorted(enumerate(activities), key=sort_key)]


def extract_repo_name(session: dict[str, Any]) -> str | None:
    source_context = session.get("sourceContext", {})
    source = source_context.get("source")
    if isinstance(source, str) and source:
        return source.removeprefix("sources/github/")
    return None


def session_matches_repo_filter(session: dict[str, Any], repo_filter: str | None) -> bool:
    if not repo_filter:
        return True
    return extract_repo_name(session) == repo_filter.strip()


def collect_gh_auth_status() -> dict[str, Any]:
    available = gh_is_available()
    payload: dict[str, Any] = {
        "installed": available,
        "authenticated": False,
    }
    if not available:
        payload["reason"] = "gh CLI is not installed."
        return payload

    try:
        result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, check=True)
        payload["authenticated"] = True
        payload["stdout"] = result.stdout.strip()
    except subprocess.CalledProcessError as exc:
        payload["stdout"] = (exc.stdout or "").strip()
        payload["stderr"] = (exc.stderr or "").strip()
    return payload


def collect_jules_cli_status() -> dict[str, Any]:
    cli_path = shutil.which("jules")
    payload: dict[str, Any] = {
        "installed": bool(cli_path),
        "path": cli_path,
        "authenticated": None,
        "authStatus": "not_installed" if not cli_path else "unknown",
        "ready": False,
    }
    if not cli_path:
        return payload

    try:
        result = subprocess.run(["jules", "version"], capture_output=True, text=True, check=True, timeout=15)
        payload["version"] = (result.stdout or result.stderr).strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        payload["versionError"] = (exc.stderr or exc.stdout).strip()

    try:
        probe = subprocess.run(
            ["jules", "remote", "list", "--repo"],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        payload["authenticated"] = True
        payload["authStatus"] = "authenticated"
        payload["authProbeOutput"] = (probe.stdout or probe.stderr).strip()
        payload["ready"] = True
        return payload
    except subprocess.TimeoutExpired:
        payload["authStatus"] = "unknown"
        payload["authProbeError"] = "Timed out while checking Jules CLI authentication."
        return payload
    except subprocess.CalledProcessError as exc:
        combined = " ".join(part for part in [(exc.stdout or "").strip(), (exc.stderr or "").strip()] if part).strip()
        normalized = combined.lower()
        if any(token in normalized for token in ["login", "log in", "sign in", "authenticate", "authentication", "not logged", "unauthorized"]):
            payload["authenticated"] = False
            payload["authStatus"] = "not_authenticated"
        else:
            payload["authStatus"] = "unknown"
        payload["authProbeError"] = combined or "Failed to determine Jules CLI authentication state."
        return payload


def format_session_line(session: dict[str, Any]) -> str:
    repo = session.get("repo") or "-"
    title = session.get("title") or "(untitled)"
    state = session.get("state") or "STATE_UNSPECIFIED"
    return f"- {session.get('name')} [{state}] {repo} :: {title}"


def format_cleanup_report_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Jules Cleanup Report",
        "",
        f"- Total scanned: {payload['summary']['totalSessionsScanned']}",
        f"- Merged candidates: {payload['summary']['mergedCandidateCount']}",
        f"- Caution: {payload['summary']['cautionCount']}",
        f"- Unmerged: {payload['summary']['unmergedCount']}",
        f"- Without PR: {payload['summary']['withoutPrCount']}",
        "",
        "## Merged Candidates",
    ]
    merged = payload.get("mergedCandidates", [])
    if merged:
        lines.extend(format_session_line(item) for item in merged)
    else:
        lines.append("- none")

    lines.extend(["", "## Caution"])
    caution = payload.get("cautionCandidates", [])
    if caution:
        lines.extend(format_session_line(item) for item in caution)
    else:
        lines.append("- none")

    lines.extend(["", "## Unmerged Sessions"])
    unmerged = payload.get("unmergedSessions", [])
    if unmerged:
        lines.extend(format_session_line(item) for item in unmerged)
    else:
        lines.append("- none")

    lines.extend(["", "## Without Pull Request"])
    without_pr = payload.get("withoutPullRequest", [])
    if without_pr:
        lines.extend(format_session_line(item) for item in without_pr)
    else:
        lines.append("- none")
    return "\n".join(lines)


def format_cleanup_report_compact(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return (
        f"scanned={summary['totalSessionsScanned']} "
        f"merged_candidates={summary['mergedCandidateCount']} "
        f"caution={summary['cautionCount']} "
        f"unmerged={summary['unmergedCount']} "
        f"without_pr={summary['withoutPrCount']}"
    )


def format_close_ready_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Jules Close-Ready Report",
        "",
        f"- Candidates: {payload['summary']['candidateCount']}",
        f"- Caution: {payload['summary']['cautionCount']}",
        "",
        "## Candidates",
    ]
    candidates = payload.get("candidates", [])
    if candidates:
        for item in candidates:
            lines.append(f"### {item.get('title') or item.get('name')}")
            lines.append(format_session_line(item))
            lines.append(f"- Close command: `{item.get('recommendedCommand')}`")
            lines.append(f"- Notify message: {item.get('message')}")
            lines.append("")
    else:
        lines.append("- none")

    caution_candidates = payload.get("cautionCandidates", [])
    if caution_candidates:
        lines.append("## Caution")
        for item in caution_candidates:
            lines.append(format_session_line(item))
            lines.append(
                f"- Reason: allMerged={item['closeReadiness'].get('allMerged')} "
                f"unknownPRs={item['closeReadiness'].get('unknownPullRequestCount')}"
            )
            lines.append("- Manual review required before any close override.")
            lines.append("")
    return "\n".join(lines)


def emit_output(payload: dict[str, Any], *, compact: bool = False, markdown: bool = False, compact_formatter=None, markdown_formatter=None) -> None:
    if markdown and markdown_formatter:
        print_text(markdown_formatter(payload))
        return
    if compact and compact_formatter:
        print_text(compact_formatter(payload))
        return
    print_json(payload)


def normalize_gh_state(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().upper()
    return normalized or None


def collect_status_check_blockers(checks: Any) -> list[str]:
    blockers: list[str] = []
    if not isinstance(checks, list):
        return blockers

    for check in checks:
        if not isinstance(check, dict):
            continue
        name = check.get("name") or check.get("context") or "status-check"
        status = normalize_gh_state(check.get("status"))
        conclusion = normalize_gh_state(check.get("conclusion"))

        if conclusion in FAILED_CHECK_CONCLUSIONS:
            blockers.append(f"{name}={conclusion}")
            continue

        if status in PENDING_CHECK_STATUSES:
            blockers.append(f"{name}={status}")
            continue

        if status == "COMPLETED" and conclusion not in SUCCESSFUL_CHECK_CONCLUSIONS:
            blockers.append(f"{name}={conclusion or 'UNKNOWN'}")
    return blockers


def build_close_command(
    session_name: str,
    *,
    allow_caution_close: bool = False,
    allow_unknown_pr_status: bool = False,
) -> str:
    parts = [
        "python3",
        "scripts/jules_api.py",
        "close-merged-session",
        "--session",
        session_name,
    ]
    if allow_caution_close:
        parts.append("--allow-caution-close")
    if allow_unknown_pr_status:
        parts.append("--allow-unknown-pr-status")
    parts.extend(["--confirm-close", CLOSE_CONFIRM_TOKEN])
    return " ".join(parts)


def build_aggregation_metadata(*, page_size: int, start_page_token: str | None) -> dict[str, Any]:
    return {
        "mode": "aggregate",
        "pageSize": page_size,
        "startPageToken": start_page_token,
        "fullyCollected": True,
    }


def add_aggregate_pagination_arguments(parser: argparse.ArgumentParser, *, default_page_size: int) -> None:
    parser.add_argument(
        "--page-size",
        type=int,
        default=default_page_size,
        help="API page size for each underlying request while aggregating all pages.",
    )
    parser.add_argument(
        "--page-token",
        help="Optional start token. The command will aggregate pages from this token onward.",
    )


def add_scope_control_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--scope-note",
        action="append",
        help="Optional extra scope guardrail to include in the Jules prompt. Repeat to add more than one.",
    )
    parser.add_argument(
        "--non-goal",
        action="append",
        help="Optional explicit non-goal to include in the Jules prompt. Repeat to add more than one.",
    )
    parser.add_argument(
        "--no-strict-scope",
        dest="strict_scope",
        action="store_false",
        help="Send the raw prompt without the default strict-scope wrapper.",
    )
    parser.set_defaults(strict_scope=True)


def list_active_sessions(args: argparse.Namespace) -> None:
    sessions, next_page_token = collect_paginated_resources(
        "/sessions",
        page_size=args.page_size,
        resource_key="sessions",
        page_token=args.page_token,
    )
    active_sessions = [
        summarize_session_brief(session, include_merge_status=args.include_merge_status)
        for session in sessions
        if session.get("state") in OPEN_STATES and session_matches_repo_filter(session, args.repo_filter)
    ]
    print_json(
        {
            "sessions": active_sessions,
            "pagination": build_aggregation_metadata(page_size=args.page_size, start_page_token=args.page_token),
            "nextPageToken": next_page_token,
        }
    )


def stale_session_report(args: argparse.Namespace) -> None:
    sessions, next_page_token = collect_paginated_resources(
        "/sessions",
        page_size=args.page_size,
        resource_key="sessions",
        page_token=args.page_token,
    )
    cutoff_hours = args.stale_after_hours
    now = utc_now()
    results = []

    for session in sessions:
        if not session_matches_repo_filter(session, args.repo_filter):
            continue
        state = session.get("state")
        if state not in OPEN_STATES:
            continue

        updated_at = parse_rfc3339(session.get("updateTime")) or parse_rfc3339(session.get("createTime"))
        if updated_at is None:
            continue

        stale_hours = (now - updated_at.astimezone(dt.timezone.utc)).total_seconds() / 3600
        if stale_hours < cutoff_hours:
            continue

        entry = {
            **summarize_session_brief(session),
            "staleHours": round(stale_hours, 2),
            "staleAfterHours": cutoff_hours,
        }
        if args.include_merge_status:
            entry["mergeStatus"] = build_merge_report(session)
        results.append(entry)

    print_json(
        {
            "summary": {
                "staleAfterHours": cutoff_hours,
                "staleSessionCount": len(results),
            },
            "sessions": results,
            "pagination": build_aggregation_metadata(page_size=args.page_size, start_page_token=args.page_token),
            "nextPageToken": next_page_token,
        }
    )


def list_unmerged_sessions(args: argparse.Namespace) -> None:
    sessions, next_page_token = collect_paginated_resources(
        "/sessions",
        page_size=args.page_size,
        resource_key="sessions",
        page_token=args.page_token,
    )
    results = []

    for session in sessions:
        if not session_matches_repo_filter(session, args.repo_filter):
            continue
        report = build_merge_report(session)
        if not report["hasPullRequest"] and not args.include_without_pr:
            continue

        unresolved = [item for item in report["pullRequests"] if item.get("status") != "merged"]
        if not unresolved and report["hasPullRequest"]:
            continue

        if not report["hasPullRequest"] and args.include_without_pr:
            unresolved = [{"status": "no_pr", "reason": "No pull request URL found in session outputs."}]

        results.append(
            {
                **summarize_session_brief(session),
                "mergeStatus": {
                    "hasPullRequest": report["hasPullRequest"],
                    "unmergedPullRequests": unresolved,
                    "allMerged": report["allMerged"],
                },
            }
        )

    print_json(
        {
            "sessions": results,
            "pagination": build_aggregation_metadata(page_size=args.page_size, start_page_token=args.page_token),
            "nextPageToken": next_page_token,
        }
    )


def list_merged_sessions(args: argparse.Namespace) -> None:
    sessions, next_page_token = collect_paginated_resources(
        "/sessions",
        page_size=args.page_size,
        resource_key="sessions",
        page_token=args.page_token,
    )
    results = []

    for session in sessions:
        if not session_matches_repo_filter(session, args.repo_filter):
            continue
        report = build_merge_report(session)
        if not report["mergedPullRequests"]:
            continue
        if args.require_all_merged and not report["allMerged"]:
            continue

        results.append(
            {
                **summarize_session_brief(session),
                "mergeStatus": {
                    "hasPullRequest": report["hasPullRequest"],
                    "mergedPullRequests": report["mergedPullRequests"],
                    "allMerged": report["allMerged"],
                },
            }
        )

    print_json(
        {
            "sessions": results,
            "pagination": build_aggregation_metadata(page_size=args.page_size, start_page_token=args.page_token),
            "nextPageToken": next_page_token,
        }
    )


def cleanup_report(args: argparse.Namespace) -> None:
    sessions, next_page_token = collect_paginated_resources(
        "/sessions",
        page_size=args.page_size,
        resource_key="sessions",
        page_token=args.page_token,
    )
    merged_candidates = []
    unmerged_sessions = []
    without_pr_sessions = []
    caution_sessions = []
    scanned_sessions = 0

    for session in sessions:
        if not session_matches_repo_filter(session, args.repo_filter):
            continue
        scanned_sessions += 1
        brief = summarize_session_brief(session)
        report = build_merge_report(session)
        close_readiness = summarize_session_close_readiness(session, report)

        if not report["hasPullRequest"]:
            without_pr_sessions.append(
                {
                    **brief,
                    "closeReadiness": close_readiness,
                    "mergeStatus": {
                        "hasPullRequest": False,
                        "reason": "No pull request URL found in session outputs.",
                    },
                }
            )
            continue

        if report["mergedPullRequests"]:
            if close_readiness["closeReady"] and (not args.require_all_merged or report["allMerged"]):
                merged_candidates.append(
                    {
                        **brief,
                        "closeReadiness": close_readiness,
                        "mergeStatus": {
                            "hasPullRequest": True,
                            "mergedPullRequests": report["mergedPullRequests"],
                            "allMerged": report["allMerged"],
                        },
                    }
                )
            elif close_readiness["caution"]:
                caution_sessions.append(
                    {
                        **brief,
                        "closeReadiness": close_readiness,
                        "mergeStatus": {
                            "hasPullRequest": True,
                            "mergedPullRequests": report["mergedPullRequests"],
                            "allMerged": report["allMerged"],
                        },
                    }
                )

        unresolved = [item for item in report["pullRequests"] if item.get("status") != "merged"]
        if unresolved:
            unmerged_sessions.append(
                {
                    **brief,
                    "closeReadiness": close_readiness,
                    "mergeStatus": {
                        "hasPullRequest": True,
                        "unmergedPullRequests": unresolved,
                        "allMerged": report["allMerged"],
                    },
                }
            )

    payload = {
        "summary": {
            "totalSessionsScanned": scanned_sessions,
            "mergedCandidateCount": len(merged_candidates),
            "cautionCount": len(caution_sessions),
            "unmergedCount": len(unmerged_sessions),
            "withoutPrCount": len(without_pr_sessions),
        },
        "mergedCandidates": merged_candidates,
        "cautionCandidates": caution_sessions,
        "unmergedSessions": unmerged_sessions,
        "withoutPullRequest": without_pr_sessions,
        "pagination": build_aggregation_metadata(page_size=args.page_size, start_page_token=args.page_token),
        "nextPageToken": next_page_token,
    }
    emit_output(
        payload,
        compact=args.compact,
        markdown=args.markdown,
        compact_formatter=format_cleanup_report_compact,
        markdown_formatter=format_cleanup_report_markdown,
    )


def close_ready_report(args: argparse.Namespace) -> None:
    sessions, next_page_token = collect_paginated_resources(
        "/sessions",
        page_size=args.page_size,
        resource_key="sessions",
        page_token=args.page_token,
    )
    candidates = []
    caution_candidates = []

    for session in sessions:
        if not session_matches_repo_filter(session, args.repo_filter):
            continue
        report = build_merge_report(session)
        close_readiness = summarize_session_close_readiness(session, report)
        if not report["mergedPullRequests"]:
            continue

        brief = summarize_session_brief(session)
        session_name = normalize_session_name(session.get("name", ""))
        recommended_command = build_close_command(session_name)
        item = {
            **brief,
            "closeReadiness": close_readiness,
            "mergeStatus": report,
            "message": build_close_message(session_name, brief, report, recommended_command=recommended_command),
            "recommendedCommand": recommended_command,
        }

        if close_readiness["closeReady"] and (not args.require_all_merged or report["allMerged"]):
            candidates.append(item)
        elif close_readiness["caution"]:
            caution_candidates.append(item)

    payload = {
        "summary": {
            "candidateCount": len(candidates),
            "cautionCount": len(caution_candidates),
        },
        "candidates": candidates,
        "cautionCandidates": caution_candidates,
        "pagination": build_aggregation_metadata(page_size=args.page_size, start_page_token=args.page_token),
        "nextPageToken": next_page_token,
    }
    emit_output(
        payload,
        compact=args.compact,
        markdown=args.markdown,
        compact_formatter=format_close_ready_compact,
        markdown_formatter=format_close_ready_markdown,
    )


def notify_close_plan(args: argparse.Namespace) -> None:
    session_name = normalize_session_name(args.session)
    session = api_request("GET", f"/{session_name}")
    report = build_merge_report(session)
    close_readiness = summarize_session_close_readiness(session, report)
    brief = summarize_session_brief(session)

    merged_prs = report["mergedPullRequests"]
    if not merged_prs:
        fail("No merged pull request was found for this session, so a close notification plan cannot be generated safely.")
    if close_readiness["caution"] and not args.allow_caution_close:
        fail(
            "This session is a caution close candidate. Review unresolved or unknown PR state first, "
            "or rerun with --allow-caution-close after explicit user approval."
        )
    if close_readiness["unknownPullRequestCount"] > 0 and not args.allow_unknown_pr_status:
        fail("Some pull requests have unknown GitHub status. Refusing to build a close plan unless --allow-unknown-pr-status is provided.")

    recommended_command = build_close_command(
        session_name,
        allow_caution_close=args.allow_caution_close,
        allow_unknown_pr_status=args.allow_unknown_pr_status,
    )
    payload = {
        "session": brief,
        "mergeStatus": report,
        "closeReadiness": close_readiness,
        "message": build_close_message(session_name, brief, report, recommended_command=recommended_command),
        "recommendedCommand": recommended_command,
    }
    if args.markdown:
        print_text(payload["message"])
        return
    print_json(payload)


def list_sources(args: argparse.Namespace) -> None:
    sources, next_page_token = collect_paginated_resources(
        "/sources",
        page_size=args.page_size,
        resource_key="sources",
        page_token=args.page_token,
        extra_query={"filter": args.filter},
    )
    print_json(
        {
            "sources": sources,
            "pagination": build_aggregation_metadata(page_size=args.page_size, start_page_token=args.page_token),
            "nextPageToken": next_page_token,
        }
    )


def repo_to_source(args: argparse.Namespace) -> None:
    repo = args.repo.strip()
    if not repo or "/" not in repo:
        fail("Use --repo owner/repo.")
    sources, next_page_token = collect_paginated_resources(
        "/sources",
        page_size=args.page_size,
        resource_key="sources",
        page_token=args.page_token,
    )
    matches = [source for source in sources if source.get("name") == f"sources/github/{repo}"]

    if not matches and args.allow_contains:
        matches = [source for source in sources if repo in source.get("name", "")]

    payload = {
        "repo": repo,
        "matches": matches,
        "count": len(matches),
        "pagination": build_aggregation_metadata(page_size=args.page_size, start_page_token=args.page_token),
        "nextPageToken": next_page_token,
    }

    if args.compact:
        if matches:
            print_text(matches[0].get("name", ""))
            return
        print_text("")
        return
    print_json(payload)


def list_sessions(args: argparse.Namespace) -> None:
    sessions, next_page_token = collect_paginated_resources(
        "/sessions",
        page_size=args.page_size,
        resource_key="sessions",
        page_token=args.page_token,
    )
    print_json(
        {
            "sessions": sessions,
            "pagination": build_aggregation_metadata(page_size=args.page_size, start_page_token=args.page_token),
            "nextPageToken": next_page_token,
        }
    )


def delete_session(args: argparse.Namespace) -> None:
    session_name = normalize_session_name(args.session)
    api_request("DELETE", f"/{session_name}")
    print(json.dumps({"ok": True, "deleted": session_name}, ensure_ascii=False))


def get_session(args: argparse.Namespace) -> None:
    response = api_request("GET", f"/{normalize_session_name(args.session)}")
    print_json(response)


def create_session(args: argparse.Namespace) -> None:
    payload: dict[str, Any] = {
        "prompt": build_prompt_from_args(args, args.prompt),
        "sourceContext": {
            "source": args.source,
            "githubRepoContext": {
                "startingBranch": args.branch,
            },
        },
    }
    if args.title:
        payload["title"] = args.title
    if args.require_plan_approval:
        payload["requirePlanApproval"] = True
    if args.automation_mode:
        payload["automationMode"] = args.automation_mode
    response = api_request("POST", "/sessions", payload=payload)
    print_json(response)


def send_message(args: argparse.Namespace) -> None:
    api_request(
        "POST",
        f"/{normalize_session_name(args.session)}:sendMessage",
        payload={"prompt": build_prompt_from_args(args, args.prompt, continue_existing_scope=True)},
    )
    print(json.dumps({"ok": True, "session": normalize_session_name(args.session)}, ensure_ascii=False))


def approve_plan(args: argparse.Namespace) -> None:
    api_request("POST", f"/{normalize_session_name(args.session)}:approvePlan", payload={})
    print(json.dumps({"ok": True, "session": normalize_session_name(args.session)}, ensure_ascii=False))


def list_activities(args: argparse.Namespace) -> None:
    activities, next_page_token = collect_session_activities(
        normalize_session_name(args.session),
        page_size=args.page_size,
        page_token=args.page_token,
    )
    print_json(
        {
            "activities": activities,
            "pagination": build_aggregation_metadata(page_size=args.page_size, start_page_token=args.page_token),
            "nextPageToken": next_page_token,
        }
    )


def get_activity(args: argparse.Namespace) -> None:
    session_name = normalize_session_name(args.session)
    activity_name = args.activity.strip()
    if not activity_name:
        fail("Activity identifier is required.")
    if activity_name.startswith("sessions/"):
        resource_name = activity_name
    else:
        resource_name = f"{session_name}/activities/{activity_name}"
    response = api_request("GET", f"/{resource_name}")
    print_json(response)


def wait_for_session(args: argparse.Namespace) -> None:
    session_name = normalize_session_name(args.session)
    deadline = time.time() + args.timeout

    while True:
        session = api_request("GET", f"/{session_name}")
        state = session.get("state", "STATE_UNSPECIFIED")

        if args.verbose:
            print_json({"name": session.get("name"), "state": state, "updateTime": session.get("updateTime"), "url": session.get("url")})

        if state in TERMINAL_STATES or state in WAITING_STATES:
            print_json(session)
            return

        if time.time() >= deadline:
            fail(f"Timed out while waiting for {session_name}. Last state: {state}")

        time.sleep(args.interval)


def find_pr_urls(value: Any) -> list[str]:
    found: set[str] = set()

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            for child in node.values():
                visit(child)
            return
        if isinstance(node, list):
            for child in node:
                visit(child)
            return
        if isinstance(node, str):
            for match in PR_URL_RE.findall(node):
                found.add(match.rstrip(".,)"))

    visit(value)
    return sorted(found)


def gh_is_available() -> bool:
    return shutil.which("gh") is not None


def gh_auth_check(args: argparse.Namespace) -> None:
    gh_status = collect_gh_auth_status()
    payload: dict[str, Any] = {
        "ghInstalled": gh_status["installed"],
        "authenticated": gh_status["authenticated"],
        "stdout": gh_status.get("stdout", ""),
        "stderr": gh_status.get("stderr", ""),
        "reason": gh_status.get("reason", ""),
    }

    if args.compact:
        state = "ok" if payload["authenticated"] else "not_authenticated"
        print_text(f"gh_installed={str(payload['ghInstalled']).lower()} gh_auth={state}")
        return
    print_json(payload)


def fetch_pr_status(pr_url: str) -> dict[str, Any]:
    if not gh_is_available():
        return {"url": pr_url, "status": "unknown", "reason": "gh CLI is not installed."}

    command = [
        "gh",
        "pr",
        "view",
        pr_url,
        "--json",
        "number,state,mergedAt,title,url,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        return {"url": pr_url, "status": "unknown", "reason": stderr or "Failed to query GitHub PR status via gh."}

    payload = json.loads(result.stdout)
    merged = bool(payload.get("mergedAt"))
    return {
        "url": payload.get("url", pr_url),
        "number": payload.get("number"),
        "title": payload.get("title"),
        "state": payload.get("state"),
        "mergedAt": payload.get("mergedAt"),
        "merged": merged,
        "status": "merged" if merged else "not_merged",
        "mergeable": payload.get("mergeable"),
        "mergeStateStatus": payload.get("mergeStateStatus"),
        "reviewDecision": payload.get("reviewDecision"),
        "statusCheckRollup": payload.get("statusCheckRollup"),
    }


def is_pr_merge_ready(pr: dict[str, Any]) -> bool:
    if pr.get("merged"):
        return True
    if pr.get("status") == "unknown":
        return False
    if pr.get("mergeable") not in ("MERGEABLE", True):
        return False
    if pr.get("reviewDecision") == "CHANGES_REQUESTED":
        return False

    merge_state = pr.get("mergeStateStatus")
    if merge_state in {"DIRTY", "BEHIND", "BLOCKED", "DRAFT", "HAS_HOOKS", "UNKNOWN", "UNSTABLE"}:
        return False

    return not collect_status_check_blockers(pr.get("statusCheckRollup"))


def summarize_pr_merge_readiness(pr: dict[str, Any]) -> dict[str, Any]:
    if pr.get("merged"):
        return {
            "number": pr.get("number"),
            "title": pr.get("title"),
            "url": pr.get("url"),
            "ready": True,
            "mergeable": pr.get("mergeable"),
            "mergeStateStatus": pr.get("mergeStateStatus"),
            "reviewDecision": pr.get("reviewDecision"),
            "blockers": [],
        }

    ready = is_pr_merge_ready(pr)
    blockers: list[str] = []

    if pr.get("status") == "unknown":
        blockers.append(pr.get("reason", "PR status is unknown."))
    if pr.get("mergeable") not in ("MERGEABLE", True):
        blockers.append(f"mergeable={pr.get('mergeable')}")
    merge_state = pr.get("mergeStateStatus")
    if merge_state in {"DIRTY", "BEHIND", "BLOCKED", "DRAFT", "HAS_HOOKS", "UNKNOWN", "UNSTABLE"}:
        blockers.append(f"mergeStateStatus={merge_state}")
    review_decision = pr.get("reviewDecision")
    if review_decision == "CHANGES_REQUESTED":
        blockers.append("reviewDecision=CHANGES_REQUESTED")

    blockers.extend(collect_status_check_blockers(pr.get("statusCheckRollup")))

    return {
        "number": pr.get("number"),
        "title": pr.get("title"),
        "url": pr.get("url"),
        "ready": ready,
        "mergeable": pr.get("mergeable"),
        "mergeStateStatus": pr.get("mergeStateStatus"),
        "reviewDecision": pr.get("reviewDecision"),
        "blockers": blockers,
    }


def summarize_session_close_readiness(session: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    pull_requests = report.get("pullRequests", [])
    merged_pull_requests = report.get("mergedPullRequests", [])
    readiness = [summarize_pr_merge_readiness(pr) for pr in pull_requests]
    unknown_prs = [pr for pr in pull_requests if pr.get("status") == "unknown"]
    ready_prs = [item for item in readiness if item.get("ready")]

    close_ready = bool(merged_pull_requests) and report.get("allMerged") and not unknown_prs
    caution = bool(merged_pull_requests) and (unknown_prs or not report.get("allMerged"))

    return {
        "closeReady": close_ready,
        "caution": caution,
        "hasPullRequest": report.get("hasPullRequest"),
        "allMerged": report.get("allMerged"),
        "mergedPullRequestCount": len(merged_pull_requests),
        "pullRequestCount": len(pull_requests),
        "unknownPullRequestCount": len(unknown_prs),
        "mergeReadyPullRequestCount": len(ready_prs),
        "pullRequestReadiness": readiness,
    }


def build_merge_report(session: dict[str, Any]) -> dict[str, Any]:
    outputs = session.get("outputs", [])
    pr_urls = find_pr_urls(outputs)
    prs = [fetch_pr_status(url) for url in pr_urls]
    merged_prs = [item for item in prs if item.get("merged")]

    return {
        "hasPullRequest": bool(prs),
        "pullRequests": prs,
        "mergedPullRequests": merged_prs,
        "allMerged": bool(prs) and len(merged_prs) == len(prs),
    }


def build_close_message(
    session_name: str,
    brief: dict[str, Any],
    report: dict[str, Any],
    *,
    recommended_command: str | None = None,
) -> str:
    lines = [
        f"Jules session `{session_name}` is a close candidate.",
        f"Title: {brief.get('title') or '(untitled)'}",
        f"State: {brief.get('state')}",
    ]

    for pr in report.get("mergedPullRequests", []):
        pr_title = pr.get("title") or "(untitled PR)"
        pr_url = pr.get("url") or "(missing URL)"
        merged_at = pr.get("mergedAt") or "unknown time"
        lines.append(f"Merged PR: #{pr.get('number')} {pr_title} ({pr_url}) at {merged_at}")

    if report.get("allMerged"):
        lines.append("All discovered PRs for this session are merged.")
    else:
        lines.append("Some PRs are merged, but not all discovered PRs are merged yet.")

    lines.append(f"If you want to close it, confirm and then run: {recommended_command or build_close_command(session_name)}")
    return "\n".join(lines)


def summarize_session_brief(session: dict[str, Any], *, include_merge_status: bool = False) -> dict[str, Any]:
    summary = {
        "name": session.get("name"),
        "id": session.get("id"),
        "title": session.get("title"),
        "state": session.get("state"),
        "url": session.get("url"),
        "repo": extract_repo_name(session),
        "updateTime": session.get("updateTime"),
        "outputCount": len(session.get("outputs", [])),
        "pullRequestUrls": find_pr_urls(session.get("outputs", [])),
    }
    if include_merge_status:
        summary["mergeStatus"] = build_merge_report(session)
    return summary


def summarize_activity(activity: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "name": activity.get("name"),
        "createTime": activity.get("createTime"),
        "originator": activity.get("originator"),
        "description": activity.get("description"),
    }

    if "agentMessaged" in activity:
        summary["type"] = "agentMessaged"
        summary["message"] = activity["agentMessaged"].get("agentMessage")
    elif "userMessaged" in activity:
        summary["type"] = "userMessaged"
        summary["message"] = activity["userMessaged"].get("userMessage")
    elif "planGenerated" in activity:
        summary["type"] = "planGenerated"
        plan = activity["planGenerated"].get("plan", {})
        summary["planId"] = plan.get("id")
        summary["steps"] = [step.get("title") for step in plan.get("steps", [])]
    elif "progressUpdated" in activity:
        summary["type"] = "progressUpdated"
        summary["title"] = activity["progressUpdated"].get("title")
        summary["details"] = activity["progressUpdated"].get("description")
    elif "planApproved" in activity:
        summary["type"] = "planApproved"
        summary["planId"] = activity["planApproved"].get("planId")
    elif "sessionCompleted" in activity:
        summary["type"] = "sessionCompleted"
    elif "sessionFailed" in activity:
        summary["type"] = "sessionFailed"
        summary["reason"] = activity["sessionFailed"].get("reason")
    else:
        summary["type"] = "unknown"

    artifacts = []
    for artifact in activity.get("artifacts", []):
        if "bashOutput" in artifact:
            bash_output = artifact["bashOutput"]
            artifacts.append(
                {
                    "kind": "bashOutput",
                    "command": bash_output.get("command"),
                    "exitCode": bash_output.get("exitCode"),
                    "output": bash_output.get("output"),
                }
            )
        elif "changeSet" in artifact:
            change_set = artifact["changeSet"]
            artifacts.append({"kind": "changeSet", "title": change_set.get("title"), "description": change_set.get("description")})
        elif "media" in artifact:
            media = artifact["media"]
            artifacts.append({"kind": "media", "mimeType": media.get("mimeType")})

    if artifacts:
        summary["artifacts"] = artifacts

    return summary


def build_session_summary_payload(
    session: dict[str, Any],
    activities: list[dict[str, Any]],
    *,
    recent_count: int,
    include_merge_status: bool = False,
) -> dict[str, Any]:
    ordered_activities = order_activities(activities)
    latest = ordered_activities[-1] if ordered_activities else None

    payload = {
        "session": {
            "name": session.get("name"),
            "id": session.get("id"),
            "title": session.get("title"),
            "state": session.get("state"),
            "url": session.get("url"),
            "repo": extract_repo_name(session),
            "createTime": session.get("createTime"),
            "updateTime": session.get("updateTime"),
            "outputs": session.get("outputs", []),
        },
        "activityCount": len(ordered_activities),
        "latestActivity": summarize_activity(latest) if latest else None,
        "recentActivities": [summarize_activity(item) for item in ordered_activities[-recent_count:]],
    }
    if include_merge_status:
        payload["mergeStatus"] = build_merge_report(session)
    return payload


def summarize_session(args: argparse.Namespace) -> None:
    session_name = normalize_session_name(args.session)
    session = api_request("GET", f"/{session_name}")
    activities, _ = collect_session_activities(session_name, page_size=args.page_size)
    print_json(
        build_session_summary_payload(
            session,
            activities,
            recent_count=args.recent_count,
            include_merge_status=args.include_merge_status,
        )
    )


def resume_session(args: argparse.Namespace) -> None:
    session_name = normalize_session_name(args.session)
    session = api_request("GET", f"/{session_name}")
    state = session.get("state", "STATE_UNSPECIFIED")

    actions = []
    if state == "AWAITING_PLAN_APPROVAL":
        api_request("POST", f"/{session_name}:approvePlan", payload={})
        actions.append("approved_plan")
        if args.prompt:
            api_request(
                "POST",
                f"/{session_name}:sendMessage",
                payload={"prompt": build_prompt_from_args(args, args.prompt, continue_existing_scope=True)},
            )
            actions.append("sent_message")
    elif state in {"AWAITING_USER_FEEDBACK", "PAUSED"}:
        if not args.prompt:
            fail(f"Session is {state}. Provide --prompt so Jules has instructions to continue.")
        api_request(
            "POST",
            f"/{session_name}:sendMessage",
            payload={"prompt": build_prompt_from_args(args, args.prompt, continue_existing_scope=True)},
        )
        actions.append("sent_message")
    elif state in ACTIVE_STATES:
        if not args.allow_active:
            fail(f"Session is already active ({state}). Use --allow-active to send an extra message anyway.")
        if not args.prompt:
            fail("Use --prompt together with --allow-active to send more instructions to an active session.")
        api_request(
            "POST",
            f"/{session_name}:sendMessage",
            payload={"prompt": build_prompt_from_args(args, args.prompt, continue_existing_scope=True)},
        )
        actions.append("sent_message")
    elif state in TERMINAL_STATES:
        fail(f"Session is {state} and cannot be resumed.")
    else:
        fail(f"Unsupported session state for resume helper: {state}")

    print_json({"ok": True, "session": session_name, "state": state, "actions": actions})


def export_session(args: argparse.Namespace) -> None:
    session_name = normalize_session_name(args.session)
    payload: Any

    if args.kind == "session":
        payload = api_request("GET", f"/{session_name}")
    elif args.kind == "activities":
        activities, next_page_token = collect_session_activities(session_name, page_size=args.page_size)
        payload = {
            "activities": activities,
            "pagination": build_aggregation_metadata(page_size=args.page_size, start_page_token=None),
            "nextPageToken": next_page_token,
        }
    elif args.kind == "outputs":
        session = api_request("GET", f"/{session_name}")
        payload = {"session": session_name, "outputs": session.get("outputs", [])}
    else:
        session = api_request("GET", f"/{session_name}")
        activities, _ = collect_session_activities(session_name, page_size=args.page_size)
        payload = build_session_summary_payload(
            session,
            activities,
            recent_count=args.recent_count,
            include_merge_status=args.include_merge_status,
        )

    rendered = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered)
            handle.write("\n")
        print(json.dumps({"ok": True, "path": args.output, "kind": args.kind, "session": session_name}, ensure_ascii=False))
        return
    print(rendered)


def check_merge_status(args: argparse.Namespace) -> None:
    session_name = normalize_session_name(args.session)
    session = api_request("GET", f"/{session_name}")
    report = build_merge_report(session)
    print_json({"session": summarize_session_brief(session), "mergeStatus": report})


def check_pr_readiness(args: argparse.Namespace) -> None:
    session_name = normalize_session_name(args.session)
    session = api_request("GET", f"/{session_name}")
    report = build_merge_report(session)
    readiness = [summarize_pr_merge_readiness(pr) for pr in report.get("pullRequests", [])]
    payload = {
        "session": summarize_session_brief(session),
        "pullRequestReadiness": readiness,
        "allReady": bool(readiness) and all(item["ready"] for item in readiness),
    }
    print_json(payload)


def request_pr_rework(args: argparse.Namespace) -> None:
    session_name = normalize_session_name(args.session)
    session = api_request("GET", f"/{session_name}")
    report = build_merge_report(session)
    readiness = [summarize_pr_merge_readiness(pr) for pr in report.get("pullRequests", [])]
    blocked = [item for item in readiness if not item["ready"]]

    if not blocked:
        fail("All discovered PRs look merge-ready. No rework request message is needed.")

    lines = [
        "Please update the open pull request so it becomes merge-ready.",
        "Address the following issues before finishing:",
    ]
    for pr in blocked:
        title = pr.get("title") or "(untitled PR)"
        number = pr.get("number")
        lines.append(f"- PR #{number} {title}")
        for blocker in pr.get("blockers", []):
            lines.append(f"  - {blocker}")

    if args.extra_instruction:
        lines.append(args.extra_instruction.strip())

    message = build_prompt_from_args(
        args,
        "\n".join(lines),
        continue_existing_scope=True,
        limit_to_current_pr=True,
        extra_non_goals=["Do not broaden the task beyond the current pull request blockers."],
    )
    payload = {
        "session": summarize_session_brief(session),
        "pullRequestReadiness": readiness,
        "message": message,
    }

    if args.send:
        api_request("POST", f"/{session_name}:sendMessage", payload={"prompt": message})
        payload["sent"] = True
    else:
        payload["sent"] = False

    if args.markdown:
        print_text(message)
        return
    print_json(payload)


def close_merged_session(args: argparse.Namespace) -> None:
    session_name = normalize_session_name(args.session)
    session = api_request("GET", f"/{session_name}")
    report = build_merge_report(session)
    close_readiness = summarize_session_close_readiness(session, report)

    if not report["hasPullRequest"]:
        fail("This session has no pull request URL in its outputs, so merged-close cannot verify it safely.")
    if not report["mergedPullRequests"]:
        fail("No merged pull request was found for this session. Refusing to close it.")
    if args.require_all_merged and not report["allMerged"]:
        fail("Some pull requests for this session are not merged yet. Refusing to close it.")
    if close_readiness["caution"] and not args.allow_caution_close:
        fail(
            "This session is not fully close-ready. Review unresolved or unknown PR state first, "
            "or rerun with --allow-caution-close after explicit user approval."
        )
    if close_readiness["unknownPullRequestCount"] > 0 and not args.allow_unknown_pr_status:
        fail("Some pull requests have unknown GitHub status. Refusing to close unless --allow-unknown-pr-status is provided.")
    if args.confirm_close != CLOSE_CONFIRM_TOKEN:
        fail(
            "Merged pull request detected, but close confirmation is missing. "
            f"Re-run with --confirm-close {CLOSE_CONFIRM_TOKEN} after user approval."
        )

    api_request("DELETE", f"/{session_name}")
    print_json(
        {
            "ok": True,
            "deleted": session_name,
            "session": summarize_session_brief(session),
            "closeReadiness": close_readiness,
            "mergeStatus": report,
        }
    )


def doctor(args: argparse.Namespace) -> None:
    dotenv_path = find_dotenv_path()
    api_key_present = bool(os.environ.get("JULES_API_KEY", "").strip())
    gh_status = collect_gh_auth_status()
    jules_status = collect_jules_cli_status()
    api_ready = api_key_present
    cli_ready = bool(jules_status.get("ready"))
    merge_ready = bool(gh_status.get("installed") and gh_status.get("authenticated"))

    payload = {
        "dotenv": {
            "found": bool(dotenv_path),
            "path": str(dotenv_path) if dotenv_path else None,
        },
        "julesApiKey": {
            "present": api_key_present,
        },
        "gh": gh_status,
        "julesCli": jules_status,
        "apiReady": api_ready,
        "cliReady": cli_ready,
        "mergeReady": merge_ready,
    }

    payload["ready"] = bool(api_ready or cli_ready)

    if args.compact:
        print_text(
            " ".join(
                [
                    f"dotenv={'yes' if payload['dotenv']['found'] else 'no'}",
                    f"api_key={'yes' if api_key_present else 'no'}",
                    f"api_ready={'yes' if api_ready else 'no'}",
                    f"gh={'yes' if gh_status.get('installed') else 'no'}",
                    f"gh_auth={'yes' if gh_status.get('authenticated') else 'no'}",
                    f"merge_ready={'yes' if merge_ready else 'no'}",
                    f"jules_cli={'yes' if jules_status.get('installed') else 'no'}",
                    f"jules_cli_auth={jules_status.get('authStatus', 'unknown')}",
                    f"cli_ready={'yes' if cli_ready else 'no'}",
                    f"ready={'yes' if payload['ready'] else 'no'}",
                ]
            )
        )
        return
    print_json(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Control Google Jules via the Jules REST API.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_active_sessions_parser = subparsers.add_parser("list-active-sessions", help="List non-terminal Jules sessions.")
    add_aggregate_pagination_arguments(list_active_sessions_parser, default_page_size=50)
    list_active_sessions_parser.add_argument("--repo-filter", help="Only include sessions for owner/repo.")
    list_active_sessions_parser.add_argument(
        "--include-merge-status",
        action="store_true",
        help="Also inspect PR merge status with gh when PR URLs are present in outputs.",
    )
    list_active_sessions_parser.set_defaults(func=list_active_sessions)

    stale_session_report_parser = subparsers.add_parser(
        "stale-session-report",
        help="List open Jules sessions that have not been updated recently.",
    )
    add_aggregate_pagination_arguments(stale_session_report_parser, default_page_size=50)
    stale_session_report_parser.add_argument("--repo-filter", help="Only include sessions for owner/repo.")
    stale_session_report_parser.add_argument(
        "--stale-after-hours",
        type=float,
        default=24.0,
        help="Treat open sessions as stale after this many hours without updates.",
    )
    stale_session_report_parser.add_argument(
        "--include-merge-status",
        action="store_true",
        help="Also inspect PR merge status with gh when PR URLs are present in outputs.",
    )
    stale_session_report_parser.set_defaults(func=stale_session_report)

    list_unmerged_sessions_parser = subparsers.add_parser(
        "list-unmerged-sessions",
        help="List sessions whose discovered PR outputs are not merged yet.",
    )
    add_aggregate_pagination_arguments(list_unmerged_sessions_parser, default_page_size=50)
    list_unmerged_sessions_parser.add_argument("--repo-filter", help="Only include sessions for owner/repo.")
    list_unmerged_sessions_parser.add_argument(
        "--include-without-pr",
        action="store_true",
        help="Also include sessions that have no pull request URL in their outputs.",
    )
    list_unmerged_sessions_parser.set_defaults(func=list_unmerged_sessions)

    list_merged_sessions_parser = subparsers.add_parser(
        "list-merged-sessions",
        help="List sessions whose discovered PR outputs include merged pull requests.",
    )
    add_aggregate_pagination_arguments(list_merged_sessions_parser, default_page_size=50)
    list_merged_sessions_parser.add_argument("--repo-filter", help="Only include sessions for owner/repo.")
    list_merged_sessions_parser.add_argument(
        "--require-all-merged",
        action="store_true",
        help="Only include sessions where every discovered PR URL is merged.",
    )
    list_merged_sessions_parser.set_defaults(func=list_merged_sessions)

    cleanup_report_parser = subparsers.add_parser(
        "cleanup-report",
        help="Show merged cleanup candidates, unmerged work, and sessions without PR outputs in one report.",
    )
    add_aggregate_pagination_arguments(cleanup_report_parser, default_page_size=50)
    cleanup_report_parser.add_argument("--repo-filter", help="Only include sessions for owner/repo.")
    cleanup_report_parser.add_argument(
        "--require-all-merged",
        action="store_true",
        help="Only treat sessions as merged candidates when every discovered PR URL is merged.",
    )
    cleanup_report_parser.add_argument("--compact", action="store_true", help="Print a one-line summary instead of JSON.")
    cleanup_report_parser.add_argument("--markdown", action="store_true", help="Print a Markdown report instead of JSON.")
    cleanup_report_parser.set_defaults(func=cleanup_report)

    close_ready_report_parser = subparsers.add_parser(
        "close-ready-report",
        help="Show merged-session cleanup candidates with close instructions.",
    )
    add_aggregate_pagination_arguments(close_ready_report_parser, default_page_size=50)
    close_ready_report_parser.add_argument("--repo-filter", help="Only include sessions for owner/repo.")
    close_ready_report_parser.add_argument(
        "--require-all-merged",
        action="store_true",
        help="Only include sessions where every discovered PR URL is merged.",
    )
    close_ready_report_parser.add_argument("--compact", action="store_true", help="Print a one-line summary instead of JSON.")
    close_ready_report_parser.add_argument("--markdown", action="store_true", help="Print a Markdown report instead of JSON.")
    close_ready_report_parser.set_defaults(func=close_ready_report)

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check .env, API key, gh auth, and Jules CLI readiness in one command.",
    )
    doctor_parser.add_argument("--compact", action="store_true", help="Print a short status line instead of JSON.")
    doctor_parser.set_defaults(func=doctor)

    gh_auth_check_parser = subparsers.add_parser(
        "gh-auth-check",
        help="Verify that gh is installed and authenticated for PR merge checks.",
    )
    gh_auth_check_parser.add_argument("--compact", action="store_true", help="Print a short status line instead of JSON.")
    gh_auth_check_parser.set_defaults(func=gh_auth_check)

    list_sources_parser = subparsers.add_parser("list-sources", help="List connected Jules sources.")
    list_sources_parser.add_argument("--filter", help="Optional AIP-160 name filter.")
    add_aggregate_pagination_arguments(list_sources_parser, default_page_size=30)
    list_sources_parser.set_defaults(func=list_sources)

    repo_to_source_parser = subparsers.add_parser(
        "repo-to-source",
        help="Resolve owner/repo to a Jules source resource name.",
    )
    repo_to_source_parser.add_argument("--repo", required=True, help="GitHub repository in owner/repo format.")
    add_aggregate_pagination_arguments(repo_to_source_parser, default_page_size=100)
    repo_to_source_parser.add_argument("--allow-contains", action="store_true", help="Fallback to substring matching when exact source lookup fails.")
    repo_to_source_parser.add_argument("--compact", action="store_true", help="Print only the first matched source name.")
    repo_to_source_parser.set_defaults(func=repo_to_source)

    list_sessions_parser = subparsers.add_parser("list-sessions", help="List Jules sessions.")
    add_aggregate_pagination_arguments(list_sessions_parser, default_page_size=30)
    list_sessions_parser.set_defaults(func=list_sessions)

    delete_session_parser = subparsers.add_parser("delete-session", help="Delete a Jules session.")
    delete_session_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    delete_session_parser.set_defaults(func=delete_session)

    cancel_session_parser = subparsers.add_parser(
        "cancel-session",
        help="Delete a Jules session as a cancel-style action. This is permanent.",
    )
    cancel_session_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    cancel_session_parser.set_defaults(func=delete_session)

    get_session_parser = subparsers.add_parser("get-session", help="Fetch one Jules session.")
    get_session_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    get_session_parser.set_defaults(func=get_session)

    create_session_parser = subparsers.add_parser("create-session", help="Create a Jules session.")
    create_session_parser.add_argument("--source", required=True, help="Source resource name, for example sources/github/OWNER/REPO.")
    create_session_parser.add_argument("--branch", required=True, help="Git branch to start from.")
    create_session_parser.add_argument("--prompt", required=True, help="Initial Jules task prompt.")
    create_session_parser.add_argument("--title", help="Optional session title.")
    create_session_parser.add_argument("--require-plan-approval", action="store_true", help="Require explicit plan approval before execution.")
    add_scope_control_arguments(create_session_parser)
    create_session_parser.add_argument(
        "--automation-mode",
        choices=["AUTO_CREATE_PR"],
        help="Optional Jules automation mode.",
    )
    create_session_parser.set_defaults(func=create_session)

    send_message_parser = subparsers.add_parser("send-message", help="Send a follow-up message to a session.")
    send_message_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    send_message_parser.add_argument("--prompt", required=True, help="Follow-up instruction.")
    add_scope_control_arguments(send_message_parser)
    send_message_parser.set_defaults(func=send_message)

    approve_plan_parser = subparsers.add_parser("approve-plan", help="Approve the latest plan in a session.")
    approve_plan_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    approve_plan_parser.set_defaults(func=approve_plan)

    list_activities_parser = subparsers.add_parser("list-activities", help="List activities for a session.")
    list_activities_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    add_aggregate_pagination_arguments(list_activities_parser, default_page_size=50)
    list_activities_parser.set_defaults(func=list_activities)

    get_activity_parser = subparsers.add_parser("get-activity", help="Fetch one activity from a session.")
    get_activity_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    get_activity_parser.add_argument("--activity", required=True, help="Activity id or full activity resource name.")
    get_activity_parser.set_defaults(func=get_activity)

    wait_parser = subparsers.add_parser("wait", help="Poll a session until it needs action or finishes.")
    wait_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    wait_parser.add_argument("--interval", type=int, default=10, help="Polling interval in seconds.")
    wait_parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="Maximum wait time in seconds.")
    wait_parser.add_argument("--verbose", action="store_true", help="Print each polled state before the final session object.")
    wait_parser.set_defaults(func=wait_for_session)

    resume_parser = subparsers.add_parser(
        "resume",
        help="Best-effort resume helper: approve a pending plan or send a follow-up prompt depending on session state.",
    )
    resume_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    resume_parser.add_argument("--prompt", help="Optional follow-up instruction. Required for PAUSED and AWAITING_USER_FEEDBACK.")
    resume_parser.add_argument("--allow-active", action="store_true", help="Allow sending a message even if the session is already active.")
    add_scope_control_arguments(resume_parser)
    resume_parser.set_defaults(func=resume_session)

    summary_parser = subparsers.add_parser("summary", help="Print a compact summary for a session and its latest activities.")
    summary_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    summary_parser.add_argument("--page-size", type=int, default=20, help="How many activities to fetch.")
    summary_parser.add_argument("--recent-count", type=int, default=5, help="How many recent activities to include in the summary.")
    summary_parser.add_argument(
        "--include-merge-status",
        action="store_true",
        help="Also inspect PR merge status with gh when PR URLs are present in outputs.",
    )
    summary_parser.set_defaults(func=summarize_session)

    export_parser = subparsers.add_parser("export", help="Export session data as JSON to stdout or a file.")
    export_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    export_parser.add_argument(
        "--kind",
        choices=["summary", "session", "activities", "outputs"],
        default="summary",
        help="Which JSON payload to export.",
    )
    export_parser.add_argument("--page-size", type=int, default=50, help="How many activities to fetch for summary or activities export.")
    export_parser.add_argument("--recent-count", type=int, default=5, help="How many recent activities to keep in summary export.")
    export_parser.add_argument(
        "--include-merge-status",
        action="store_true",
        help="Include PR merge status in summary export by querying GitHub with gh.",
    )
    export_parser.add_argument("--output", help="Write JSON to a file instead of stdout.")
    export_parser.set_defaults(func=export_session)

    check_merge_parser = subparsers.add_parser("check-merge-status", help="Inspect PR merge status for a Jules session via gh.")
    check_merge_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    check_merge_parser.set_defaults(func=check_merge_status)

    check_pr_readiness_parser = subparsers.add_parser(
        "check-pr-readiness",
        help="Inspect whether a session's discovered PRs look merge-ready.",
    )
    check_pr_readiness_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    check_pr_readiness_parser.set_defaults(func=check_pr_readiness)

    request_pr_rework_parser = subparsers.add_parser(
        "request-pr-rework",
        help="Generate or send a Jules follow-up message when PRs are not merge-ready.",
    )
    request_pr_rework_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    request_pr_rework_parser.add_argument("--extra-instruction", help="Optional extra instruction appended to the rework message.")
    request_pr_rework_parser.add_argument("--send", action="store_true", help="Send the generated message to Jules immediately.")
    request_pr_rework_parser.add_argument("--markdown", action="store_true", help="Print only the generated rework message.")
    add_scope_control_arguments(request_pr_rework_parser)
    request_pr_rework_parser.set_defaults(func=request_pr_rework)

    notify_close_parser = subparsers.add_parser(
        "notify-close-plan",
        help="Generate a user-facing confirmation message for a merged session before closing it.",
    )
    notify_close_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    notify_close_parser.add_argument(
        "--allow-caution-close",
        action="store_true",
        help="Allow a manually reviewed close plan even when the session is marked caution.",
    )
    notify_close_parser.add_argument(
        "--allow-unknown-pr-status",
        action="store_true",
        help="Allow a manually reviewed close plan when some PR statuses are unknown.",
    )
    notify_close_parser.add_argument("--markdown", action="store_true", help="Print only the user-facing message as Markdown text.")
    notify_close_parser.set_defaults(func=notify_close_plan)

    close_merged_parser = subparsers.add_parser(
        "close-merged-session",
        help="Delete a session only if a merged PR is detected and explicit confirmation is provided.",
    )
    close_merged_parser.add_argument("--session", required=True, help="Session id or sessions/<id> resource name.")
    close_merged_parser.add_argument(
        "--confirm-close",
        help=f"Required safety token. Must be exactly {CLOSE_CONFIRM_TOKEN}.",
    )
    close_merged_parser.add_argument(
        "--require-all-merged",
        action="store_true",
        help="Refuse to close unless every discovered PR URL for the session is merged.",
    )
    close_merged_parser.add_argument(
        "--allow-unknown-pr-status",
        action="store_true",
        help="Allow close even when some PR statuses could not be resolved from GitHub.",
    )
    close_merged_parser.add_argument(
        "--allow-caution-close",
        action="store_true",
        help="Allow a manually reviewed override close when the session is marked caution.",
    )
    close_merged_parser.set_defaults(func=close_merged_session)

    return parser


def main() -> None:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
