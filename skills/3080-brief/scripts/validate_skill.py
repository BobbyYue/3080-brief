#!/usr/bin/env python3
"""Validate the installable skill without third-party Python packages."""

import argparse
import json
import re
import sys
from pathlib import Path


MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_SKILL_LINES = 500
ALLOWED_KEYS = {"name", "description"}
FORBIDDEN_ROOT_DOCS = {
    "README.md",
    "INSTALLATION_GUIDE.md",
    "QUICK_REFERENCE.md",
    "CHANGELOG.md",
}


def parse_scalar(value):
    value = value.strip()
    if not value:
        return ""
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid quoted scalar: {exc}") from exc
        if not isinstance(parsed, str):
            raise ValueError("frontmatter scalar must be a string")
        return parsed
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise ValueError("unterminated single-quoted scalar")
        return value[1:-1].replace("''", "'")
    return value


def parse_frontmatter(text):
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md must start with a closed YAML frontmatter block")
    values = {}
    for line_number, line in enumerate(match.group(1).splitlines(), 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1].isspace() or "\t" in line:
            raise ValueError(f"line {line_number}: local validator supports flat string frontmatter only")
        field = re.fullmatch(r"([A-Za-z0-9_-]+):\s*(.*)", line)
        if not field:
            raise ValueError(f"line {line_number}: invalid frontmatter entry")
        key, raw_value = field.groups()
        if key in values:
            raise ValueError(f"line {line_number}: duplicate frontmatter key {key}")
        values[key] = parse_scalar(raw_value)
    return values


def validate_links(skill_dir, text):
    errors = []
    for raw_target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = raw_target.strip().strip("<>").split("#", 1)[0]
        if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
            continue
        resolved = (skill_dir / target).resolve()
        try:
            resolved.relative_to(skill_dir.resolve())
        except ValueError:
            errors.append(f"SKILL.md link escapes skill directory: {raw_target}")
            continue
        if not resolved.exists():
            errors.append(f"SKILL.md link target is missing: {target}")
    return errors


def validate(skill_dir):
    errors = []
    skill_dir = Path(skill_dir).resolve()
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return ["SKILL.md not found"]
    text = skill_md.read_text(encoding="utf-8")
    try:
        frontmatter = parse_frontmatter(text)
    except ValueError as exc:
        return [str(exc)]

    unexpected = set(frontmatter) - ALLOWED_KEYS
    missing = ALLOWED_KEYS - set(frontmatter)
    if unexpected:
        errors.append(f"unexpected frontmatter keys: {', '.join(sorted(unexpected))}")
    if missing:
        errors.append(f"missing frontmatter keys: {', '.join(sorted(missing))}")

    name = frontmatter.get("name", "").strip()
    description = frontmatter.get("description", "").strip()
    if not name:
        errors.append("name must not be empty")
    elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        errors.append("name must use lowercase hyphen-case without leading, trailing, or repeated hyphens")
    elif len(name) > MAX_NAME_LENGTH:
        errors.append(f"name exceeds {MAX_NAME_LENGTH} characters")
    elif skill_dir.name != name:
        errors.append(f"skill directory name {skill_dir.name!r} does not match frontmatter name {name!r}")

    if not description:
        errors.append("description must not be empty")
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(f"description exceeds {MAX_DESCRIPTION_LENGTH} characters")
    elif "<" in description or ">" in description:
        errors.append("description cannot contain angle brackets")

    if len(text.splitlines()) > MAX_SKILL_LINES:
        errors.append(f"SKILL.md exceeds the {MAX_SKILL_LINES}-line progressive-disclosure limit")
    for filename in sorted(FORBIDDEN_ROOT_DOCS):
        if (skill_dir / filename).exists():
            errors.append(f"installable skill contains auxiliary root document: {filename}")
    errors.extend(validate_links(skill_dir, text))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_directory", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    errors = validate(args.skill_directory)
    result = {"status": "FAIL" if errors else "PASS", "errors": errors}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif errors:
        print("FAIL")
        for error in errors:
            print(f"ERROR {error}")
    else:
        print("3080-brief local skill validation PASS")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
