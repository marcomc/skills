#!/usr/bin/env python3
"""Detect the active Codex review anchor for the current GitHub PR."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from typing import Any
from urllib.parse import unquote

BOT_LOGINS = {
    "chatgpt-codex-connector",
    "chatgpt-codex-connector[bot]",
}
REVIEW_REQUEST_RE = re.compile(r"(?<!\w)@codex\s+review\b", re.IGNORECASE)
USAGE_LIMIT_TEXT = "you have reached your codex usage limits for code reviews"

CLEAN_TEXT = "didn't find any major issues"
REVIEWED_COMMIT_RE = re.compile(r"\*\*Reviewed commit:\*\*\s*`?([0-9a-fA-F]{7,40})`?")


QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      id
      number
      url
      createdAt
      headRefOid
      commits(last: 1) {
        nodes {
          commit {
            oid
            committedDate
          }
        }
      }
      reactionGroups {
        content
        users(first: 100) { nodes { login } }
      }
      reactions(first: 100) {
        nodes {
          content
          createdAt
          user { login }
        }
      }
      comments(last: 100) {
        nodes {
          id
          url
          body
          createdAt
          author { login }
          reactionGroups {
            content
            users(first: 100) { nodes { login } }
          }
          reactions(first: 100) {
            nodes {
              content
              createdAt
              user { login }
            }
          }
        }
      }
      reviewThreads(first: 100) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          comments(first: 20) {
            nodes {
              id
              url
              body
              path
              line
              pullRequestReview { id commit { oid } }
              createdAt
              author { login }
            }
          }
        }
      }
      reviews(last: 100) {
        nodes {
          id
          url
          body
          state
          submittedAt
          commit { oid }
          author { login }
        }
      }
    }
  }
}
"""


THREADS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $cursor: String!) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          comments(first: 20) {
            nodes {
              id
              url
              body
              path
              line
              pullRequestReview { id commit { oid } }
              createdAt
              author { login }
            }
          }
        }
      }
    }
  }
}
"""


# Codex's finding headings are deliberately narrower than arbitrary Markdown.
FINDING_HEADING_RE = re.compile(
    r"^(?:#{1,6}\s+)?(?:\*\*)?(?:<sub>)*\s*"
    r"(?:!\[P(?P<badge>[0-3]) Badge\]\(https://img\.shields\.io/badge/"
    r"P(?P=badge)-[^)\s]+\)|\[P(?P<plain>[0-3])\])"
    r"(?:</sub>)*\s+(?P<title>\S.*)$"
)
SOURCE_LOCATION_RE = re.compile(
    r"https://[^\s<>()[\]]+/blob/(?P<commit>[0-9a-fA-F]{40})/"
    r"(?P<path>[^\s<>()[\]#]+)#L(?P<line>\d+)(?:-L(?P<end_line>\d+))?"
)


def finding_blocks(body: str) -> list[dict[str, Any]]:
    """Read Codex priority headings, ignoring examples inside fenced code."""
    lines = body.splitlines()
    headings = []
    fence = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        fence_match = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence_match:
            marker = fence_match.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        match = FINDING_HEADING_RE.fullmatch(stripped)
        if match:
            title = match.group("title").removesuffix("**").strip()
            headings.append(
                (index, "P" + (match.group("badge") or match.group("plain")), title)
            )
    blocks = []
    for position, (start, priority, title) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        # A following finding's preceding URL must not supply this one's location.
        next_location = end - 1
        while next_location > start and not lines[next_location].strip():
            next_location -= 1
        if position + 1 < len(headings) and SOURCE_LOCATION_RE.fullmatch(
            lines[next_location].strip()
        ):
            end = next_location
        # Codex also puts a bare blob URL immediately before the heading.
        previous = start - 1
        while previous >= 0 and not lines[previous].strip():
            previous -= 1
        preceding = lines[previous].strip() if previous >= 0 else ""
        block = "\n".join(lines[start:end]).split("<details>", 1)[0].strip()
        location_text = (
            preceding + "\n" + block
            if SOURCE_LOCATION_RE.fullmatch(preceding)
            else block
        )
        blocks.append(
            {
                "priority": priority,
                "title": title,
                "body": block,
                "locations": list(SOURCE_LOCATION_RE.finditer(location_text)),
            }
        )
    return blocks


def normalized_finding_title(title: str) -> str:
    return " ".join(title.replace("`", "").replace("**", "").casefold().split())


def actionable_codex_review_bodies(pr: dict[str, Any]) -> list[dict[str, Any]]:
    """Return exact-head body findings unless a matching inline thread is resolved."""
    head = pr.get("headRefOid", "")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", head):
        return []
    source_prefix = str(pr.get("url", "")).split("/pull/", 1)[0] + "/blob/"
    resolved = set()
    for thread in pr.get("reviewThreads", {}).get("nodes", []):
        if not thread.get("isResolved"):
            continue
        for comment in thread.get("comments", {}).get("nodes", []):
            if comment.get("author", {}).get("login") not in BOT_LOGINS:
                continue
            for block in finding_blocks(str(comment.get("body", ""))):
                resolved.add(
                    (
                        (comment.get("pullRequestReview") or {}).get("id"),
                        block["priority"],
                        normalized_finding_title(block["title"]),
                        comment.get("path"),
                        comment.get("line"),
                    )
                )
    findings = []
    reviews = list(pr.get("reviews", {}).get("nodes", []))
    # Issue comments have no review commit field; exact same-repo/head blob links
    # below supply location identity. Keep their IDs distinct from inline reviews.
    reviews.extend(
        {
            **comment,
            "state": "COMMENTED",
            "submittedAt": comment.get("createdAt"),
            "commit": {"oid": head},
            "issue_comment": True,
        }
        for comment in pr.get("comments", {}).get("nodes", [])
    )
    for review in reviews:
        if (
            review.get("author", {}).get("login") not in BOT_LOGINS
            or review.get("state") not in {"COMMENTED", "CHANGES_REQUESTED", "APPROVED"}
            or not review.get("submittedAt")
            or (review.get("commit") or {}).get("oid", "").lower() != head.lower()
        ):
            continue
        for block in finding_blocks(str(review.get("body", ""))):
            location = next(
                (
                    match
                    for match in block["locations"]
                    if match.group(0).startswith(source_prefix)
                    and match.group("commit").lower() == head.lower()
                ),
                None,
            )
            if location is None:
                continue
            path = unquote(location.group("path"))
            line = int(location.group("line"))
            key = (
                review.get("id"),
                block["priority"],
                normalized_finding_title(block["title"]),
                path,
                line,
            )
            if not review.get("issue_comment") and key in resolved:
                continue
            findings.append(
                {
                    "review_id": review.get("id"),
                    "url": review.get("url"),
                    "submitted_at": review["submittedAt"],
                    "commit_oid": head,
                    "priority": block["priority"],
                    "title": block["title"],
                    "path": path,
                    "line": line,
                    "body": block["body"],
                }
            )
    return findings


def run_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def collect_remaining_review_threads(
    owner: str, name: str, number: int, pr: dict[str, Any]
) -> None:
    """Fetch every inline thread: a later finding is still actionable feedback."""
    connection = pr.get("reviewThreads") or {}
    page_info = connection.get("pageInfo") or {}
    while page_info.get("hasNextPage"):
        cursor = page_info.get("endCursor")
        if not cursor:
            raise ValueError("reviewThreads reports another page without an end cursor")
        data = run_json(
            [
                "gh",
                "api",
                "graphql",
                "-f",
                f"query={THREADS_QUERY}",
                "-f",
                f"owner={owner}",
                "-f",
                f"name={name}",
                "-F",
                f"number={number}",
                "-f",
                f"cursor={cursor}",
            ]
        )
        next_connection = data["data"]["repository"]["pullRequest"][
            "reviewThreads"
        ]
        connection.setdefault("nodes", []).extend(next_connection.get("nodes", []))
        page_info = next_connection.get("pageInfo") or {}
    pr["reviewThreads"] = connection


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def bot_reacted(groups: list[dict[str, Any]], content: str) -> bool:
    for group in groups:
        if group.get("content") != content:
            continue
        users = group.get("users", {}).get("nodes", [])
        if any(user.get("login") in BOT_LOGINS for user in users):
            return True
    return False


def bot_has_any_reaction(groups: list[dict[str, Any]]) -> bool:
    return any(
        any(
            user.get("login") in BOT_LOGINS
            for user in group.get("users", {}).get("nodes", [])
        )
        for group in groups
    )


def bot_reaction_time(reactions: dict[str, Any], content: str) -> datetime | None:
    reaction_times = []
    for reaction in reactions.get("nodes", []):
        if reaction.get("content") != content:
            continue
        if reaction.get("user", {}).get("login") not in BOT_LOGINS:
            continue
        reaction_times.append(parse_time(reaction["createdAt"]))
    if not reaction_times:
        return None
    return max(reaction_times)


def anchor_state(groups: list[dict[str, Any]]) -> str:
    has_eyes = bot_reacted(groups, "EYES")
    has_plus = bot_reacted(groups, "THUMBS_UP")
    if has_eyes:
        return "in_progress"
    if has_plus:
        return "clean_signal"
    return "no_signal"


def latest_commit_time(pr: dict[str, Any]) -> datetime | None:
    nodes = pr.get("commits", {}).get("nodes", [])
    if not nodes:
        return None
    committed_date = nodes[-1].get("commit", {}).get("committedDate")
    if not committed_date:
        return None
    return parse_time(committed_date)


def reviewed_commit_matches_head(body: str, head_ref_oid: str) -> bool:
    match = REVIEWED_COMMIT_RE.search(body)
    if not match:
        return False
    reviewed_commit = match.group(1).lower()
    head = head_ref_oid.lower()
    return head.startswith(reviewed_commit) or reviewed_commit.startswith(head)


def codex_clean_summary_is_current(
    body: str,
    created_at: str | None,
    head_ref_oid: str,
    current_head_time: datetime | None,
) -> bool:
    if CLEAN_TEXT not in body.lower():
        return False
    if REVIEWED_COMMIT_RE.search(body):
        return reviewed_commit_matches_head(body, head_ref_oid)
    if current_head_time is None or created_at is None:
        return False
    return parse_time(created_at) >= current_head_time


def has_current_clean_summary(pr: dict[str, Any]) -> bool:
    head_ref_oid = pr.get("headRefOid", "")
    current_head_time = latest_commit_time(pr)
    comments = pr.get("comments", {}).get("nodes", [])
    reviews = pr.get("reviews", {}).get("nodes", [])
    candidates = [
        (comment.get("body", ""), comment.get("createdAt"))
        for comment in comments
        if comment.get("author", {}).get("login") in BOT_LOGINS
    ]
    candidates.extend(
        (review.get("body", ""), review.get("submittedAt"))
        for review in reviews
        if review.get("author", {}).get("login") in BOT_LOGINS
        and (review.get("commit") or {}).get("oid", "").lower()
        == head_ref_oid.lower()
    )
    return any(
        codex_clean_summary_is_current(
            str(body),
            created_at,
            head_ref_oid,
            current_head_time,
        )
        for body, created_at in candidates
    )


def clean_signal_is_current(
    pr: dict[str, Any],
    anchor: dict[str, Any] | None,
    review_head: str | None = None,
    review_start: str | None = None,
) -> bool:
    if (
        not anchor
        or anchor.get("type") != "PR description timeline comment"
        or anchor.get("state") != "clean_signal"
    ):
        return False
    clean_signal_at = anchor.get("clean_signal_at")
    current_head_time = latest_commit_time(pr)
    if not clean_signal_at:
        return False
    clean_time = parse_time(clean_signal_at)
    requests = review_request_comments(pr)
    if requests and parse_time(requests[-1]["createdAt"]) > clean_time:
        return False
    # A backdated/reused commit date cannot override explicit contrary identity.
    identified = []
    for record in pr.get("reviews", {}).get("nodes", []):
        if record.get("author", {}).get("login") not in BOT_LOGINS or not record.get(
            "submittedAt"
        ):
            continue
        oid = (record.get("commit") or {}).get("oid")
        if oid and CLEAN_TEXT in str(record.get("body", "")).lower():
            identified.append((parse_time(record["submittedAt"]), oid.lower()))
    for record in pr.get("comments", {}).get("nodes", []):
        if record.get("author", {}).get("login") not in BOT_LOGINS:
            continue
        match = REVIEWED_COMMIT_RE.search(str(record.get("body", "")))
        if match and CLEAN_TEXT in str(record.get("body", "")).lower():
            identified.append((parse_time(record["createdAt"]), match.group(1).lower()))
    recorded_start = None
    if (
        review_head
        and review_head.lower() == pr.get("headRefOid", "").lower()
        and review_start
    ):
        start = parse_time(review_start)
        if start <= clean_time:
            recorded_start = start
    if identified:
        identified_at, reviewed = max(identified)
        if not pr.get("headRefOid", "").lower().startswith(reviewed):
            if recorded_start is None or identified_at >= recorded_start:
                return False
        elif identified_at <= clean_time:
            return True
    if recorded_start is not None:
        return True
    return current_head_time is not None and clean_time >= current_head_time


def clean_head_binding(
    pr: dict[str, Any],
    anchor: dict[str, Any] | None,
    review_head: str | None,
    review_start: str | None,
) -> str | None:
    """Bind a candidate reaction to a recorded pass or explicit review commit."""
    if not clean_signal_is_current(pr, anchor, review_head, review_start):
        return None
    head = pr.get("headRefOid", "").lower()
    if (
        review_head
        and review_head.lower() == head
        and review_start
        and parse_time(review_start) <= parse_time(anchor["clean_signal_at"])
    ):
        return "recorded_pass"
    for review in pr.get("reviews", {}).get("nodes", []):
        if (
            review.get("author", {}).get("login") in BOT_LOGINS
            and (review.get("commit") or {}).get("oid", "").lower() == head
            and review.get("state") in {"COMMENTED", "APPROVED"}
            and review.get("submittedAt")
            and CLEAN_TEXT in str(review.get("body", "")).lower()
        ):
            return "review_commit"
    for comment in pr.get("comments", {}).get("nodes", []):
        text = str(comment.get("body", ""))
        if (
            comment.get("author", {}).get("login") in BOT_LOGINS
            and CLEAN_TEXT in text.lower()
            and reviewed_commit_matches_head(text, head)
        ):
            return "summary_commit"
    return None


def review_request_comments(pr: dict[str, Any]) -> list[dict[str, Any]]:
    comments = pr.get("comments", {}).get("nodes", [])
    anchors = [
        comment
        for comment in comments
        if REVIEW_REQUEST_RE.fullmatch(str(comment.get("body", "")).strip())
    ]
    return sorted(anchors, key=lambda item: parse_time(item["createdAt"]))


def latest_review_request_is_current(pr: dict[str, Any]) -> bool:
    requests = review_request_comments(pr)
    head_time = latest_commit_time(pr)
    if not requests or head_time is None:
        return False
    return parse_time(requests[-1]["createdAt"]) >= head_time


def usage_limit_comment(pr: dict[str, Any]) -> dict[str, Any] | None:
    requests = review_request_comments(pr)
    if not requests:
        return None
    latest_request_at = parse_time(requests[-1]["createdAt"])
    comments = pr.get("comments", {}).get("nodes", [])
    candidates = [
        comment
        for comment in comments
        if comment.get("author", {}).get("login") in BOT_LOGINS
        and USAGE_LIMIT_TEXT in str(comment.get("body", "")).lower()
        and parse_time(comment["createdAt"]) > latest_request_at
    ]
    if not candidates:
        return None
    comment = max(candidates, key=lambda item: parse_time(item["createdAt"]))
    quota_time = parse_time(comment["createdAt"])
    later_evidence = [
        parse_time(reaction["createdAt"])
        for reaction in pr.get("reactions", {}).get("nodes", [])
        if reaction.get("user", {}).get("login") in BOT_LOGINS
        and reaction.get("createdAt")
    ]
    for review in pr.get("reviews", {}).get("nodes", []):
        if review.get("author", {}).get("login") in BOT_LOGINS and review.get(
            "submittedAt"
        ):
            later_evidence.append(parse_time(review["submittedAt"]))
    for issue_comment in comments:
        if issue_comment.get("author", {}).get("login") not in BOT_LOGINS:
            continue
        if USAGE_LIMIT_TEXT in str(issue_comment.get("body", "")).lower():
            continue
        later_evidence.append(parse_time(issue_comment["createdAt"]))
    for thread in pr.get("reviewThreads", {}).get("nodes", []):
        for thread_comment in thread.get("comments", {}).get("nodes", []):
            if thread_comment.get("author", {}).get("login") in BOT_LOGINS:
                later_evidence.append(parse_time(thread_comment["createdAt"]))
    if any(evidence_time > quota_time for evidence_time in later_evidence):
        return None
    return {
        "id": comment["id"],
        "url": comment["url"],
        "created_at": comment["createdAt"],
        "body": comment.get("body", ""),
        "after_request_id": requests[-1]["id"],
    }


def unresolved_codex_threads(pr: dict[str, Any]) -> list[dict[str, Any]]:
    """Return complete, current-head feedback ready for one closure batch."""
    head = pr.get("headRefOid", "")
    threads = []
    for thread in pr.get("reviewThreads", {}).get("nodes", []):
        if thread.get("isResolved"):
            continue
        comments = thread.get("comments", {}).get("nodes", [])
        bot_comments = [
            comment
            for comment in comments
            if comment.get("author", {}).get("login") in BOT_LOGINS
        ]
        if bot_comments:
            latest = max(bot_comments, key=lambda comment: comment.get("createdAt", ""))
            blocks = finding_blocks(str(latest.get("body", "")))
            finding = blocks[0] if blocks else None
            review = latest.get("pullRequestReview") or {}
            review_commit = (review.get("commit") or {}).get("oid")
            threads.append(
                {
                    "thread_id": thread.get("id"),
                    "url": latest.get("url"),
                    "path": latest.get("path"),
                    "line": latest.get("line"),
                    "created_at": latest.get("createdAt"),
                    "review_id": review.get("id"),
                    "review_commit_oid": review_commit,
                    "head_relation": (
                        "current"
                        if review_commit and review_commit.lower() == head.lower()
                        else "older_or_unbound"
                    ),
                    "priority": finding.get("priority") if finding else None,
                    "title": finding.get("title") if finding else None,
                    "body": finding.get("body") if finding else latest.get("body", ""),
                }
            )
    return threads


def latest_bot_activity_at(pr: dict[str, Any]) -> str | None:
    """Return the latest observable Codex event, not a guessed completion time."""
    timestamps = []
    for reaction in pr.get("reactions", {}).get("nodes", []):
        if reaction.get("user", {}).get("login") in BOT_LOGINS and reaction.get(
            "createdAt"
        ):
            timestamps.append(reaction["createdAt"])
    for comment in pr.get("comments", {}).get("nodes", []):
        if comment.get("author", {}).get("login") in BOT_LOGINS and comment.get(
            "createdAt"
        ):
            timestamps.append(comment["createdAt"])
    for review in pr.get("reviews", {}).get("nodes", []):
        if review.get("author", {}).get("login") in BOT_LOGINS and review.get(
            "submittedAt"
        ):
            timestamps.append(review["submittedAt"])
    for thread in pr.get("reviewThreads", {}).get("nodes", []):
        for comment in thread.get("comments", {}).get("nodes", []):
            if comment.get("author", {}).get("login") in BOT_LOGINS and comment.get(
                "createdAt"
            ):
                timestamps.append(comment["createdAt"])
    return max(timestamps, key=parse_time) if timestamps else None


def review_observation(
    decision: str,
    anchor: dict[str, Any] | None,
) -> dict[str, Any]:
    """Make non-terminal review states explicit for an unattended loop runner."""
    if decision == "review_closed":
        return {
            "phase": "closed",
            "terminal": True,
            "next_action": "Do not request, push, or monitor another review; report the closed PR outcome.",
        }
    if decision == "fix_existing_feedback":
        return {
            "phase": "feedback_ready",
            "terminal": False,
            "next_action": "Read the full finding snapshot, make one complete closure batch, then validate it locally.",
        }
    if decision == "usage_limit_blocked":
        return {
            "phase": "quota_blocked",
            "terminal": False,
            "next_action": "Preserve the current head and wait for review quota; do not infer a clean result.",
        }
    if decision == "verify_clean_signal":
        return {
            "phase": "clean_confirmation_pending",
            "terminal": False,
            "next_action": "Verify a current-head clean signal; do not post another @codex review yet.",
        }
    if decision == "monitor_existing_pass":
        phase = (
            "running"
            if anchor and anchor.get("state") == "in_progress"
            else "requested_unacknowledged"
        )
        return {
            "phase": phase,
            "terminal": False,
            "next_action": "Keep observing this exact head. Silence or a polling timeout is not completion.",
        }
    if decision == "clean_signal":
        return {
            "phase": "clean",
            "terminal": True,
            "next_action": "The current head has a bound clean signal; finish the review loop.",
        }
    return {
        "phase": "not_requested",
        "terminal": False,
        "next_action": "Record the current head and request exactly one Codex review pass.",
    }


def active_anchor(pr: dict[str, Any]) -> dict[str, Any] | None:
    description_state = anchor_state(pr.get("reactionGroups", []))
    description_anchor = None
    if description_state != "no_signal":
        clean_signal_at = bot_reaction_time(pr.get("reactions", {}), "THUMBS_UP")
        description_anchor = {
            "type": "PR description timeline comment",
            "id": pr["id"],
            "url": pr["url"],
            "created_at": pr["createdAt"],
            "state": description_state,
            "clean_signal_at": clean_signal_at.isoformat() if clean_signal_at else None,
        }

    dedicated = []
    for comment in review_request_comments(pr):
        clean_signal_at = bot_reaction_time(comment.get("reactions", {}), "THUMBS_UP")
        dedicated.append(
            {
                "type": "@codex review comment",
                "id": comment["id"],
                "url": comment["url"],
                "created_at": comment["createdAt"],
                "state": anchor_state(comment.get("reactionGroups", [])),
                "clean_signal_at": clean_signal_at.isoformat()
                if clean_signal_at
                else None,
            }
        )
    active_dedicated = [item for item in dedicated if item["state"] != "no_signal"]
    if description_anchor and description_state == "in_progress":
        return description_anchor
    if description_anchor and description_state == "clean_signal":
        clean_signal_at = description_anchor.get("clean_signal_at")
        newer_in_progress = [
            item
            for item in active_dedicated
            if item["state"] == "in_progress"
            and (
                not clean_signal_at
                or parse_time(item["created_at"]) > parse_time(clean_signal_at)
            )
        ]
        if not newer_in_progress:
            return description_anchor
        return newer_in_progress[-1]
    if active_dedicated:
        return active_dedicated[-1]
    if description_anchor:
        return description_anchor
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-head", help="Head recorded when this pass started")
    parser.add_argument("--review-start", help="UTC timestamp recorded for that pass")
    args = parser.parse_args([] if argv is None else argv)
    if bool(args.review_head) != bool(args.review_start):
        parser.error("--review-head and --review-start must be supplied together")
    if args.review_head:
        if not re.fullmatch(r"[0-9a-fA-F]{40}", args.review_head):
            parser.error("--review-head must be a full commit SHA")
        try:
            if parse_time(args.review_start).tzinfo is None:
                parser.error("--review-start requires a timezone")
        except ValueError:
            parser.error("--review-start must be an ISO timestamp")
    pr_view = run_json(
        ["gh", "pr", "view", "--json", "number,url,headRefName,state,mergedAt,closedAt"]
    )
    repo_view = run_json(["gh", "repo", "view", "--json", "owner,name"])
    owner = repo_view["owner"]["login"]
    name = repo_view["name"]
    number = pr_view["number"]
    data = run_json(
        [
            "gh",
            "api",
            "graphql",
            "-f",
            f"query={QUERY}",
            "-f",
            f"owner={owner}",
            "-f",
            f"name={name}",
            "-F",
            f"number={number}",
        ]
    )
    pr = data["data"]["repository"]["pullRequest"]
    collect_remaining_review_threads(owner, name, number, pr)
    threads = unresolved_codex_threads(pr)
    body_findings = actionable_codex_review_bodies(pr)
    anchor = active_anchor(pr)
    usage_limit = usage_limit_comment(pr)
    binding = clean_head_binding(pr, anchor, args.review_head, args.review_start)
    clean_summary = has_current_clean_summary(pr)

    if pr_view.get("state") not in {None, "OPEN"}:
        decision = "review_closed"
    elif threads or body_findings:
        decision = "fix_existing_feedback"
    elif usage_limit:
        decision = "usage_limit_blocked"
    elif anchor and anchor["state"] == "in_progress":
        decision = "monitor_existing_pass"
    elif (
        anchor
        and anchor["state"] == "clean_signal"
        and clean_signal_is_current(pr, anchor, args.review_head, args.review_start)
    ):
        decision = "clean_signal" if binding else "verify_clean_signal"
    elif clean_summary:
        decision = "verify_clean_signal"
    elif latest_review_request_is_current(pr):
        decision = "monitor_existing_pass"
    else:
        decision = "post_codex_review"
    observation = review_observation(decision, anchor)

    print(
        json.dumps(
            {
                "decision": decision,
                "pr": {
                    "number": number,
                    "url": pr_view["url"],
                    "branch": pr_view["headRefName"],
                    "head_ref_oid": pr.get("headRefOid"),
                    "state": pr_view.get("state", "OPEN"),
                    "merged_at": pr_view.get("mergedAt"),
                    "closed_at": pr_view.get("closedAt"),
                },
                "active_anchor": anchor,
                "clean_signal_current": decision == "clean_signal",
                "clean_head_binding": binding,
                "clean_summary_current": clean_summary,
                "latest_bot_activity_at": latest_bot_activity_at(pr),
                "review_observation": observation,
                "usage_limit_blocked": usage_limit,
                "unresolved_codex_threads": threads,
                "actionable_codex_review_bodies": body_findings,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr or str(exc))
        raise SystemExit(exc.returncode)
