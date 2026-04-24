import argparse
import importlib.util
import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "google-jules-control" / "scripts" / "jules_api.py"
SPEC = importlib.util.spec_from_file_location("jules_api", MODULE_PATH)
jules_api = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(jules_api)


class JulesApiTests(unittest.TestCase):
    class _FakeResponse:
        def __init__(self, body: str) -> None:
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            return None

        def read(self) -> bytes:
            return self.body.encode("utf-8")

    def test_build_url_uses_current_env_base_url(self) -> None:
        with mock.patch.dict(jules_api.os.environ, {"JULES_API_BASE_URL": "https://example.test/v9"}):
            url = jules_api.build_url("/sources", {"pageSize": 1})

        self.assertEqual("https://example.test/v9/sources?pageSize=1", url)

    def test_api_request_uses_request_timeout(self) -> None:
        with mock.patch.dict(jules_api.os.environ, {"JULES_API_KEY": "test-key"}, clear=False):
            with mock.patch.object(jules_api.urllib.request, "urlopen", return_value=self._FakeResponse("{}")) as urlopen:
                jules_api.api_request("GET", "/sources")

        self.assertEqual(60, urlopen.call_args.kwargs.get("timeout"))

    def test_api_request_reports_invalid_json_without_traceback(self) -> None:
        captured: BaseException | None = None
        stderr = io.StringIO()

        with mock.patch.dict(jules_api.os.environ, {"JULES_API_KEY": "test-key"}, clear=False):
            with mock.patch.object(jules_api.urllib.request, "urlopen", return_value=self._FakeResponse("not json")):
                with redirect_stderr(stderr):
                    try:
                        jules_api.api_request("GET", "/sources")
                    except BaseException as exc:
                        captured = exc

        self.assertIsInstance(captured, SystemExit)
        self.assertIn("non-JSON", stderr.getvalue())

    def test_build_strict_scope_prompt_includes_default_guards(self) -> None:
        prompt = jules_api.build_strict_scope_prompt("Fix the flaky login redirect test.")

        self.assertIn("Interpret the request as narrowly as possible.", prompt)
        self.assertIn("Do not expand scope on your own.", prompt)
        self.assertIn("Touch only what you must. Clean up only your own mess.", prompt)
        self.assertIn("Every changed line should trace directly to the user's request.", prompt)
        self.assertIn("If multiple interpretations are possible, do not choose the broader one.", prompt)
        self.assertIn("Verification performed", prompt)
        self.assertIn("Fix the flaky login redirect test.", prompt)

    def test_create_session_wraps_prompt_with_strict_scope_rules(self) -> None:
        args = argparse.Namespace(
            source="sources/github/owner/repo",
            branch="main",
            prompt="Fix the flaky login redirect test.",
            title="Fix flaky test",
            require_plan_approval=True,
            automation_mode=None,
        )

        with mock.patch.object(jules_api, "api_request", return_value={"name": "sessions/123"}) as api_request:
            jules_api.create_session(args)

        payload = api_request.call_args.kwargs["payload"]
        self.assertIn("Interpret the request as narrowly as possible.", payload["prompt"])
        self.assertIn("Fix the flaky login redirect test.", payload["prompt"])

    def test_send_message_wraps_prompt_with_follow_up_scope_guard(self) -> None:
        args = argparse.Namespace(
            session="123",
            prompt="Keep the patch under 200 lines.",
        )

        with mock.patch.object(jules_api, "api_request", return_value={}) as api_request:
            jules_api.send_message(args)

        payload = api_request.call_args.kwargs["payload"]
        self.assertIn("Continue only within the existing approved task scope.", payload["prompt"])
        self.assertIn("Keep the patch under 200 lines.", payload["prompt"])

    def test_create_session_includes_scope_notes_and_non_goals(self) -> None:
        args = argparse.Namespace(
            source="sources/github/owner/repo",
            branch="main",
            prompt="Fix the flaky login redirect test.",
            title=None,
            require_plan_approval=False,
            automation_mode=None,
            scope_note=["Stay within tests/auth."],
            non_goal=["Do not refactor shared helpers."],
        )

        with mock.patch.object(jules_api, "api_request", return_value={"name": "sessions/123"}) as api_request:
            jules_api.create_session(args)

        payload = api_request.call_args.kwargs["payload"]
        self.assertIn("Scope notes:", payload["prompt"])
        self.assertIn("Stay within tests/auth.", payload["prompt"])
        self.assertIn("Non-goals:", payload["prompt"])
        self.assertIn("Do not refactor shared helpers.", payload["prompt"])

    def test_resume_session_wraps_prompt_with_follow_up_scope_guard(self) -> None:
        args = argparse.Namespace(
            session="123",
            prompt="Only fix the failing CI check.",
            allow_active=False,
        )
        session = {"name": "sessions/123", "state": "PAUSED"}

        with mock.patch.object(jules_api, "api_request", side_effect=[session, {"ok": True}]) as api_request:
            jules_api.resume_session(args)

        payload = api_request.call_args_list[1].kwargs["payload"]
        self.assertIn("Continue only within the existing approved task scope.", payload["prompt"])
        self.assertIn("Only fix the failing CI check.", payload["prompt"])

    def test_request_pr_rework_send_scopes_message_to_current_pr(self) -> None:
        args = argparse.Namespace(
            session="123",
            extra_instruction="Avoid dependency updates.",
            send=True,
            markdown=False,
        )
        session = {"name": "sessions/123", "title": "Rework test", "state": "IN_PROGRESS", "outputs": ["https://github.com/owner/repo/pull/1"]}
        report = {
            "pullRequests": [
                {
                    "number": 1,
                    "title": "Fix flaky login redirect test",
                    "url": "https://github.com/owner/repo/pull/1",
                    "status": "not_merged",
                    "merged": False,
                    "mergeable": "CONFLICTING",
                    "mergeStateStatus": "DIRTY",
                    "reviewDecision": "CHANGES_REQUESTED",
                    "statusCheckRollup": [{"name": "ci/test", "status": "COMPLETED", "conclusion": "FAILURE"}],
                }
            ]
        }

        with mock.patch.object(jules_api, "api_request", side_effect=[session, {"ok": True}]) as api_request:
            with mock.patch.object(jules_api, "build_merge_report", return_value=report):
                jules_api.request_pr_rework(args)

        payload = api_request.call_args_list[1].kwargs["payload"]
        self.assertIn("Only make the minimum changes required to make the current pull request merge-ready.", payload["prompt"])
        self.assertIn("Avoid dependency updates.", payload["prompt"])

    def test_request_pr_rework_reports_missing_pull_request_output(self) -> None:
        args = argparse.Namespace(
            session="123",
            extra_instruction=None,
            send=False,
            markdown=False,
        )
        session = {"name": "sessions/123", "title": "No PR", "state": "COMPLETED", "outputs": []}
        report = {
            "hasPullRequest": False,
            "pullRequests": [],
            "mergedPullRequests": [],
            "allMerged": False,
        }
        stderr = io.StringIO()

        with mock.patch.object(jules_api, "api_request", return_value=session):
            with mock.patch.object(jules_api, "build_merge_report", return_value=report):
                with redirect_stderr(stderr):
                    with self.assertRaises(SystemExit):
                        jules_api.request_pr_rework(args)

        self.assertIn("No pull request URL", stderr.getvalue())

    def test_build_parser_supports_scope_control_flags(self) -> None:
        parser = jules_api.build_parser()

        args = parser.parse_args(
            [
                "create-session",
                "--source",
                "sources/github/owner/repo",
                "--branch",
                "main",
                "--prompt",
                "Fix flaky test",
                "--scope-note",
                "tests/auth only",
                "--non-goal",
                "no refactor",
                "--no-strict-scope",
            ]
        )

        self.assertEqual(["tests/auth only"], args.scope_note)
        self.assertEqual(["no refactor"], args.non_goal)
        self.assertFalse(args.strict_scope)

    def test_in_progress_status_check_is_not_merge_ready(self) -> None:
        pr = {
            "status": "not_merged",
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
            "reviewDecision": None,
            "statusCheckRollup": [{"name": "ci/test", "status": "IN_PROGRESS", "conclusion": None}],
        }

        self.assertFalse(jules_api.is_pr_merge_ready(pr))

        summary = jules_api.summarize_pr_merge_readiness(pr)
        self.assertFalse(summary["ready"])
        self.assertIn("ci/test=IN_PROGRESS", summary["blockers"])

    def test_state_only_failed_status_check_is_not_merge_ready(self) -> None:
        pr = {
            "status": "not_merged",
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
            "reviewDecision": None,
            "statusCheckRollup": [{"context": "ci/legacy", "state": "FAILURE"}],
        }

        self.assertFalse(jules_api.is_pr_merge_ready(pr))

        summary = jules_api.summarize_pr_merge_readiness(pr)
        self.assertFalse(summary["ready"])
        self.assertIn("ci/legacy=FAILURE", summary["blockers"])

    def test_unknown_status_check_shape_is_not_merge_ready(self) -> None:
        pr = {
            "status": "not_merged",
            "mergeable": "MERGEABLE",
            "mergeStateStatus": "CLEAN",
            "reviewDecision": None,
            "statusCheckRollup": [{"name": "ci/unknown"}],
        }

        self.assertFalse(jules_api.is_pr_merge_ready(pr))

        summary = jules_api.summarize_pr_merge_readiness(pr)
        self.assertFalse(summary["ready"])
        self.assertIn("ci/unknown=UNKNOWN", summary["blockers"])

    def test_merged_pr_readiness_has_no_spurious_blockers(self) -> None:
        pr = {
            "status": "merged",
            "merged": True,
            "mergeable": None,
            "mergeStateStatus": None,
            "reviewDecision": None,
            "statusCheckRollup": [],
        }

        summary = jules_api.summarize_pr_merge_readiness(pr)
        self.assertTrue(summary["ready"])
        self.assertEqual([], summary["blockers"])

    def test_cleanup_report_format_includes_caution_summary(self) -> None:
        payload = {
            "summary": {
                "totalSessionsScanned": 3,
                "mergedCandidateCount": 0,
                "cautionCount": 2,
                "unmergedCount": 1,
                "withoutPrCount": 0,
            },
            "mergedCandidates": [],
            "cautionCandidates": [{"name": "sessions/1", "state": "IN_PROGRESS", "repo": "owner/repo", "title": "Investigate"}],
            "unmergedSessions": [],
            "withoutPullRequest": [],
        }

        compact = jules_api.format_cleanup_report_compact(payload)
        markdown = jules_api.format_cleanup_report_markdown(payload)

        self.assertIn("caution=2", compact)
        self.assertIn("## Caution", markdown)
        self.assertIn("sessions/1", markdown)

    def test_close_merged_session_refuses_caution_without_override(self) -> None:
        session = {
            "name": "sessions/123",
            "title": "Cleanup test",
            "state": "COMPLETED",
            "outputs": ["https://github.com/owner/repo/pull/1", "https://github.com/owner/repo/pull/2"],
        }
        report = {
            "hasPullRequest": True,
            "pullRequests": [
                {"url": "https://github.com/owner/repo/pull/1", "status": "merged", "merged": True},
                {
                    "url": "https://github.com/owner/repo/pull/2",
                    "status": "not_merged",
                    "merged": False,
                    "mergeable": "MERGEABLE",
                    "mergeStateStatus": "CLEAN",
                    "reviewDecision": None,
                    "statusCheckRollup": [],
                },
            ],
            "mergedPullRequests": [{"url": "https://github.com/owner/repo/pull/1", "status": "merged", "merged": True}],
            "allMerged": False,
        }
        args = argparse.Namespace(
            session="sessions/123",
            require_all_merged=False,
            allow_unknown_pr_status=False,
            allow_caution_close=False,
            confirm_close=jules_api.CLOSE_CONFIRM_TOKEN,
        )

        with mock.patch.object(jules_api, "api_request", return_value=session) as api_request:
            with mock.patch.object(jules_api, "build_merge_report", return_value=report):
                with redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        jules_api.close_merged_session(args)

        self.assertEqual(1, api_request.call_count)

    def test_delete_session_requires_explicit_confirmation_token(self) -> None:
        args = argparse.Namespace(session="sessions/123", confirm_delete=None)

        with mock.patch.object(jules_api, "api_request") as api_request:
            with redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit):
                    jules_api.delete_session(args)

        self.assertEqual(0, api_request.call_count)
        self.assertIn("DELETE_JULES_SESSION", stderr.getvalue())

    def test_delete_session_allows_explicit_confirmation_token(self) -> None:
        args = argparse.Namespace(session="sessions/123", confirm_delete="DELETE_JULES_SESSION")

        with mock.patch.object(jules_api, "api_request", return_value={}) as api_request:
            with redirect_stdout(io.StringIO()):
                jules_api.delete_session(args)

        api_request.assert_called_once_with("DELETE", "/sessions/123")

    def test_delete_session_parser_accepts_confirmation_token(self) -> None:
        parser = jules_api.build_parser()

        args = parser.parse_args(
            [
                "delete-session",
                "--session",
                "sessions/123",
                "--confirm-delete",
                "DELETE_JULES_SESSION",
            ]
        )

        self.assertEqual("DELETE_JULES_SESSION", args.confirm_delete)

    def test_doctor_reports_api_key_present_without_api_ready_when_not_validated(self) -> None:
        args = argparse.Namespace(compact=True, validate_api=False)
        output = io.StringIO()

        with mock.patch.object(jules_api, "find_dotenv_path", return_value=Path("/tmp/.env")):
            with mock.patch.dict(jules_api.os.environ, {"JULES_API_KEY": "test-key"}, clear=False):
                with mock.patch.object(jules_api, "collect_gh_auth_status", return_value={"installed": True, "authenticated": False}):
                    with mock.patch.object(
                        jules_api,
                        "collect_jules_cli_status",
                        return_value={"installed": False, "path": None, "authStatus": "not_installed", "ready": False},
                    ):
                        with redirect_stdout(output):
                            jules_api.doctor(args)

        rendered = output.getvalue().strip()
        self.assertIn("api_key=yes", rendered)
        self.assertIn("api_validated=no", rendered)
        self.assertIn("api_ready=no", rendered)
        self.assertIn("cli_ready=no", rendered)
        self.assertIn("merge_ready=no", rendered)
        self.assertIn("ready=no", rendered)

    def test_doctor_validate_api_marks_api_ready_after_successful_probe(self) -> None:
        args = argparse.Namespace(compact=True, validate_api=True)
        output = io.StringIO()

        with mock.patch.object(jules_api, "find_dotenv_path", return_value=Path("/tmp/.env")):
            with mock.patch.dict(jules_api.os.environ, {"JULES_API_KEY": "test-key"}, clear=False):
                with mock.patch.object(jules_api, "collect_gh_auth_status", return_value={"installed": True, "authenticated": False}):
                    with mock.patch.object(
                        jules_api,
                        "collect_jules_cli_status",
                        return_value={"installed": False, "path": None, "authStatus": "not_installed", "ready": False},
                    ):
                        with mock.patch.object(jules_api, "api_request", return_value={"sources": []}) as api_request:
                            with redirect_stdout(output):
                                jules_api.doctor(args)

        api_request.assert_called_once_with("GET", "/sources", query={"pageSize": 1})
        rendered = output.getvalue().strip()
        self.assertIn("api_validated=yes", rendered)
        self.assertIn("api_status=ok", rendered)
        self.assertIn("api_ready=yes", rendered)
        self.assertIn("ready=yes", rendered)

    def test_doctor_validate_api_reports_failed_probe_without_ready(self) -> None:
        args = argparse.Namespace(compact=True, validate_api=True)
        output = io.StringIO()

        with mock.patch.object(jules_api, "find_dotenv_path", return_value=Path("/tmp/.env")):
            with mock.patch.dict(jules_api.os.environ, {"JULES_API_KEY": "test-key"}, clear=False):
                with mock.patch.object(jules_api, "collect_gh_auth_status", return_value={"installed": True, "authenticated": False}):
                    with mock.patch.object(
                        jules_api,
                        "collect_jules_cli_status",
                        return_value={"installed": False, "path": None, "authStatus": "not_installed", "ready": False},
                    ):
                        with mock.patch.object(jules_api, "api_request", side_effect=SystemExit(1)):
                            with redirect_stdout(output):
                                jules_api.doctor(args)

        rendered = output.getvalue().strip()
        self.assertIn("api_validated=yes", rendered)
        self.assertIn("api_status=failed", rendered)
        self.assertIn("api_ready=no", rendered)
        self.assertIn("ready=no", rendered)

    def test_doctor_parser_supports_api_validation_probe(self) -> None:
        parser = jules_api.build_parser()

        args = parser.parse_args(["doctor", "--validate-api"])

        self.assertTrue(args.validate_api)

    def test_collect_jules_cli_status_marks_authenticated_when_probe_succeeds(self) -> None:
        version_result = mock.Mock(stdout="1.2.3\n", stderr="")
        probe_result = mock.Mock(stdout="repo-a\nrepo-b\n", stderr="")

        with mock.patch.object(jules_api.shutil, "which", return_value="/usr/local/bin/jules"):
            with mock.patch.object(jules_api.subprocess, "run", side_effect=[version_result, probe_result]) as run:
                status = jules_api.collect_jules_cli_status()

        self.assertTrue(status["installed"])
        self.assertTrue(status["authenticated"])
        self.assertEqual("authenticated", status["authStatus"])
        self.assertTrue(status["ready"])
        self.assertEqual(2, run.call_count)

    def test_collect_jules_cli_status_marks_login_required_when_probe_fails_with_auth_error(self) -> None:
        version_result = mock.Mock(stdout="1.2.3\n", stderr="")
        auth_error = jules_api.subprocess.CalledProcessError(
            returncode=1,
            cmd=["jules", "remote", "list", "--repo"],
            stderr="Please login first.",
        )

        with mock.patch.object(jules_api.shutil, "which", return_value="/usr/local/bin/jules"):
            with mock.patch.object(jules_api.subprocess, "run", side_effect=[version_result, auth_error]):
                status = jules_api.collect_jules_cli_status()

        self.assertTrue(status["installed"])
        self.assertFalse(status["authenticated"])
        self.assertEqual("not_authenticated", status["authStatus"])
        self.assertFalse(status["ready"])

    def test_build_close_message_uses_override_aware_command(self) -> None:
        message = jules_api.build_close_message(
            "sessions/123",
            {"title": "Cleanup test", "state": "COMPLETED"},
            {
                "mergedPullRequests": [{"number": 7, "title": "Fix", "url": "https://example.com/pr/7", "mergedAt": "2026-04-05T10:00:00Z"}],
                "allMerged": False,
            },
            recommended_command=(
                "python3 scripts/jules_api.py close-merged-session "
                "--session sessions/123 --allow-caution-close --confirm-close CLOSE_MERGED_SESSION"
            ),
        )

        self.assertIn("--allow-caution-close", message)

    def test_list_sessions_collects_all_pages(self) -> None:
        output = io.StringIO()
        args = argparse.Namespace(page_size=2, page_token=None)

        with mock.patch.object(
            jules_api,
            "collect_paginated_resources",
            return_value=([{"name": "sessions/1"}, {"name": "sessions/2"}], None),
        ) as collector:
            with redirect_stdout(output):
                jules_api.list_sessions(args)

        collector.assert_called_once_with("/sessions", page_size=2, resource_key="sessions", page_token=None)
        self.assertIn('"mode": "aggregate"', output.getvalue())
        self.assertIn('"pageSize": 2', output.getvalue())
        self.assertIn('"name": "sessions/2"', output.getvalue())

    def test_list_activities_collects_all_pages(self) -> None:
        output = io.StringIO()
        args = argparse.Namespace(session="123", page_size=3, page_token=None)

        with mock.patch.object(
            jules_api,
            "collect_session_activities",
            return_value=([{"name": "sessions/123/activities/1"}, {"name": "sessions/123/activities/2"}], None),
        ) as collector:
            with redirect_stdout(output):
                jules_api.list_activities(args)

        collector.assert_called_once_with("sessions/123", page_size=3, page_token=None)
        self.assertIn('"mode": "aggregate"', output.getvalue())
        self.assertIn('"pageSize": 3', output.getvalue())
        self.assertIn('"name": "sessions/123/activities/2"', output.getvalue())

    def test_summary_uses_true_latest_activity_across_pages(self) -> None:
        args = argparse.Namespace(session="123", page_size=10, recent_count=2, include_merge_status=False)
        output = io.StringIO()
        session = {
            "name": "sessions/123",
            "id": "123",
            "title": "Summary test",
            "state": "IN_PROGRESS",
            "url": "https://example.com/session/123",
            "createTime": "2026-04-05T08:00:00Z",
            "updateTime": "2026-04-05T10:00:00Z",
            "outputs": [],
        }
        activities = [
            {"name": "a2", "createTime": "2026-04-05T10:00:00Z", "description": "newest", "agentMessaged": {"agentMessage": "new"}},
            {"name": "a1", "createTime": "2026-04-05T09:00:00Z", "description": "older", "agentMessaged": {"agentMessage": "old"}},
        ]

        with mock.patch.object(jules_api, "api_request", return_value=session) as api_request:
            with mock.patch.object(jules_api, "collect_session_activities", return_value=(activities, None)) as collector:
                with redirect_stdout(output):
                    jules_api.summarize_session(args)

        api_request.assert_called_once_with("GET", "/sessions/123")
        collector.assert_called_once_with("sessions/123", page_size=10)
        rendered = output.getvalue()
        self.assertIn('"name": "a2"', rendered)

    def test_export_summary_uses_paginated_activities(self) -> None:
        args = argparse.Namespace(
            session="123",
            kind="summary",
            page_size=10,
            recent_count=2,
            include_merge_status=False,
            output=None,
        )
        output = io.StringIO()
        session = {
            "name": "sessions/123",
            "id": "123",
            "title": "Export test",
            "state": "IN_PROGRESS",
            "url": "https://example.com/session/123",
            "createTime": "2026-04-05T08:00:00Z",
            "updateTime": "2026-04-05T10:00:00Z",
            "outputs": [],
        }
        activities = [
            {"name": "a2", "createTime": "2026-04-05T10:00:00Z", "description": "newest", "agentMessaged": {"agentMessage": "new"}},
            {"name": "a1", "createTime": "2026-04-05T09:00:00Z", "description": "older", "agentMessaged": {"agentMessage": "old"}},
        ]

        with mock.patch.object(jules_api, "api_request", return_value=session) as api_request:
            with mock.patch.object(jules_api, "collect_session_activities", return_value=(activities, None)) as collector:
                with redirect_stdout(output):
                    jules_api.export_session(args)

        api_request.assert_called_once_with("GET", "/sessions/123")
        collector.assert_called_once_with("sessions/123", page_size=10)
        rendered = output.getvalue()
        self.assertIn('"name": "a2"', rendered)

    def test_export_activities_collects_all_pages(self) -> None:
        args = argparse.Namespace(
            session="123",
            kind="activities",
            page_size=10,
            recent_count=2,
            include_merge_status=False,
            output=None,
        )
        output = io.StringIO()
        activities = [{"name": "a1"}, {"name": "a2"}]

        with mock.patch.object(jules_api, "collect_session_activities", return_value=(activities, None)) as collector:
            with redirect_stdout(output):
                jules_api.export_session(args)

        collector.assert_called_once_with("sessions/123", page_size=10)
        self.assertIn('"mode": "aggregate"', output.getvalue())
        self.assertIn('"name": "a2"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
