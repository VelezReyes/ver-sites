"""Decide which areas to publish after a push to main.

- A change under an area folder publishes that area.
- A change to _template/, scripts/ or areas.json publishes every live area.
- A manual run can target one area or "all".
Only areas marked "live": true in areas.json are ever published.

Writes `matrix` (JSON) and `any` (true/false) to $GITHUB_OUTPUT.
"""
import argparse
import json
import os
import subprocess

from config import GLOBAL_PATHS, area_info, live_areas, load_config

ZERO_SHA = "0" * 40


def changed_files(base, head):
    if not base or base == ZERO_SHA:
        return None  # first push or unknown history: treat as "everything"
    try:
        out = subprocess.run(
            ["git", "diff", "--name-only", base, head],
            check=True, capture_output=True, text=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None  # base not in history (e.g. force push): rebuild everything
    return [line for line in out.splitlines() if line]


def select(config, base, head, requested):
    live = live_areas(config)
    if requested and requested != "all":
        if requested not in config["areas"]:
            raise SystemExit(f"Unknown area '{requested}'.")
        info = area_info(config, requested)
        if not info["live"]:
            raise SystemExit(f"Area '{requested}' isn't live yet. Set \"live\": true in areas.json first.")
        return [info]
    if requested == "all":
        return live

    files = changed_files(base, head)
    if files is None or any(f.startswith(GLOBAL_PATHS) for f in files):
        return live
    touched = {f.split("/", 1)[0] for f in files}
    return [a for a in live if a["area"] in touched]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="")
    p.add_argument("--head", default="HEAD")
    p.add_argument("--area", default="")
    args = p.parse_args()

    areas = select(load_config(), args.base, args.head, args.area.strip())
    matrix = {"include": areas}
    print("Areas to publish:", ", ".join(a["area"] for a in areas) or "none")

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"matrix={json.dumps(matrix)}\n")
            f.write(f"any={'true' if areas else 'false'}\n")


if __name__ == "__main__":
    main()
