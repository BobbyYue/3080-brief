#!/usr/bin/env python3
"""Report stable 3080-brief dependencies and emit an approval-safe install plan."""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_ENTRY_DIR = Path(__file__).absolute().parents[1]
SKILL_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = SKILL_DIR / "config" / "dependencies.json"


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def version_tuple(value):
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", value or "")
    if not match:
        return None
    return tuple(int(part or 0) for part in match.groups())


def default_cache_root():
    override = os.environ.get("BRIEF3080_TOOL_CACHE")
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".cache"
    return base / "3080-brief" / "tools"


def default_skill_roots():
    roots = [SKILL_ENTRY_DIR.parent]
    install_root = configured_skill_install_root()
    if install_root:
        roots.append(install_root)
    extra = os.environ.get("BRIEF3080_SKILL_ROOTS")
    if extra:
        roots.extend(Path(value).expanduser() for value in extra.split(os.pathsep) if value)
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    roots.extend((codex_home / "skills", Path.home() / ".agents" / "skills"))
    unique = []
    seen = set()
    for root in roots:
        key = str(root)
        if key not in seen:
            unique.append(root)
            seen.add(key)
    return unique


def configured_skill_install_root():
    override = os.environ.get("BRIEF3080_SKILL_INSTALL_ROOT")
    return Path(override).expanduser() if override else None


def tool_prefix(cache_root, tool_id, spec):
    return cache_root / tool_id / spec["install_version"]


def cached_binary(cache_root, tool_id, spec):
    suffix = ".cmd" if os.name == "nt" else ""
    return tool_prefix(cache_root, tool_id, spec) / "node_modules" / ".bin" / f"{spec['command']}{suffix}"


def run_command(argv, timeout=12):
    try:
        result = subprocess.run(argv, text=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    if result.returncode != 0:
        return None, output or f"exit {result.returncode}"
    return output, None


def package_metadata_from_binary(binary, expected_package):
    try:
        resolved = Path(binary).resolve()
    except OSError:
        return None
    for parent in (resolved.parent, *resolved.parents):
        package_json = parent / "package.json"
        if not package_json.is_file():
            continue
        try:
            metadata = json.loads(package_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if metadata.get("name") == expected_package:
            return metadata
    return None


def tool_candidates(tool_id, spec, cache_root, isolated):
    environment_value = os.environ.get(spec["environment_variable"])
    if environment_value:
        return [("environment", Path(environment_value).expanduser())]
    candidates = [("cache", cached_binary(cache_root, tool_id, spec))]
    if not isolated:
        found = shutil.which(spec["command"])
        if found:
            candidates.insert(0, ("PATH", Path(found)))
    unique = []
    seen = set()
    for source, candidate in candidates:
        key = str(candidate)
        if key not in seen:
            unique.append((source, candidate))
            seen.add(key)
    return unique


def inspect_tool(tool_id, spec, cache_root, isolated, required):
    failures = []
    existing = [(source, path) for source, path in tool_candidates(tool_id, spec, cache_root, isolated) if path.is_file()]
    if not existing:
        return {
            "id": tool_id,
            "status": "BLOCKED" if required else "SKIP",
            "reason": "command not found",
            "path": None,
            "version": None,
        }

    for source, path in existing:
        if tool_id == "lark-cli":
            output, error = run_command([str(path), "--version"])
            version = version_tuple(output or "")
        else:
            metadata = package_metadata_from_binary(path, spec["package"])
            version = version_tuple(metadata.get("version", "")) if metadata else None
            output, error = run_command([str(path), "--help"])
        if error:
            failures.append(f"{path}: smoke test failed: {error}")
            continue
        if version is None:
            failures.append(f"{path}: package version could not be verified")
            continue
        installed = ".".join(str(part) for part in version)
        policy = spec["version_policy"]
        expected_text = spec.get("minimum_version") or spec["install_version"]
        expected = version_tuple(expected_text)
        compatible = version >= expected if policy == "minimum" else version == expected
        if not compatible:
            failures.append(f"{path}: version {installed} violates {policy} policy {expected_text}")
            continue
        return {
            "id": tool_id,
            "status": "PASS",
            "reason": f"compatible {source} installation",
            "path": str(path.resolve()),
            "version": installed,
        }

    return {
        "id": tool_id,
        "status": "BLOCKED" if required else "SKIP",
        "reason": "; ".join(failures),
        "path": None,
        "version": None,
    }


def frontmatter_value(skill_md, key):
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    match = re.search(rf"(?m)^{re.escape(key)}:\s*['\"]?([^'\"\n]+)", parts[1])
    return match.group(1).strip() if match else None


def skill_candidates(skill_id, spec, skill_roots, isolated):
    environment_value = os.environ.get(spec["environment_variable"])
    candidates = []
    if environment_value:
        candidates.append(("environment", Path(environment_value).expanduser()))
    for root in skill_roots:
        candidates.append(("skill-root", Path(root).expanduser() / skill_id))
    if not isolated:
        for root in default_skill_roots():
            candidates.append(("default-root", root / skill_id))
    unique = []
    seen = set()
    for source, candidate in candidates:
        key = str(candidate)
        if key not in seen:
            unique.append((source, candidate))
            seen.add(key)
    return unique


def inspect_skill(skill_id, spec, skill_roots, isolated, required):
    failures = []
    existing = [(source, path) for source, path in skill_candidates(skill_id, spec, skill_roots, isolated) if path.exists()]
    if not existing:
        return {
            "id": skill_id,
            "kind": "skill",
            "status": "BLOCKED" if required else "SKIP",
            "reason": "skill not found",
            "path": None,
            "version": None,
        }
    expected = version_tuple(spec["minimum_version"])
    for source, path in existing:
        missing = [relative for relative in spec["required_paths"] if not (path / relative).exists()]
        if missing:
            failures.append(f"{path}: missing required paths: {', '.join(missing)}")
            continue
        skill_md = path / "SKILL.md"
        declared_name = frontmatter_value(skill_md, "name")
        declared_version = frontmatter_value(skill_md, "version")
        installed = version_tuple(declared_version or "")
        if declared_name != skill_id:
            failures.append(f"{path}: SKILL.md declares name {declared_name!r}, expected {skill_id!r}")
            continue
        if installed is None:
            failures.append(f"{path}: SKILL.md version could not be verified")
            continue
        compatible = installed >= expected if spec["version_policy"] == "minimum" else installed == expected
        if not compatible:
            failures.append(
                f"{path}: version {declared_version} violates {spec['version_policy']} policy {spec['minimum_version']}"
            )
            continue
        return {
            "id": skill_id,
            "kind": "skill",
            "status": "PASS",
            "reason": f"compatible {source} installation",
            "path": str(path.resolve()),
            "version": declared_version,
        }
    return {
        "id": skill_id,
        "kind": "skill",
        "status": "BLOCKED" if required else "SKIP",
        "reason": "; ".join(failures),
        "path": None,
        "version": None,
    }


def inspect_python(config):
    minimum = version_tuple(config["python"]["minimum_version"])
    current = sys.version_info[:3]
    return {
        "id": "python",
        "status": "PASS" if current >= minimum else "FAIL",
        "reason": f"requires >= {config['python']['minimum_version']}",
        "path": sys.executable,
        "version": ".".join(str(part) for part in current),
    }


def inspect_node(config, isolated, required):
    override = os.environ.get("NODE")
    path = override if override else (None if isolated else shutil.which("node"))
    if not path:
        return {
            "id": "node",
            "status": "BLOCKED" if required else "SKIP",
            "reason": "Node.js is required for Feishu adapters and CLI installation",
            "path": None,
            "version": None,
        }
    if not Path(path).is_file():
        return {"id": "node", "status": "FAIL", "reason": f"configured Node.js path does not exist: {path}", "path": None, "version": None}
    output, error = run_command([path, "--version"])
    current = version_tuple(output or "")
    minimum = version_tuple(config["node"]["minimum_version"])
    if error or current is None:
        return {"id": "node", "status": "FAIL", "reason": error or "version unavailable", "path": path, "version": None}
    installed = ".".join(str(part) for part in current)
    return {
        "id": "node",
        "status": "PASS" if current >= minimum else "FAIL",
        "reason": f"requires >= {config['node']['minimum_version']}",
        "path": str(Path(path).resolve()),
        "version": installed,
    }


def install_item(tool_id, spec, cache_root, npm_path):
    prefix = tool_prefix(cache_root, tool_id, spec)
    package = f"{spec['package']}@{spec['install_version']}"
    command = None
    if npm_path:
        command = [
            npm_path,
            "install",
            "--prefix",
            str(prefix),
            "--no-audit",
            "--no-fund",
            "--save-exact",
            package,
        ]
    return {
        "type": "npm_cli",
        "tool": tool_id,
        "package": package,
        "install_root": str(prefix),
        "network_access": True,
        "creates": [str(prefix / "node_modules"), str(prefix / "package.json"), str(prefix / "package-lock.json")],
        "command": command,
        "blocked_by": [] if npm_path else ["node/npm"],
    }


def skill_install_item(skill_id, spec, install_root=None):
    source = spec["source"]
    host_prompt = (
        f"Install {source['url']} as an independent Agent Skill named {skill_id} through the current "
        "agent's native Skill installer or import UI, then reload the agent."
    )
    if install_root is None:
        return {
            "type": "skill",
            "skill": skill_id,
            "minimum_version": spec["minimum_version"],
            "source": source,
            "install_root": None,
            "network_access": True,
            "creates": [],
            "requires_agent_reload": True,
            "requires_host_registration": True,
            "registration_status": "HOST_REGISTRATION_REQUIRED",
            "host_install_prompt": host_prompt,
            "command": None,
            "blocked_by": ["verified host Agent Skill registry root or native Skill installer"],
        }
    destination_root = Path(install_root).expanduser().resolve()
    destination = destination_root / skill_id
    return {
        "type": "skill",
        "skill": skill_id,
        "minimum_version": spec["minimum_version"],
        "source": source,
        "install_root": str(destination),
        "network_access": True,
        "creates": [str(destination)],
        "requires_agent_reload": True,
        "requires_host_registration": False,
        "registration_status": "PENDING_RUNTIME_RECHECK",
        "host_install_prompt": host_prompt,
        "command": [
            sys.executable,
            str(SKILL_DIR / "scripts" / "install_skill_dependency.py"),
            "--skill",
            skill_id,
            "--user-approved",
            "--install-root",
            str(destination_root),
        ],
        "blocked_by": [],
    }


def approval_bundle(config, installations):
    contract = config["installation_bundle"]
    covered = [item.get("tool") or item.get("skill") for item in installations]
    return {
        "id": contract["id"],
        "approval_mode": contract["approval_mode"],
        "approval_scope": contract["approval_scope"],
        "approval_prompt": contract["approval_prompt"],
        "single_approval_covers": covered,
        "on_approve": contract["on_approve"],
        "on_decline": contract["on_decline"],
        "excludes": contract["excludes"],
    }


def build_report(mode, cache_root, isolated, skill_roots, skill_install_root=None):
    config = load_config()
    feishu_required = mode == "feishu"
    checks = [inspect_python(config), inspect_node(config, isolated, feishu_required)]
    for tool_id, spec in config["tools"].items():
        checks.append(inspect_tool(tool_id, spec, cache_root, isolated, feishu_required))
    for skill_id, spec in config.get("skills", {}).items():
        checks.append(inspect_skill(skill_id, spec, skill_roots, isolated, feishu_required))

    if any(check["status"] == "FAIL" for check in checks):
        overall = "FAIL"
        exit_code = 1
    elif feishu_required and any(check["status"] == "BLOCKED" for check in checks):
        overall = "BLOCKED"
        exit_code = 3
    elif any(check["status"] == "SKIP" for check in checks):
        overall = "PARTIAL"
        exit_code = 0
    else:
        overall = "PASS"
        exit_code = 0

    missing_tools = [check["id"] for check in checks if check["id"] in config["tools"] and check["status"] != "PASS"]
    npm_path = None if isolated else shutil.which("npm")
    install_tools = [install_item(tool_id, config["tools"][tool_id], cache_root, npm_path) for tool_id in missing_tools]
    missing_skills = [check["id"] for check in checks if check["id"] in config.get("skills", {}) and check["status"] != "PASS"]
    install_skills = [skill_install_item(skill_id, config["skills"][skill_id], skill_install_root) for skill_id in missing_skills]
    installations = install_tools + install_skills
    installation_required = feishu_required and bool(installations)
    approval_commands = []
    if installation_required and install_tools:
        approval_commands.append([
            sys.executable,
            str(SKILL_DIR / "scripts" / "install_optional_dependencies.py"),
            "--tool",
            "all" if len(install_tools) > 1 else missing_tools[0],
            "--user-approved",
            "--tool-cache",
            str(cache_root),
        ])
    if installation_required:
        approval_commands.extend(item["command"] for item in install_skills if item["command"])
    request = {
        "required": installation_required,
        "requires_user_approval": installation_required,
        "reason": "Feishu output requires the missing CLI and skill dependencies" if feishu_required else "optional Feishu dependencies are unavailable",
        "network_access": bool(installations),
        "host_registration_required": any(item.get("requires_host_registration") for item in install_skills),
        "approval_bundle": approval_bundle(config, installations),
        "installations": installations,
        "approval_commands": approval_commands,
    }
    return {"mode": mode, "overall_status": overall, "checks": checks, "installation_request": request}, exit_code


def print_human(report):
    for check in report["checks"]:
        details = f"path={check['path']} version={check['version']}" if check["path"] else check["reason"]
        print(f"[{check['status']}] {check['id']}: {details}")
    print(f"OVERALL {report['overall_status']}")
    request = report["installation_request"]
    if request["required"]:
        bundle = request["approval_bundle"]
        print("ONE APPROVAL FOR ALL LISTED DEPENDENCIES")
        print(bundle["approval_prompt"])
        print("Covers: " + ", ".join(bundle["single_approval_covers"]))
        print("INSTALLATION APPROVAL REQUIRED")
        for item in request["installations"]:
            label = item.get("tool") or item.get("skill")
            package = item.get("package") or f"{item['source']['repo']}@{item['source']['ref']}"
            destination = item["install_root"] or "current agent's native Skill registry"
            print(f"- {label}: {package} -> {destination}")
            if item["command"]:
                print("  command: " + " ".join(item["command"]))
            elif item.get("host_install_prompt"):
                print("  host action: " + item["host_install_prompt"])
            else:
                print("  blocked by: " + ", ".join(item["blocked_by"]))
        print("Do not install until the user explicitly approves this plan.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("core", "all", "feishu"), default="all")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--resolve", choices=("lark-cli", "whiteboard-cli"))
    parser.add_argument("--tool-cache", type=Path, default=default_cache_root())
    parser.add_argument("--skill-root", type=Path, action="append", default=[], help="Additional root containing installed skill directories.")
    parser.add_argument("--skill-install-root", type=Path, help="Verified host Agent Skill registry root for approved dependency installation.")
    parser.add_argument("--isolated", action="store_true", help="Ignore PATH; use only the configured cache and explicit environment overrides.")
    args = parser.parse_args()
    config = load_config()
    cache_root = args.tool_cache.expanduser().resolve()

    if args.resolve:
        result = inspect_tool(args.resolve, config["tools"][args.resolve], cache_root, args.isolated, True)
        if result["status"] == "PASS":
            print(result["path"])
            return 0
        print(f"[{result['status']}] {args.resolve}: {result['reason']}", file=sys.stderr)
        print("Run check_dependencies.py --mode feishu --json and request user approval before installation.", file=sys.stderr)
        return 3 if result["status"] == "BLOCKED" else 1

    mode = args.mode
    if mode == "core":
        report = {
            "mode": "core",
            "overall_status": "PASS",
            "checks": [inspect_python(config)],
            "installation_request": {
                "required": False,
                "requires_user_approval": False,
                "reason": "Feishu adapters are outside the core offline validation surface",
                "network_access": False,
                "host_registration_required": False,
                "approval_bundle": approval_bundle(config, []),
                "installations": [],
                "approval_commands": [],
            },
        }
        if report["checks"][0]["status"] != "PASS":
            report["overall_status"] = "FAIL"
            exit_code = 1
        else:
            exit_code = 0
    else:
        install_root = args.skill_install_root or configured_skill_install_root()
        report, exit_code = build_report(mode, cache_root, args.isolated, args.skill_root, install_root)
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else "", end="" if args.json else "")
    if not args.json:
        print_human(report)
    elif args.json:
        print()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
