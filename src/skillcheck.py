#!/usr/bin/env python3
"""Lint a Markdown agent skill file without executing its contents."""
import argparse, re, sys
from pathlib import Path

REQUIRED = ("name", "description")
SECTIONS = ("instructions", "examples", "references")

def lint(path):
    text = path.read_text(encoding="utf-8")
    errors, warnings = [], []
    if not text.startswith("---\n"):
        errors.append("Missing YAML-style frontmatter at the beginning")
        body = text
    else:
        end = text.find("\n---", 4)
        if end < 0:
            errors.append("Frontmatter is not closed with ---")
            body = ""
        else:
            front = text[4:end]
            body = text[end + 4:]
            values = {}
            for line in front.splitlines():
                if ":" in line and not line.lstrip().startswith("#"):
                    key, value = line.split(":", 1)
                    values[key.strip()] = value.strip().strip("\"'")
            for key in REQUIRED:
                if not values.get(key):
                    errors.append(f"Frontmatter field '{key}' is required")
            name = values.get("name", "")
            if name and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
                errors.append("name must be lowercase words separated by hyphens")
            if len(values.get("description", "")) > 1024:
                warnings.append("description is longer than 1024 characters")
    headings = {m.group(1).strip().lower() for m in re.finditer(r"^#{1,3}\s+(.+)$", body, re.M)}
    for section in SECTIONS:
        if not any(section in heading for heading in headings):
            warnings.append(f"Consider adding a '{section}' section")
    for target in re.findall(r"\]\((?!https?://|mailto:|#)([^)]+)\)", body):
        local = (path.parent / target.split("#", 1)[0]).resolve()
        if target and not local.exists():
            errors.append(f"Broken local link: {target}")
    return errors, warnings

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    if not args.file.is_file():
        parser.error(f"File not found: {args.file}")
    errors, warnings = lint(args.file)
    for item in errors: print("ERROR:", item)
    for item in warnings: print("WARN: ", item)
    if not errors and not warnings: print("OK: skill file passed all checks")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
