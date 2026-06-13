#!/usr/bin/env python3
"""Detect the active Codex review anchor for the current GitHub PR."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from typing import Any

BOT_LOGINS = {
    "chatgpt-codex-connector",
    "chatgpt-codex-connector[bot]",
}

CLEAN_TEXT = "didn't find any major issues"
REVIEWED_COMMIT_RE = re.compile(
    r"\*\*Reviewed commit:\*\*\s*`?([0-9a-fA-F]{7,40})`?"
)


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
              createdAt
              author { login }
            }
          }
        }
      }
      reviews(last: 50) {
        nodes {
          id
          url
          body
          state
          submittedAt
          author { login }
        }
      }
    }
  }
}
"""


def run_json(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


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
    pr: dict[str, Any], anchor: dict[str, Any] | None
) -> bool:
    if has_current_clean_summary(pr):
        return True
    if not anchor:
        return False
    clean_signal_at = anchor.get("clean_signal_at")
    current_head_time = latest_commit_time(pr)
    if not clean_signal_at or current_head_time is None:
        return False
    return parse_time(clean_signal_at) >= current_head_time


def review_request_comments(pr: dict[str, Any]) -> list[dict[str, Any]]:
    comments = pr.get("comments", {}).get("nodes", [])
    anchors = [
        comment
        for comment in comments
        if "@codex review" in str(comment.get("body", "")).lower()
    ]
    return sorted(anchors, key=lambda item: parse_time(item["createdAt"]))


def unresolved_codex_threads(pr: dict[str, Any]) -> list[dict[str, Any]]:
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
            first = bot_comments[0]
            threads.append(
                {
                    "thread_id": thread.get("id"),
                    "url": first.get("url"),
                    "path": first.get("path"),
                    "line": first.get("line"),
                    "created_at": first.get("createdAt"),
                }
            )
    return threads


def active_anchor(pr: dict[str, Any]) -> dict[str, Any] | None:
    dedicated = []
    for comment in review_request_comments(pr):
        clean_signal_at = bot_reaction_time(
            comment.get("reactions", {}), "THUMBS_UP"
        )
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
    if active_dedicated:
        return active_dedicated[-1]

    description_state = anchor_state(pr.get("reactionGroups", []))
    if description_state != "no_signal":
        clean_signal_at = bot_reaction_time(pr.get("reactions", {}), "THUMBS_UP")
        return {
            "type": "PR description timeline comment",
            "id": pr["id"],
            "url": pr["url"],
            "created_at": pr["createdAt"],
            "state": description_state,
            "clean_signal_at": clean_signal_at.isoformat()
            if clean_signal_at
            else None,
        }
    return None


def main() -> int:
    pr_view = run_json(["gh", "pr", "view", "--json", "number,url,headRefName"])
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
    threads = unresolved_codex_threads(pr)
    anchor = active_anchor(pr)

    if threads:
        decision = "fix_existing_feedback"
    elif anchor and anchor["state"] == "in_progress":
        decision = "monitor_existing_pass"
    elif anchor and anchor["state"] == "clean_signal" and clean_signal_is_current(
        pr, anchor
    ):
        decision = "clean_signal"
    else:
        decision = "post_codex_review"

    print(
        json.dumps(
            {
                "decision": decision,
                "pr": {
                    "number": number,
                    "url": pr_view["url"],
                    "branch": pr_view["headRefName"],
                    "head_ref_oid": pr.get("headRefOid"),
                },
                "active_anchor": anchor,
                "clean_signal_current": clean_signal_is_current(pr, anchor),
                "unresolved_codex_threads": threads,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr or str(exc))
        raise SystemExit(exc.returncode)
