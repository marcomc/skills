"""Offline review-body detection and existing anchor behavior regressions."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "detect_codex_review_anchor.py"
)
SPEC = importlib.util.spec_from_file_location("detector", SCRIPT)
assert SPEC and SPEC.loader
DETECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DETECTOR)
HEAD = "a" * 40
OLD_HEAD = "b" * 40
BOT = {"login": "chatgpt-codex-connector[bot]"}
URL = "https://github.com/example/project"


def location(path="source.py", head=HEAD):
    return f"{URL}/blob/{head}/{path}#L10-L12"


def heading(priority="P1", title="Validate the exact target", badge=True):
    if badge:
        return (
            f"**<sub><sub>![{priority} Badge](https://img.shields.io/badge/"
            f"{priority}-orange?style=flat)</sub></sub>  {title}**"
        )
    return f"**[{priority}] {title}**"


def body(
    priority="P1", title="Validate the exact target", path="source.py", badge=True
):
    return (
        f"\n### 💡 Codex Review\n\n{location(path)}\n"
        f"{heading(priority, title, badge)}\n\nRequire exact target validation.\n"
        "<details> <summary>ℹ️ About Codex in GitHub</summary>\n"
        "If Codex has suggestions, it will comment; otherwise it reacts.\n</details>"
    )


def review(text=None, review_id="review-current", head=HEAD):
    return {
        "id": review_id,
        "url": URL + "/pull/1#pullrequestreview-1",
        "body": body() if text is None else text,
        "state": "COMMENTED",
        "submittedAt": "2026-01-01T12:05:00Z",
        "author": BOT,
        "commit": {"oid": head},
    }


def fixture():
    return {
        "id": "pr",
        "url": URL + "/pull/1",
        "headRefOid": HEAD,
        "createdAt": "2026-01-01T10:00:00Z",
        "commits": {"nodes": [{"commit": {"committedDate": "2026-01-01T12:00:00Z"}}]},
        "reactionGroups": [],
        "reactions": {"nodes": []},
        "comments": {"nodes": []},
        "reviews": {"nodes": [review()]},
        "reviewThreads": {"nodes": []},
    }


def react(pr, content="EYES"):
    pr["reactionGroups"] = [{"content": content, "users": {"nodes": [BOT]}}]
    pr["reactions"] = {
        "nodes": [
            {"content": content, "user": BOT, "createdAt": "2026-01-01T12:10:00Z"}
        ]
    }


def inline(
    resolved=True,
    review_id="review-current",
    path="source.py",
    title="Validate the exact target",
):
    return {
        "id": "thread",
        "isResolved": resolved,
        "comments": {
            "nodes": [
                {
                    "id": "comment",
                    "url": URL + "/pull/1#discussion_r1",
                    "body": heading(title=title),
                    "author": BOT,
                    "path": path,
                    "line": 10,
                    "createdAt": "2026-01-01T12:05:00Z",
                    "pullRequestReview": {"id": review_id, "commit": {"oid": HEAD}},
                }
            ]
        },
    }


def run(pr, argv=None):
    answers = [
        {
            "number": 1,
            "url": pr["url"],
            "headRefName": "feature",
            "state": pr.get("state", "OPEN"),
            "mergedAt": pr.get("mergedAt"),
            "closedAt": pr.get("closedAt"),
        },
        {"owner": {"login": "example"}, "name": "project"},
        {"data": {"repository": {"pullRequest": pr}}},
    ]
    output = io.StringIO()
    with (
        patch.object(DETECTOR, "run_json", side_effect=answers),
        contextlib.redirect_stdout(output),
    ):
        assert DETECTOR.main(argv) == 0
    return json.loads(output.getvalue())


class ReviewBodyTests(unittest.TestCase):
    def test_body_only_actual_codex_shape_is_actionable(self):
        result = run(fixture())
        self.assertEqual(result["decision"], "fix_existing_feedback")
        self.assertEqual(result["unresolved_codex_threads"], [])
        (finding,) = result["actionable_codex_review_bodies"]
        self.assertEqual(
            (finding["priority"], finding["path"], finding["line"]),
            ("P1", "source.py", 10),
        )
        self.assertEqual(finding["review_id"], "review-current")
        self.assertEqual(finding["commit_oid"], HEAD)
        self.assertNotIn("<details>", finding["body"])

    def test_all_priority_badges_and_bracket_headings(self):
        for priority in ("P0", "P1", "P2", "P3"):
            for badge in (True, False):
                with self.subTest(priority=priority, badge=badge):
                    pr = fixture()
                    pr["reviews"]["nodes"][0]["body"] = body(
                        priority=priority, badge=badge
                    )
                    self.assertEqual(
                        run(pr)["actionable_codex_review_bodies"][0]["priority"],
                        priority,
                    )

    def test_location_after_heading(self):
        pr = fixture()
        pr["reviews"]["nodes"][0]["body"] = heading() + "\n\n" + location()
        self.assertEqual(run(pr)["decision"], "fix_existing_feedback")

    def test_body_precedes_eyes_clean_and_latest_trigger(self):
        for reaction in ("EYES", "THUMBS_UP"):
            pr = fixture()
            react(pr, reaction)
            pr["comments"]["nodes"] = [
                {
                    "id": "trigger",
                    "url": URL,
                    "body": "@codex review",
                    "createdAt": "2026-01-01T12:01:00Z",
                    "reactionGroups": [],
                }
            ]
            result = run(pr)
            self.assertEqual(result["decision"], "fix_existing_feedback")
            self.assertFalse(result["clean_signal_current"])

    def test_body_precedes_quota_message(self):
        pr = fixture()
        pr["comments"]["nodes"] = [
            {
                "id": "trigger",
                "url": URL,
                "body": "@codex review",
                "createdAt": "2026-01-01T12:01:00Z",
            },
            {
                "id": "quota",
                "url": URL,
                "body": "You have reached your Codex usage limits for code reviews.",
                "createdAt": "2026-01-01T12:06:00Z",
                "author": BOT,
            },
        ]
        self.assertEqual(run(pr)["decision"], "fix_existing_feedback")

    def test_old_commit_is_excluded_even_with_new_timestamp(self):
        pr = fixture()
        pr["reviews"]["nodes"][0]["commit"]["oid"] = OLD_HEAD
        self.assertEqual(run(pr)["actionable_codex_review_bodies"], [])

    def test_only_current_review_returned(self):
        pr = fixture()
        pr["reviews"]["nodes"].insert(0, review(review_id="old", head=OLD_HEAD))
        self.assertEqual(
            [f["review_id"] for f in run(pr)["actionable_codex_review_bodies"]],
            ["review-current"],
        )

    def test_unknown_or_mismatched_identity_is_not_current(self):
        for commit in ({}, None, {"oid": OLD_HEAD}, {"oid": HEAD[:7]}):
            pr = fixture()
            pr["reviews"]["nodes"][0]["commit"] = commit
            self.assertEqual(run(pr)["actionable_codex_review_bodies"], [])

    def test_nonbot_pending_dismissed_and_unsubmitted_excluded(self):
        for field, value in (
            ("author", {"login": "human"}),
            ("state", "PENDING"),
            ("state", "DISMISSED"),
            ("submittedAt", None),
        ):
            pr = fixture()
            pr["reviews"]["nodes"][0][field] = value
            self.assertEqual(run(pr)["actionable_codex_review_bodies"], [])

    def test_boilerplate_clean_empty_and_examples_excluded(self):
        for text in (
            "",
            "### Codex Review\nNo inline findings.",
            "Didn't find any major issues.",
            "Documentation mentions [P1] for priority.\n" + location(),
            "```markdown\n" + body() + "\n```",
            location("AGENTS.md"),
        ):
            pr = fixture()
            pr["reviews"]["nodes"][0]["body"] = text
            self.assertEqual(run(pr)["actionable_codex_review_bodies"], [])

    def test_priority_requires_source_location_on_same_repo_and_head(self):
        for link in (
            "",
            location().replace(HEAD, OLD_HEAD),
            location().replace("example/project", "other/project"),
        ):
            pr = fixture()
            pr["reviews"]["nodes"][0]["body"] = heading() + "\n" + link
            self.assertEqual(run(pr)["actionable_codex_review_bodies"], [])

    def test_two_findings_and_unresolved_inline_are_preserved(self):
        pr = fixture()
        pr["reviews"]["nodes"][0]["body"] = (
            body().split("<details>")[0]
            + "\n"
            + body(title="Second problem", path="other.py")
        )
        pr["reviewThreads"]["nodes"] = [inline(resolved=False)]
        result = run(pr)
        self.assertEqual(len(result["actionable_codex_review_bodies"]), 2)
        self.assertEqual(len(result["unresolved_codex_threads"]), 1)

    def test_resolved_exact_inline_duplicate_is_excluded(self):
        pr = fixture()
        pr["reviewThreads"]["nodes"] = [inline()]
        self.assertEqual(run(pr)["actionable_codex_review_bodies"], [])

    def test_resolved_duplicate_does_not_hide_second_body_finding(self):
        pr = fixture()
        pr["reviews"]["nodes"][0]["body"] = (
            body().split("<details>")[0]
            + "\n"
            + body(title="Second problem", path="other.py")
        )
        pr["reviewThreads"]["nodes"] = [inline()]
        self.assertEqual(
            [f["title"] for f in run(pr)["actionable_codex_review_bodies"]],
            ["Second problem"],
        )

    def test_same_title_other_review_path_line_priority_or_author_not_suppressed(self):
        for field, value in (
            ("pullRequestReview", {"id": "other-review"}),
            ("path", "other.py"),
            ("line", 11),
            ("body", heading(priority="P2")),
            ("author", {"login": "human"}),
        ):
            pr = fixture()
            thread = inline()
            thread["comments"]["nodes"][0][field] = value
            pr["reviewThreads"]["nodes"] = [thread]
            self.assertEqual(run(pr)["decision"], "fix_existing_feedback")

    def test_next_finding_location_does_not_attach_to_unlocated_heading(self):
        pr = fixture()
        pr["reviews"]["nodes"][0]["body"] = (
            heading(title="No location")
            + "\n\n"
            + location("other.py")
            + "\n"
            + heading(title="Located finding")
        )
        self.assertEqual(
            [f["title"] for f in run(pr)["actionable_codex_review_bodies"]],
            ["Located finding"],
        )

    def test_query_includes_review_and_thread_identity(self):
        self.assertIn("submittedAt\n          commit { oid }", DETECTOR.QUERY)
        self.assertIn("pullRequestReview { id commit { oid } }", DETECTOR.QUERY)
        self.assertIn("pageInfo { hasNextPage endCursor }", DETECTOR.QUERY)

    def test_unresolved_inline_exposes_the_actionable_finding(self):
        pr = fixture()
        pr["reviews"]["nodes"] = []
        pr["reviewThreads"]["nodes"] = [inline(resolved=False)]
        (finding,) = run(pr)["unresolved_codex_threads"]
        self.assertEqual(finding["review_id"], "review-current")
        self.assertEqual(finding["review_commit_oid"], HEAD)
        self.assertEqual(finding["head_relation"], "current")
        self.assertEqual(finding["priority"], "P1")
        self.assertEqual(finding["title"], "Validate the exact target")
        self.assertIn("Validate the exact target", finding["body"])

    def test_later_review_thread_pages_are_collected(self):
        pr = fixture()
        pr["reviewThreads"] = {
            "nodes": [],
            "pageInfo": {"hasNextPage": True, "endCursor": "page-one"},
        }
        next_page = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "reviewThreads": {
                            "nodes": [inline(resolved=False)],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                        }
                    }
                }
            }
        }
        with patch.object(DETECTOR, "run_json", return_value=next_page) as mocked:
            DETECTOR.collect_remaining_review_threads("example", "project", 1, pr)
        self.assertEqual(len(pr["reviewThreads"]["nodes"]), 1)
        self.assertIn("cursor=page-one", mocked.call_args.args[0])


class ExistingBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.pr = fixture()
        self.pr["reviews"]["nodes"] = []

    def test_idle_posts_and_eyes_monitors(self):
        self.assertEqual(run(self.pr)["decision"], "post_codex_review")
        react(self.pr)
        result = run(self.pr)
        self.assertEqual(result["decision"], "monitor_existing_pass")
        self.assertEqual(result["review_observation"]["phase"], "running")
        self.assertFalse(result["review_observation"]["terminal"])

    def test_unresolved_thread_keeps_existing_feedback(self):
        self.pr["reviewThreads"]["nodes"] = [inline(resolved=False)]
        self.assertEqual(run(self.pr)["decision"], "fix_existing_feedback")

    def test_completed_description_signal_supersedes_current_trigger(self):
        self.pr["comments"]["nodes"] = [
            {
                "id": "trigger",
                "url": URL,
                "body": "@codex review",
                "createdAt": "2026-01-01T12:01:00Z",
                "reactionGroups": [],
            }
        ]
        self.assertEqual(run(self.pr)["decision"], "monitor_existing_pass")
        react(self.pr, "THUMBS_UP")
        result = run(
            self.pr, ["--review-head", HEAD, "--review-start", "2026-01-01T12:01:00Z"]
        )
        self.assertTrue(result["clean_signal_current"])
        self.assertEqual(result["decision"], "clean_signal")
        react(self.pr, "EYES")
        self.assertEqual(run(self.pr)["decision"], "monitor_existing_pass")

    def test_current_and_stale_description_clean_reactions(self):
        self.pr["reviews"]["nodes"] = [review("Didn't find any major issues.")]
        react(self.pr, "THUMBS_UP")
        self.assertTrue(run(self.pr)["clean_signal_current"])
        self.pr["reactions"]["nodes"][0]["createdAt"] = "2026-01-01T11:00:00Z"
        self.assertFalse(run(self.pr)["clean_signal_current"])

    def test_existing_variant_summary_and_quota_contracts(self):
        installed_behavior = hasattr(DETECTOR, "usage_limit_comment")
        self.pr["reviews"]["nodes"] = [review("Didn't find any major issues.")]
        self.assertEqual(
            DETECTOR.clean_signal_is_current(self.pr, None), not installed_behavior
        )
        self.pr["reviews"]["nodes"] = []
        self.pr["comments"]["nodes"] = [
            {
                "id": "trigger",
                "url": URL,
                "body": "@codex review",
                "createdAt": "2026-01-01T12:01:00Z",
            },
            {
                "id": "quota",
                "url": URL,
                "body": "You have reached your Codex usage limits for code reviews.",
                "createdAt": "2026-01-01T12:06:00Z",
                "author": BOT,
            },
        ]
        self.assertEqual(
            run(self.pr)["decision"],
            "usage_limit_blocked" if installed_behavior else "post_codex_review",
        )
        self.pr["comments"]["nodes"].pop()
        self.assertEqual(
            run(self.pr)["decision"],
            "monitor_existing_pass" if installed_behavior else "post_codex_review",
        )

    def test_current_clean_summary_without_reaction_needs_confirmation(self):
        self.pr["reviews"]["nodes"] = [review("Didn't find any major issues.")]
        result = run(self.pr)
        self.assertEqual(result["decision"], "verify_clean_signal")
        self.assertEqual(
            result["review_observation"]["phase"], "clean_confirmation_pending"
        )
        self.assertIn("do not post another", result["review_observation"]["next_action"])

    def test_closed_pr_does_not_keep_the_loop_running(self):
        self.pr["state"] = "MERGED"
        self.pr["mergedAt"] = "2026-01-01T12:30:00Z"
        result = run(self.pr)
        self.assertEqual(result["decision"], "review_closed")
        self.assertEqual(result["review_observation"]["phase"], "closed")
        self.assertTrue(result["review_observation"]["terminal"])


class PassIdentityTests(unittest.TestCase):
    def setUp(self):
        self.pr = fixture()
        self.pr["reviews"]["nodes"] = []
        react(self.pr, "THUMBS_UP")

    def request(self):
        return {
            "id": "trigger",
            "url": URL,
            "body": "@codex review",
            "createdAt": "2026-01-01T12:11:00Z",
            "reactionGroups": [],
        }

    def test_unbound_thumb_requires_head_association(self):
        result = run(self.pr)
        self.assertEqual(result["decision"], "verify_clean_signal")
        self.assertFalse(result["clean_signal_current"])

    def test_recorded_pass_binds_head_and_later_reaction(self):
        args = ["--review-head", HEAD, "--review-start", "2026-01-01T12:01:00Z"]
        self.assertEqual(run(self.pr, args)["decision"], "clean_signal")
        args[1] = OLD_HEAD
        self.assertFalse(run(self.pr, args)["clean_signal_current"])
        args[1] = HEAD
        args[3] = "2026-01-01T12:11:00Z"
        self.assertFalse(run(self.pr, args)["clean_signal_current"])

    def test_new_recorded_pass_supersedes_older_head_summary(self):
        self.pr["reviews"]["nodes"] = [
            review("Didn't find any major issues.", head=OLD_HEAD)
        ]
        args = ["--review-head", HEAD, "--review-start", "2026-01-01T12:06:00Z"]
        self.assertEqual(run(self.pr, args)["decision"], "clean_signal")
        self.pr["commits"]["nodes"][0]["commit"]["committedDate"] = (
            "2026-01-01T12:15:00Z"
        )
        self.assertEqual(run(self.pr, args)["decision"], "clean_signal")
        args[3] = "2026-01-01T12:01:00Z"
        self.assertFalse(run(self.pr, args)["clean_signal_current"])

    def test_new_silent_request_supersedes_old_clean(self):
        self.pr["comments"]["nodes"] = [self.request()]
        result = run(self.pr)
        self.assertEqual(result["decision"], "monitor_existing_pass")
        self.assertEqual(result["review_observation"]["phase"], "requested_unacknowledged")
        self.assertFalse(result["clean_signal_current"])

    def test_new_quota_not_suppressed_by_historical_reaction(self):
        self.pr["comments"]["nodes"] = [
            self.request(),
            {
                "id": "quota",
                "url": URL,
                "author": BOT,
                "body": "You have reached your Codex usage limits for code reviews.",
                "createdAt": "2026-01-01T12:12:00Z",
            },
        ]
        self.assertEqual(run(self.pr)["decision"], "usage_limit_blocked")
        react(self.pr, "EYES")
        self.pr["reactions"]["nodes"][0]["createdAt"] = "2026-01-01T12:13:00Z"
        self.assertEqual(run(self.pr)["decision"], "monitor_existing_pass")

    def test_explicit_other_head_overrides_commit_date_heuristic(self):
        self.pr["reviews"]["nodes"] = [
            review("Didn't find any major issues.", head=OLD_HEAD)
        ]
        self.assertEqual(run(self.pr)["decision"], "post_codex_review")
        self.assertFalse(run(self.pr)["clean_signal_current"])

    def test_current_issue_comment_finding_prevents_clean(self):
        self.pr["comments"]["nodes"] = [
            {
                "id": "body-comment",
                "url": URL,
                "body": body(),
                "author": BOT,
                "createdAt": "2026-01-01T12:11:00Z",
            }
        ]
        result = run(self.pr)
        self.assertEqual(result["decision"], "fix_existing_feedback")
        self.assertEqual(
            result["actionable_codex_review_bodies"][0]["path"], "source.py"
        )
        self.assertFalse(result["clean_signal_current"])
        for invalid in [
            body().replace(HEAD, OLD_HEAD),
            "```\n" + body() + "\n```",
            body().replace("example/project", "other/project"),
        ]:
            self.pr["comments"]["nodes"][0]["body"] = invalid
            self.assertEqual(run(self.pr)["actionable_codex_review_bodies"], [])

    def test_clean_flag_false_when_inline_feedback_or_eyes_remain(self):
        self.pr["reviews"]["nodes"] = [review("Didn't find any major issues.")]
        self.pr["reviewThreads"]["nodes"] = [inline(resolved=False)]
        self.assertFalse(run(self.pr)["clean_signal_current"])
        self.pr["reviewThreads"]["nodes"] = []
        react(self.pr, "EYES")
        self.assertFalse(run(self.pr)["clean_signal_current"])

    def test_quoted_request_is_not_a_new_pass(self):
        comment = self.request()
        comment["body"] = "Do not post another @codex review until validation passes."
        self.pr["comments"]["nodes"] = [comment]
        self.assertEqual(DETECTOR.review_request_comments(self.pr), [])


if __name__ == "__main__":
    unittest.main()
