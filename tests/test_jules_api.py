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

    def test_doctor_reports_api_ready_without_merge_ready(self) -> None:
        args = argparse.Namespace(compact=True)
        output = io.StringIO()

        with mock.patch.object(jules_api, "find_dotenv_path", return_value=Path("/tmp/.env")):
            with mock.patch.dict(jules_api.os.environ, {"JULES_API_KEY": "test-key"}, clear=False):
                with mock.patch.object(jules_api, "collect_gh_auth_status", return_value={"installed": True, "authenticated": False}):
                    with mock.patch.object(jules_api, "collect_jules_cli_status", return_value={"installed": False, "path": None}):
                        with redirect_stdout(output):
                            jules_api.doctor(args)

        rendered = output.getvalue().strip()
        self.assertIn("merge_ready=no", rendered)
        self.assertIn("ready=yes", rendered)

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
        self.assertIn('"name": "a2"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
