"""Checks every pull request before it can be merged.

Errors block the merge. Warnings show up as annotations on the PR so a
reviewer can look, but they don't block.

Run locally:  python scripts/validate.py
"""
import json
import os
import re
import sys
from pathlib import Path

from config import RESERVED_DIRS, ROOT, ROOT_FILES, SLUG_RE, load_config

TEXT_EXTS = {".html", ".htm", ".md", ".txt", ".json", ".csv", ".js", ".svg", ".xml"}
DATA_EXTS = {".csv", ".xlsx", ".xls", ".json"}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
# 8 to 11 digit runs: likely ID numbers (cédulas) or phone numbers.
LONG_DIGITS_RE = re.compile(r"(?<![\d.#-])\d{8,11}(?![\d.])")
# "logo@2x.png" looks like an email to the regex; skip file names.
FILE_TLDS = {"png", "jpg", "jpeg", "gif", "svg", "webp", "avif", "css", "js", "woff", "woff2"}
MAX_WARNINGS_PER_FILE = 5

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ORG_DOMAINS = load_config()["checks"].get("allowed_email_domains", ["velezreyesmas.org"])
OWNER_RE = re.compile(r"^[A-Za-z0-9._%+-]+@(" + "|".join(re.escape(d) for d in ORG_DOMAINS) + r")$", re.I)

IN_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"
errors, warnings = [], []


def report(kind, path, msg, line=None):
    rel = path.relative_to(ROOT).as_posix() if isinstance(path, Path) else path
    (errors if kind == "error" else warnings).append((rel, msg, line))


def emit():
    for kind, items in (("error", errors), ("warning", warnings)):
        for rel, msg, line in items:
            if IN_ACTIONS:
                loc = f"file={rel}" + (f",line={line}" if line else "")
                print(f"::{kind} {loc}::{msg}")
            else:
                print(f"{kind.upper()}: {rel}{':' + str(line) if line else ''}: {msg}")


def check_structure(config):
    areas = set(config["areas"])
    for slug in areas:
        if not SLUG_RE.match(slug):
            report("error", "areas.json", f"Area slug '{slug}' must be lowercase letters, numbers and hyphens.")

    for entry in sorted(ROOT.iterdir()):
        name = entry.name
        if name.startswith(".git") and name != ".github":
            continue
        if entry.is_file():
            if name not in ROOT_FILES:
                report("error", entry, "Files can't sit in the repo root. Put pages inside an area/project folder.")
            continue
        if name in RESERVED_DIRS or name.startswith("."):
            continue
        if name not in areas:
            report("error", entry, f"'{name}' isn't an area in areas.json. Use one of: {', '.join(sorted(areas))}.")
            continue
        check_area(entry)


def check_area(area_dir):
    for entry in sorted(area_dir.iterdir()):
        if entry.is_file():
            if entry.name != ".gitkeep":
                report("error", entry, "Files can't sit directly in an area folder. Put them in a project folder.")
            continue
        if not SLUG_RE.match(entry.name):
            report("error", entry, f"Project folder '{entry.name}' must use lowercase letters, numbers and hyphens (no accents or spaces).")
        if entry.name.startswith("_"):
            report("error", entry, "Project folders can't start with '_' (reserved for shared assets).")
        if not (entry / "index.html").is_file():
            report("error", entry, "Every project needs an index.html.")
        check_project_json(entry)


def check_project_json(project_dir):
    """Every project needs a project.json naming an accountable owner."""
    meta = project_dir / "project.json"
    if not meta.is_file():
        report("error", project_dir, "Missing project.json. Every project needs one with at least an \"owner\" email.")
        return
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("must be a JSON object")
    except (ValueError, json.JSONDecodeError) as e:
        report("error", meta, f"project.json isn't valid JSON: {e}")
        return

    owner = data.get("owner")
    if not owner or not isinstance(owner, str):
        report("error", meta, "Missing \"owner\": the email of the person responsible for this page.")
    elif not OWNER_RE.match(owner.strip()):
        report("error", meta, f"\"owner\" must be one person's email at {' or '.join(ORG_DOMAINS)} (got '{owner}').")

    updated = data.get("updated")
    if updated is not None and not (isinstance(updated, str) and DATE_RE.match(updated)):
        report("error", meta, "\"updated\" must be a date written as YYYY-MM-DD.")
    if "hidden" in data and not isinstance(data["hidden"], bool):
        report("error", meta, "\"hidden\" must be true or false (no quotes).")
    for field in ("title", "description"):
        if field in data and not isinstance(data[field], str):
            report("error", meta, f"\"{field}\" must be text.")


def check_files(config):
    max_bytes = config["checks"].get("max_file_mb", 25) * 1024 * 1024
    allowed_domains = {d.lower() for d in config["checks"].get("allowed_email_domains", [])}

    for area in config["areas"]:
        area_dir = ROOT / area
        if not area_dir.is_dir():
            continue
        for path in area_dir.rglob("*"):
            if not path.is_file():
                continue
            size = path.stat().st_size
            if size > max_bytes:
                report("error", path, f"File is {size / 1048576:.1f} MB; the limit is {max_bytes // 1048576} MB.")
            ext = path.suffix.lower()
            if ext in DATA_EXTS and path.name != "project.json":
                report("warning", path, "Raw data file on a public site. Confirm it holds no personal data.")
            if ext in TEXT_EXTS:
                scan_text(path, allowed_domains)


def scan_text(path, allowed_domains):
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return
    digit_warnings = 0
    for i, line in enumerate(lines, start=1):
        for m in EMAIL_RE.finditer(line):
            domain = m.group(1).lower()
            if domain.rsplit(".", 1)[-1] in FILE_TLDS:
                continue
            if not any(domain == d or domain.endswith("." + d) for d in allowed_domains):
                report("error", path, "Email address found. Public pages can't include personal emails; remove it or anonymize the data.", i)
                break
        if digit_warnings < MAX_WARNINGS_PER_FILE and LONG_DIGITS_RE.search(line):
            digit_warnings += 1
            report("warning", path, "Long number found (could be an ID or phone number). Check it isn't personal data.", i)


def main():
    config = load_config()
    check_structure(config)
    check_files(config)
    emit()
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s).")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
