"""Shared helpers: read areas.json and derive repo/domain names for each area."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "areas.json"

# Top-level folders that are not areas.
RESERVED_DIRS = {".github", "_template", "scripts", "docs", "_build"}
# Top-level files allowed in the repo root.
ROOT_FILES = {"areas.json", "README.md", ".gitignore", "LICENSE"}
# Changes here affect every area, so every live area is rebuilt.
GLOBAL_PATHS = ("_template/", "scripts/", "areas.json")

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def area_info(config, slug):
    """Everything the build and sync steps need to know about one area."""
    area = config["areas"][slug]
    return {
        "area": slug,
        "name": area["name"],
        "live": bool(area.get("live", False)),
        "repo": area.get("repo", f"site-{slug}"),
        "domain": area.get("subdomain", slug) + "." + config["domain"],
    }


def live_areas(config):
    return [area_info(config, s) for s in config["areas"] if config["areas"][s].get("live")]
