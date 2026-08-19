#!/usr/bin/env python3
"""Install an approved 3080-brief skill dependency with the official Codex installer."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import check_dependencies as dependencies


def installer_candidates():
    override = os.environ.get("CODEX_SKILL_INSTALLER")
    if override:
        yield Path(override).expanduser()
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    yield codex_home / "skills" / ".system" / "skill-installer" / "scripts" / "install-skill-from-github.py"
    yield dependencies.SKILL_DIR.parent / ".system" / "skill-installer" / "scripts" / "install-skill-from-github.py"


def find_installer():
    for candidate in installer_candidates():
        if candidate.is_file():
            return candidate.resolve()
    return None


def build_plan(skill_id, spec):
    source = spec["source"]
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    destination_root = codex_home / "skills"
    installer = find_installer()
    command = None
    if installer:
        command = [
            sys.executable,
            str(installer),
            "--repo",
            source["repo"],
            "--path",
            source["path"],
            "--ref",
            source["ref"],
            "--dest",
            str(destination_root),
            "--name",
            skill_id,
        ]
    return {
        "type": "skill",
        "skill": skill_id,
        "minimum_version": spec["minimum_version"],
        "source": source,
        "install_root": str(destination_root / skill_id),
        "network_access": True,
        "creates": [str(destination_root / skill_id)],
        "requires_codex_restart": True,
        "command": command,
        "blocked_by": [] if installer else ["official Codex skill-installer not found"],
    }


def main():
    config = dependencies.load_config()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", choices=tuple(config.get("skills", {})), required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--user-approved", action="store_true", help="Assert that the user approved the displayed network/install plan.")
    args = parser.parse_args()
    spec = config["skills"][args.skill]
    plan = build_plan(args.skill, spec)
    print(json.dumps({"status": "DRY_RUN" if args.dry_run else "APPROVAL_CHECK", "installation": plan}, ensure_ascii=False, indent=2))
    if args.dry_run:
        return 0
    if not args.user_approved:
        print("BLOCKED: explicit user approval is required before network installation.", file=sys.stderr)
        return 3
    if not plan["command"]:
        print("BLOCKED: official Codex skill-installer is unavailable.", file=sys.stderr)
        return 3
    if Path(plan["install_root"]).exists():
        print(f"BLOCKED: destination already exists and will not be overwritten: {plan['install_root']}", file=sys.stderr)
        return 3
    result = subprocess.run(plan["command"], text=True)
    if result.returncode != 0:
        print(f"FAIL: skill installation failed for {args.skill}", file=sys.stderr)
        return 1
    verify = dependencies.inspect_skill(args.skill, spec, [Path(plan["install_root"]).parent], True, True)
    if verify["status"] != "PASS":
        print(f"FAIL: installed skill did not pass contract verification: {verify['reason']}", file=sys.stderr)
        return 1
    print(f"PASS installed and verified {args.skill} {verify['version']} at {verify['path']}")
    print("RESTART REQUIRED: restart Codex so the new skill is registered before continuing the Feishu task.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
