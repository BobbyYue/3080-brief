#!/usr/bin/env python3
"""Install an approved 3080-brief skill dependency from its verified GitHub source."""

import argparse
import json
import os
import shutil
import stat
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

import check_dependencies as dependencies


MAX_ARCHIVE_BYTES = 100 * 1024 * 1024


def archive_url(source):
    configured = source.get("archive_url")
    if configured:
        return configured
    return f"https://github.com/{source['repo']}/archive/refs/heads/{source['ref']}.zip"


def default_install_root():
    configured = dependencies.configured_skill_install_root()
    return configured.resolve() if configured else None


def build_plan(skill_id, spec, install_root, local_archive=None):
    source = spec["source"]
    destination = install_root / skill_id if install_root else None
    command = None
    if install_root:
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--skill",
            skill_id,
            "--user-approved",
            "--install-root",
            str(install_root),
        ]
        if local_archive:
            command.extend(("--archive", str(local_archive)))
    return {
        "type": "skill",
        "skill": skill_id,
        "minimum_version": spec["minimum_version"],
        "source": source,
        "download_url": str(local_archive) if local_archive else archive_url(source),
        "installation_method": "verified GitHub archive",
        "install_root": str(destination) if destination else None,
        "network_access": local_archive is None,
        "creates": [str(destination)] if destination else [],
        "requires_agent_reload": True,
        "requires_host_registration": install_root is None,
        "registration_status": "PENDING_RUNTIME_RECHECK" if install_root else "HOST_REGISTRATION_REQUIRED",
        "host_install_prompt": (
            f"Install {source['url']} as an independent Agent Skill named {skill_id} through the current "
            "agent's native Skill installer or import UI, then reload the agent."
        ),
        "command": command,
        "blocked_by": [] if install_root else ["verified host Agent Skill registry root or native Skill installer"],
    }


def download(url, destination):
    request = urllib.request.Request(url, headers={"User-Agent": "3080-brief-dependency-installer"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
        declared = response.headers.get("Content-Length")
        if declared and int(declared) > MAX_ARCHIVE_BYTES:
            raise RuntimeError(f"archive exceeds {MAX_ARCHIVE_BYTES} bytes")
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_ARCHIVE_BYTES:
                raise RuntimeError(f"archive exceeds {MAX_ARCHIVE_BYTES} bytes")
            output.write(chunk)


def extract_verified_archive(archive, destination):
    with zipfile.ZipFile(archive) as bundle:
        top_levels = set()
        for info in bundle.infolist():
            path = PurePosixPath(info.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in info.filename or not path.parts:
                raise RuntimeError(f"unsafe archive member: {info.filename}")
            mode = info.external_attr >> 16
            if stat.S_IFMT(mode) == stat.S_IFLNK:
                raise RuntimeError(f"symbolic links are not allowed in the skill archive: {info.filename}")
            top_levels.add(path.parts[0])
        if len(top_levels) != 1:
            raise RuntimeError("GitHub archive must contain exactly one repository root")
        bundle.extractall(destination)
    return destination / next(iter(top_levels))


def source_directory(repository_root, source):
    relative = PurePosixPath(source.get("path", "."))
    if relative.is_absolute() or ".." in relative.parts:
        raise RuntimeError(f"unsafe skill source path: {relative}")
    selected = repository_root if str(relative) == "." else repository_root.joinpath(*relative.parts)
    if not selected.is_dir():
        raise RuntimeError(f"skill source path was not found in the archive: {relative}")
    return selected


def install(skill_id, spec, install_root, local_archive=None):
    destination = install_root / skill_id
    if destination.exists():
        raise FileExistsError(f"destination already exists and will not be overwritten: {destination}")
    install_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{skill_id}-", dir=install_root) as temporary:
        temporary_path = Path(temporary)
        archive = temporary_path / "source.zip"
        if local_archive:
            shutil.copyfile(local_archive, archive)
        else:
            download(archive_url(spec["source"]), archive)
        repository_root = extract_verified_archive(archive, temporary_path / "unpacked")
        selected = source_directory(repository_root, spec["source"])
        payload = temporary_path / "payload" / skill_id
        shutil.copytree(selected, payload)
        staged = dependencies.inspect_skill(skill_id, spec, [payload.parent], True, True)
        if staged["status"] != "PASS":
            raise RuntimeError(f"downloaded skill failed contract verification: {staged['reason']}")
        payload.rename(destination)
    installed = dependencies.inspect_skill(skill_id, spec, [install_root], True, True)
    if installed["status"] != "PASS":
        raise RuntimeError(f"installed skill failed contract verification: {installed['reason']}")
    return installed


def main():
    config = dependencies.load_config()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", choices=tuple(config.get("skills", {})), required=True)
    parser.add_argument("--install-root", type=Path, default=default_install_root())
    parser.add_argument("--archive", type=Path, help="Use a local GitHub-format ZIP archive for offline verification.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--user-approved", action="store_true", help="Assert that the user approved the displayed network/install plan.")
    args = parser.parse_args()
    spec = config["skills"][args.skill]
    install_root = args.install_root.expanduser().resolve() if args.install_root else None
    local_archive = args.archive.expanduser().resolve() if args.archive else None
    plan = build_plan(args.skill, spec, install_root, local_archive)
    print(json.dumps({"status": "DRY_RUN" if args.dry_run else "APPROVAL_CHECK", "installation": plan}, ensure_ascii=False, indent=2))
    if args.dry_run:
        return 0
    if install_root is None:
        print(
            "BLOCKED: no verified host Agent Skill registry root was provided. Use the host's native Skill "
            "installer/import UI, or pass --install-root / set BRIEF3080_SKILL_INSTALL_ROOT explicitly.",
            file=sys.stderr,
        )
        return 3
    if not args.user_approved:
        print("BLOCKED: explicit user approval is required before network or file installation.", file=sys.stderr)
        return 3
    try:
        installed = install(args.skill, spec, install_root, local_archive)
    except (FileExistsError, OSError, RuntimeError, urllib.error.URLError, zipfile.BadZipFile) as exc:
        print(f"FAIL: skill installation failed for {args.skill}: {exc}", file=sys.stderr)
        return 1
    print(f"FILES INSTALLED AND VERIFIED: {args.skill} {installed['version']} at {installed['path']}")
    print("REGISTRATION PENDING: reload or restart the current agent, then rerun the dependency check from its normal runtime.")
    print("Do not treat this dependency as PASS until that runtime check succeeds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
