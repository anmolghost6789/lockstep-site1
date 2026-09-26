#!/usr/bin/env python3
"""
jira_attachments.py — Upload/download Jira issue attachments via the Jira Cloud REST API.

The Atlassian remote MCP server does not expose any attachment tool. This script is the
required complement, invoked by the agent via bash from /publish-jira-stories
(Requirements package) and /fetch-jira-context (Build package). The same file is shipped
in both packages — DO NOT fork it; copy on change.

Usage:
    python jira_attachments.py --action upload   --site <SITE> --issue <ISSUE_KEY> --files <path>...
    python jira_attachments.py --action download --site <SITE> --issue <ISSUE_KEY> --dest  <dir>

Credential resolution (per field, independent precedence):
    1. CLI arg            --site / --email / --token
    2. Environment var    JIRA_SITE / JIRA_EMAIL / JIRA_API_TOKEN
    3. .jira_config.json  in the current working directory:
                          { "site": "...", "email": "...", "api_token": "..." }

--site accepts either the short subdomain (constructs <SUB>.atlassian.net) or a full host.

Exit codes:
    0  success (uploads: at least one file uploaded; downloads: completed, even if 0 attachments)
    1  failure (missing credentials, issue not found, all uploads failed, network error)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import requests
except ImportError:
    print("ERROR: 'requests' is not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)


REQUEST_TIMEOUT_SECONDS = 30
CONFIG_FILENAME = ".jira_config.json"


def _load_config_file() -> Dict[str, str]:
    """Read .jira_config.json from CWD. Returns {} on any failure (warned to stderr)."""
    config_path = Path.cwd() / CONFIG_FILENAME
    if not config_path.exists():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"WARNING: Could not read {config_path}: {exc}", file=sys.stderr)
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: str(v).strip() for k, v in data.items() if isinstance(v, (str, int))}


def _resolve(cli_value: Optional[str], env_var: str, config_key: str, config: Dict[str, str]) -> str:
    """CLI arg > env var > .jira_config.json. Returns '' if none resolves."""
    if cli_value:
        return cli_value.strip()
    env_value = os.environ.get(env_var, "").strip()
    if env_value:
        return env_value
    return config.get(config_key, "").strip()


def _load_credentials(
    cli_site: Optional[str], cli_email: Optional[str], cli_token: Optional[str]
) -> Tuple[str, Tuple[str, str]]:
    """Return (base_url, (email, api_token)). Exits 1 with a clear message if anything is missing."""
    config = _load_config_file()
    site = _resolve(cli_site, "JIRA_SITE", "site", config)
    email = _resolve(cli_email, "JIRA_EMAIL", "email", config)
    token = _resolve(cli_token, "JIRA_API_TOKEN", "api_token", config)

    missing = [name for name, value in (("site", site), ("email", email), ("api_token", token)) if not value]
    if missing:
        print("ERROR: Missing Jira credentials: " + ", ".join(missing), file=sys.stderr)
        print(
            "       Provide via CLI args (--site/--email/--token), env vars\n"
            "       (JIRA_SITE/JIRA_EMAIL/JIRA_API_TOKEN), or .jira_config.json in CWD.",
            file=sys.stderr,
        )
        sys.exit(1)

    host = site if "." in site else f"{site}.atlassian.net"
    return f"https://{host}", (email, token)


def upload(
    issue: str,
    file_paths: List[str],
    cli_site: Optional[str],
    cli_email: Optional[str],
    cli_token: Optional[str],
) -> int:
    """Upload each file to the given issue. Returns the number of successful uploads."""
    base_url, auth = _load_credentials(cli_site, cli_email, cli_token)
    endpoint = f"{base_url}/rest/api/3/issue/{issue}/attachments"
    # X-Atlassian-Token: no-check is mandatory — without it Jira rejects the request as
    # a CSRF check failure even when Basic auth is valid.
    headers = {"X-Atlassian-Token": "no-check", "Accept": "application/json"}

    successes = 0
    for raw_path in file_paths:
        path = Path(raw_path)
        if not path.exists():
            print(f"WARNING: Skipping missing file: {path}", file=sys.stderr)
            continue
        if not path.is_file():
            print(f"WARNING: Skipping non-file path: {path}", file=sys.stderr)
            continue

        try:
            with path.open("rb") as fh:
                files = {"file": (path.name, fh, "application/octet-stream")}
                response = requests.post(
                    endpoint, auth=auth, headers=headers, files=files, timeout=REQUEST_TIMEOUT_SECONDS
                )
        except requests.RequestException as exc:
            print(f"ERROR: Upload failed for {path.name}: {exc}", file=sys.stderr)
            continue

        if response.status_code == 404:
            print(f"ERROR: Issue not found: {issue} (HTTP 404)", file=sys.stderr)
            return successes
        if not response.ok:
            print(
                f"ERROR: Upload failed for {path.name}: HTTP {response.status_code} {response.text[:500]}",
                file=sys.stderr,
            )
            continue

        try:
            body = response.json()
        except ValueError:
            print(f"ERROR: Upload returned non-JSON for {path.name}: {response.text[:200]}", file=sys.stderr)
            continue

        attachments = body if isinstance(body, list) else [body]
        for att in attachments:
            print(json.dumps({
                "filename": att.get("filename", path.name),
                "id": att.get("id"),
                "self": att.get("self"),
                "size": att.get("size"),
            }))
        successes += 1

    return successes


def download(
    issue: str,
    dest_dir: str,
    cli_site: Optional[str],
    cli_email: Optional[str],
    cli_token: Optional[str],
) -> int:
    """Download every attachment on the issue into dest_dir. Returns the number of files written."""
    base_url, auth = _load_credentials(cli_site, cli_email, cli_token)
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    issue_url = f"{base_url}/rest/api/3/issue/{issue}"
    try:
        response = requests.get(
            issue_url,
            auth=auth,
            headers={"Accept": "application/json"},
            params={"fields": "attachment"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        print(f"ERROR: Failed to fetch issue {issue}: {exc}", file=sys.stderr)
        return 0

    if response.status_code == 404:
        print(f"ERROR: Issue not found: {issue} (HTTP 404)", file=sys.stderr)
        return 0
    if not response.ok:
        print(
            f"ERROR: Failed to fetch issue {issue}: HTTP {response.status_code} {response.text[:500]}",
            file=sys.stderr,
        )
        return 0

    try:
        attachments = response.json().get("fields", {}).get("attachment") or []
    except ValueError:
        print(f"ERROR: Issue response was not JSON: {response.text[:200]}", file=sys.stderr)
        return 0

    if not attachments:
        print(f"No attachments found on {issue}.")
        return 0

    written = 0
    for att in attachments:
        filename = att.get("filename") or f"attachment-{att.get('id', 'unknown')}"
        content_url = att.get("content")
        if not content_url:
            print(f"WARNING: Attachment {filename} has no content URL; skipping.", file=sys.stderr)
            continue

        try:
            with requests.get(
                content_url,
                auth=auth,
                stream=True,
                allow_redirects=True,
                timeout=REQUEST_TIMEOUT_SECONDS,
            ) as dl:
                if not dl.ok:
                    print(f"ERROR: Download failed for {filename}: HTTP {dl.status_code}", file=sys.stderr)
                    continue
                target = dest / filename
                with target.open("wb") as out:
                    for chunk in dl.iter_content(chunk_size=64 * 1024):
                        if chunk:
                            out.write(chunk)
        except requests.RequestException as exc:
            print(f"ERROR: Download failed for {filename}: {exc}", file=sys.stderr)
            continue

        print(str(target))
        written += 1

    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Upload or download Jira issue attachments via the Jira Cloud REST API. "
            "Credentials resolved per field by CLI arg > env var > .jira_config.json in CWD."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples (all values are runtime-discovered placeholders):\n"
            "  python jira_attachments.py --action upload   --site <SITE> --issue <ISSUE_KEY> --files <file>...\n"
            "  python jira_attachments.py --action download --site <SITE> --issue <ISSUE_KEY> --dest  <dir>\n"
        ),
    )
    parser.add_argument("--action", required=True, choices=["upload", "download"], help="Operation to perform.")
    parser.add_argument("--issue", required=True, help="Jira issue key or numeric ID.")
    parser.add_argument("--site",  default=None, help="Atlassian site short name or full host. Overrides JIRA_SITE / .jira_config.json.")
    parser.add_argument("--email", default=None, help="Atlassian account email. Overrides JIRA_EMAIL / .jira_config.json.")
    parser.add_argument("--token", default=None, help="Atlassian API token. Overrides JIRA_API_TOKEN / .jira_config.json.")
    parser.add_argument("--files", nargs="+", help="One or more file paths to upload (required when --action upload).")
    parser.add_argument("--dest",  help="Destination directory for downloads (required when --action download).")
    args = parser.parse_args()

    if args.action == "upload":
        if not args.files:
            parser.error("--files is required when --action upload")
        successes = upload(args.issue, args.files, args.site, args.email, args.token)
        sys.exit(0 if successes > 0 else 1)

    if not args.dest:
        parser.error("--dest is required when --action download")
    download(args.issue, args.dest, args.site, args.email, args.token)
    sys.exit(0)


if __name__ == "__main__":
    main()
