#!/usr/bin/env python3
"""Deploy GitHub Pages from the current workflow artifact, with extended polling.

Avoids the 600-second client-side timeout hardcoded by actions/deploy-pages.
Does NOT bypass GitHub Pages backend timeouts, quotas or environment rules.
Requires an Actions job with pages:write, id-token:write and actions:read.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ARTIFACT_NAME = "github-pages"
FAILURE_STATUSES = {
    "deployment_failed",
    "deployment_content_failed",
    "deployment_cancelled",
    "deployment_lost",
    "failed",
    "failure",
    "error",
    "cancelled",
    "canceled",
}


class DeploymentError(RuntimeError):
    pass


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise DeploymentError(f"Missing GitHub Actions environment variable: {name}")
    return value


def request_json(method: str, url: str, *, token: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "neural-smith-pages-publisher",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    try:
        with urlopen(Request(url, data=data, headers=headers, method=method), timeout=45) as response:
            content = response.read()
            return json.loads(content) if content else {}
    except HTTPError as exc:
        # Do not print POST payloads or bearer tokens to action logs.
        raise DeploymentError(f"GitHub API {method} failed with HTTP {exc.code}: {url}") from exc
    except (URLError, TimeoutError) as exc:
        raise DeploymentError(f"GitHub API {method} connection failed: {url} ({exc})") from exc


def oidc_token() -> str:
    url = required_env("ACTIONS_ID_TOKEN_REQUEST_URL")
    token = required_env("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    # Matching actions/deploy-pages: request GitHub's default OIDC audience.
    try:
        with urlopen(Request(url, headers={"Authorization": f"Bearer {token}"}), timeout=30) as response:
            value = json.loads(response.read()).get("value")
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise DeploymentError("Could not retrieve GitHub Actions OIDC token") from exc
    if not isinstance(value, str) or not value:
        raise DeploymentError("GitHub's OIDC response contained no token")
    return value


def artifact_id(api: str, run_id: str, token: str) -> int:
    response = request_json(
        "GET", f"{api}/actions/runs/{run_id}/artifacts?per_page=100", token=token
    )
    artifacts = [
        a for a in response.get("artifacts", [])
        if a.get("name") == ARTIFACT_NAME and not a.get("expired", False)
    ]
    if len(artifacts) != 1:
        raise DeploymentError(
            f"Expected exactly one non-expired '{ARTIFACT_NAME}' artifact in workflow run "
            f"{run_id}, found {len(artifacts)}"
        )
    result = artifacts[0].get("id")
    if not isinstance(result, int):
        raise DeploymentError("Pages artifact has no numeric ID")
    print(f"Found Pages artifact {result} (size {artifacts[0].get('size_in_bytes', '?')} bytes)", flush=True)
    return result


def monitor(api: str, deploy_id: str, token: str, *, timeout_seconds: int, poll_seconds: int) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_status = None
    errors = 0
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        time.sleep(min(poll_seconds, max(0, remaining)))
        try:
            deployment = request_json("GET", f"{api}/pages/deployments/{deploy_id}", token=token)
            errors = 0
        except DeploymentError as exc:
            errors += 1
            print(f"Status check {errors}/8 failed: {exc}", flush=True)
            if errors >= 8:
                raise DeploymentError("Too many Pages deployment status API failures") from exc
            continue
        status = deployment.get("status", "unknown_status")
        if status != last_status:
            print(f"Pages deployment status: {status}", flush=True)
            last_status = status
        if status == "succeed":
            print("GitHub Pages deployment succeeded.", flush=True)
            return
        if status in FAILURE_STATUSES:
            raise DeploymentError(f"GitHub Pages backend reported terminal status: {status}")
    # The custom poller does not cancel a potentially active deploy; canceling
    # can leave a deployment lock stuck. Surface the ID for manual inspection.
    raise DeploymentError(
        f"The deployment has not completed after {timeout_seconds} seconds. "
        f"Deployment ID: {deploy_id}. Check GitHub Pages deployment status "
        "and GitHub Status; a backend timeout cannot be overridden here."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument("--poll-seconds", type=int, default=20)
    args = parser.parse_args()
    if not (60 <= args.timeout_seconds <= 21600):
        parser.error("--timeout-seconds must be between 60 and 21600")
    if not (5 <= args.poll_seconds <= 300):
        parser.error("--poll-seconds must be between 5 and 300")

    repository = required_env("GITHUB_REPOSITORY")
    run_id = required_env("GITHUB_RUN_ID")
    sha = required_env("GITHUB_SHA")
    token = required_env("GITHUB_TOKEN")
    api = f"{os.environ.get('GITHUB_API_URL', 'https://api.github.com').rstrip('/')}/repos/{repository}"

    # Only pull the private OIDC token after validating artifact availability.
    a_id = artifact_id(api, run_id, token)
    signing_token = oidc_token()
    deployment = request_json(
        "POST", f"{api}/pages/deployments", token=token,
        payload={"artifact_id": a_id, "pages_build_version": sha, "oidc_token": signing_token},
    )
    deploy_id = str(deployment.get("id") or deployment.get("status_url", "").rsplit("/", 1)[-1] or sha)
    print(f"Pages deployment created. ID: {deploy_id}", flush=True)
    monitor(api, deploy_id, token, timeout_seconds=args.timeout_seconds, poll_seconds=args.poll_seconds)
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with Path(output_file).open("a", encoding="utf-8") as output:
            output.write("page_url=https://neural-smith.github.io/\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except DeploymentError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
