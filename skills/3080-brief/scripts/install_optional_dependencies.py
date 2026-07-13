#!/usr/bin/env python3
"""Install approved Feishu adapters into an isolated user tool cache."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import check_dependencies as dependencies


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", choices=("lark-cli", "whiteboard-cli", "all"), required=True)
    parser.add_argument("--tool-cache", type=Path, default=dependencies.default_cache_root())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--user-approved", action="store_true", help="Assert that the user approved the displayed network/install plan.")
    args = parser.parse_args()

    config = dependencies.load_config()
    selected = list(config["tools"]) if args.tool == "all" else [args.tool]
    npm_path = shutil.which("npm")
    plans = [dependencies.install_item(tool_id, config["tools"][tool_id], args.tool_cache.expanduser().resolve(), npm_path) for tool_id in selected]
    print(json.dumps({"status": "DRY_RUN" if args.dry_run else "APPROVAL_CHECK", "installations": plans}, ensure_ascii=False, indent=2))
    if args.dry_run:
        return 0
    if not args.user_approved:
        print("BLOCKED: explicit user approval is required before network installation.", file=sys.stderr)
        return 3
    if not npm_path:
        print("BLOCKED: Node.js/npm is missing. Request approval for a platform-appropriate Node.js >=18 installation first.", file=sys.stderr)
        return 3

    for plan in plans:
        prefix = Path(plan["install_root"])
        prefix.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(plan["command"], text=True)
        if result.returncode != 0:
            print(f"FAIL: npm installation failed for {plan['tool']}", file=sys.stderr)
            return 1
        verify = subprocess.run(
            [
                sys.executable,
                str(dependencies.SKILL_DIR / "scripts" / "check_dependencies.py"),
                "--resolve",
                plan["tool"],
                "--tool-cache",
                str(args.tool_cache.expanduser().resolve()),
                "--isolated",
            ],
            text=True,
        )
        if verify.returncode != 0:
            print(f"FAIL: installed {plan['tool']} did not pass the pinned-version smoke test", file=sys.stderr)
            return 1
        print(f"PASS installed and verified {plan['tool']} at {prefix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
