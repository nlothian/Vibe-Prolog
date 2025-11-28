from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from . import (
    check_commands_available,
    ensure_env,
    has_staged_changes,
    run,
    stage_changes,
)
def _checkout_and_get_current_branch(issue_number: str, config: IssueWorkflowConfig) -> str:
    """Helper: refresh, then checkout/create branch as needed and return current branch name."""
    # Refresh
    run(["git", "pull"], capture_output=False)
    # Get current branch
    current_branch = run(["git", "branch", "--show-current"]).strip()

    # Check if current branch is for this issue
    issue_token = config.branch_prefix_token(issue_number)
    is_issue_branch = issue_token in current_branch

    # Create new branch if:
    # 1. Explicitly requested via --newbranch
    # 2. Not currently on a branch for this issue (e.g., on main)
    if config.use_new_branch or not is_issue_branch:
        run(["gh", "issue", "develop", issue_number, "--checkout"], capture_output=False)
        return run(["git", "branch", "--show-current"]).strip()

    # Already on an issue branch for this issue, use it
    return current_branch



@dataclass(frozen=True)
class IssueWorkflowConfig:
    """Configuration for running the fix-issue workflow with a specific tool."""

    tool_cmd: Sequence[str]
    branch_prefix: str
    default_commit_message: str
    branch_suffix: str = "-"
    required_commands: Sequence[str] | None = None
    pr_model: str = "gpt-5-nano"
    timeout_seconds: int | None = None
    session_dir: Path | None = None
    use_json_output: bool = False
    input_instruction: str | None = None
    use_new_branch: bool = False
    existing_branch: str | None = None

    def required_cmds(self) -> list[str]:
        """Commands that must be present before executing the workflow."""
        base = ["gh", "llm"]
        extra = list(self.required_commands) if self.required_commands is not None else []
        if not extra and self.tool_cmd:
            extra.append(self.tool_cmd[0])
        commands: list[str] = []
        for cmd in [*extra, *base]:
            if cmd and cmd not in commands:
                commands.append(cmd)
        return commands

    def branch_requirement(self, issue_number: str) -> str:
        """Full prefix text enforced for generated branch names."""
        return f"{self.branch_prefix}/{issue_number}{self.branch_suffix}"

    def branch_prefix_token(self, issue_number: str) -> str:
        """Substring that must appear in the branch name."""
        return f"{self.branch_prefix}/{issue_number}"


def get_issue_content(issue_number: str) -> str:
    template = (
        "# Issue: \n"
        "{{.title}}\n\n"
        "# Description\n"
        "{{.body}}\n\n"
        "# Comments\n\n"
        "{{range .comments}}## Comment\n"
        "{{.body}}\n\n"
        "{{end}}"
    )
    return run(
        [
            "gh",
            "issue",
            "view",
            issue_number,
            "--json",
            "title,body,comments",
            "--template",
            template,
        ]
    )


def create_branch_name(issue_number: str, issue_content: str, config: IssueWorkflowConfig) -> str:
    prompt = (
        "create a good git branch title for a branch that addresses this issue. "
        f"It should start with `{config.branch_requirement(issue_number)}` and must be a valid branch name"
    )
    raw_output = run(["llm", prompt], input_text=issue_content).strip()
    lines = [line.strip() for line in raw_output.splitlines() if line.strip()]

    temp_branch_name = ""
    required_token = config.branch_prefix_token(issue_number)
    for line in lines:
        if required_token in line:
            temp_branch_name = line
            break
    if not temp_branch_name and lines:
        temp_branch_name = lines[0]
    if not temp_branch_name:
        raise SystemExit(f"llm did not return a usable branch name: {raw_output!r}")

    normalized = run(["git", "check-ref-format", "--normalize", temp_branch_name]).strip()
    return normalized


def get_or_create_branch(issue_number: str, config: IssueWorkflowConfig) -> str:
    """Get existing branch or create a new one for the given issue, returning the
    name of the branch that is checked out.
    
    Logic refactored to use a helper to remove duplication across code paths.
    """
    return _checkout_and_get_current_branch(issue_number, config)


def run_tool(issue_content: str, config: IssueWorkflowConfig) -> None:
    """Run the configured tool with optional timeout and session management."""
    cmd = list(config.tool_cmd)

    # Add JSON output flag if configured
    if config.use_json_output and "--output" not in cmd:
        cmd.extend(["--output", "json"])

    # If no timeout, run normally
    if config.timeout_seconds is None:
        run(cmd, input_text=issue_content, capture_output=False)
        return

    # Run with timeout
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Send input and wait with timeout
        try:
            stdout, stderr = process.communicate(input=issue_content, timeout=config.timeout_seconds)

            # If using JSON output, try to parse and display
            if stdout:
                if config.use_json_output:
                    try:
                        result = json.loads(stdout)
                        # Extract session ID if present
                        if isinstance(result, dict) and "session_id" in result:
                            session_id = result["session_id"]
                            if config.session_dir:
                                save_session_id(session_id, config.session_dir)
                                print(f"Session ID saved: {session_id}")
                        print(json.dumps(result, indent=2))
                    except json.JSONDecodeError:
                        print(stdout)
                else:
                    print(stdout)

            if stderr:
                print(stderr, file=sys.stderr)

            if process.returncode != 0:
                raise SystemExit(f"Tool failed with exit code {process.returncode}")

        except subprocess.TimeoutExpired:
            # Kill the process
            process.kill()
            stdout_data, stderr_data = process.communicate()

            session_id = extract_session_id_from_output(stdout_data, stderr_data)

            if session_id:
                if config.session_dir:
                    save_session_id(session_id, config.session_dir)
                print(f"\n⏱️  Timeout after {config.timeout_seconds}s. Session ID: {session_id}", file=sys.stderr)
            else:
                print(f"\n⏱️  Timeout after {config.timeout_seconds}s. No session ID found.", file=sys.stderr)

            raise SystemExit(124)  # Standard timeout exit code

    except FileNotFoundError:
        raise SystemExit(f"Command not found: {cmd[0]}")


def save_session_id(session_id: str, session_dir: Path) -> None:
    """Save a session ID to the session directory."""
    session_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    session_file = session_dir / f"session_{timestamp}_{session_id}.txt"
    session_file.write_text(f"{session_id}\n")


def extract_session_id_from_output(stdout: str, stderr: str) -> str | None:
    """Try to extract session ID from command output."""
    combined = stdout + "\n" + stderr

    # Try to parse as JSON first
    for stream_content in (stdout, stderr):
        if not stream_content:
            continue
        try:
            data = json.loads(stream_content)
            if isinstance(data, dict) and "session_id" in data:
                return str(data["session_id"])
        except (json.JSONDecodeError, ValueError):
            pass

    # Look for common session ID patterns
    # Match patterns like "session-xxxxx" or "Session ID: xxxxx"
    patterns = [
        r'session[_-]id[:\s]+([a-zA-Z0-9_-]+)',
        r'session[:\s]+([a-zA-Z0-9_-]+)',
        r'"session_id"[:\s]+"([^"]+)"',
    ]

    for pattern in patterns:
        match = re.search(pattern, combined, re.IGNORECASE)
        if match:
            return match.group(1)

    return None


def create_commit_if_needed(default_message: str) -> None:
    if not has_staged_changes():
        print("No changes to commit.")
        return

    diff = run(["git", "diff", "--cached"])
    commit_message = run(
        ["llm", "-s", "give me a git commit message for these changes"],
        input_text=diff,
    ).strip()
    if not commit_message:
        commit_message = default_message
    run(["git", "commit", "-m", commit_message], capture_output=False)


def push_branch(branch_name: str) -> None:
    run(["git", "push", "--set-upstream", "origin", branch_name], capture_output=False)


def build_pr_title_body(issue_number: str, model: str) -> dict[str, Any]:
    git_log_output = run(["git", "log", "origin/main.."])
    prompt = (
        "Looking at this git log output, summarise into a `title` and `body` suitable for a pull request. "
        f"The `body` MUST start with `Closes #{issue_number}`"
    )
    pr_title_body_json = run(
        [
            "llm",
            "--schema",
            "title,body",
            "-m",
            model,
            prompt,
        ],
        input_text=git_log_output,
    )
    try:
        data = json.loads(pr_title_body_json)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse JSON from llm output: {exc}\nRaw output:\n{pr_title_body_json}")
    if not isinstance(data, dict):
        raise SystemExit(f"Unexpected JSON type from llm: {type(data)}")
    return data


def create_pr(issue_number: str, model: str) -> None:
    pr_data = build_pr_title_body(issue_number, model)
    title = str(pr_data.get("title", "")).strip()
    body = str(pr_data.get("body", "")).strip()
    run(
        [
            "gh",
            "pr",
            "create",
            "--title",
            title,
            "--body",
            body,
        ],
        capture_output=False,
    )


def run_issue_workflow(issue_number: str, config: IssueWorkflowConfig) -> None:
    check_commands_available(config.required_cmds())
    ensure_env()

    issue_content = get_issue_content(issue_number)
    tool_input = issue_content
    if config.input_instruction:
        tool_input = f"{config.input_instruction}\n\n{issue_content}"

    branch_name = get_or_create_branch(issue_number, config)

    run_tool(tool_input, config)
    stage_changes()
    create_commit_if_needed(config.default_commit_message)
    push_branch(branch_name)
    create_pr(issue_number, config.pr_model)
