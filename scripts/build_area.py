"""Build the publishable site for one area.

    python scripts/build_area.py education _build/education

Output layout (this is what lands in the site-<area> repo):
    index.html        generated list of the area's projects
    404.html          generated not-found page
    CNAME             <area>.velezreyesmas.org
    .nojekyll         serve files as-is
    _assets/          shared brand CSS and images from _template/assets
    <project>/...     each project folder, copied unchanged
"""
import html
import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

from config import ROOT, area_info, load_config

FONTS = ("https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800"
         "&family=Roboto:wght@400;500&display=swap")
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
DESC_RE = re.compile(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', re.I | re.S)


def git_date(path):
    """Date of the last commit touching this folder, or None outside git."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path)],
            cwd=ROOT, check=True, capture_output=True, text=True,
        ).stdout.strip()
        return out or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def project_meta(folder):
    meta = {}
    pj = folder / "project.json"
    if pj.is_file():
        meta = json.loads(pj.read_text(encoding="utf-8"))
    page = (folder / "index.html").read_text(encoding="utf-8", errors="replace")[:20000]
    if not meta.get("title"):
        m = TITLE_RE.search(page)
        meta["title"] = html.unescape(m.group(1).strip()) if m else folder.name.replace("-", " ").capitalize()
    if not meta.get("description"):
        m = DESC_RE.search(page)
        meta["description"] = html.unescape(m.group(1).strip()) if m else ""
    meta["updated"] = meta.get("updated") or git_date(folder)
    meta["slug"] = folder.name
    meta["hidden"] = bool(meta.get("hidden", False))
    return meta


def nice_date(iso):
    try:
        d = date.fromisoformat(iso)
    except (TypeError, ValueError):
        return None
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{months[d.month - 1]} {d.day}, {d.year}"


def page_shell(title, body, area_name):
    e = html.escape
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="/_assets/ver.css">
</head>
<body>
<div class="ver-wrap">
  <header class="ver-banner"><a href="https://velezreyesmas.org"><img src="/_assets/header.png" alt="VélezReyes+ home" width="640" height="37"></a></header>
{body}
  <footer class="ver-footer">{e(area_name)} at VélezReyes+</footer>
</div>
</body>
</html>
"""


def render_index(info, projects):
    e = html.escape
    if projects:
        rows = []
        for p in projects:
            when = nice_date(p["updated"])
            time_html = f'<time datetime="{e(p["updated"])}">Updated {when}</time>' if when else ""
            desc_html = f'<span class="desc">{e(p["description"])}</span>' if p["description"] else ""
            rows.append(
                f'    <li><a href="/{e(p["slug"])}/"><span class="title">{e(p["title"])}</span>'
                f"{time_html}{desc_html}</a></li>"
            )
        listing = '  <ul class="ver-projects">\n' + "\n".join(rows) + "\n  </ul>"
    else:
        listing = '  <p class="ver-empty">No public projects yet.</p>'

    body = f"""  <main>
  <section class="ver-area-head">
    <h1>{e(info["name"])}</h1>
    <p>Public projects, reports and tools from the {e(info["name"])} team.</p>
  </section>
{listing}
  </main>"""
    return page_shell(f'{info["name"]} | VélezReyes+', body, info["name"])


def render_404(info):
    body = """  <main class="ver-article">
    <h1>Page not found</h1>
    <p class="lede">This address doesn't match any published project. It may have moved or been unpublished.</p>
    <p><a href="/">See all projects</a></p>
  </main>"""
    return page_shell(f'Not found | {info["name"]} | VélezReyes+', body, info["name"])


def build(area, out_dir):
    config = load_config()
    if area not in config["areas"]:
        raise SystemExit(f"Unknown area '{area}'.")
    info = area_info(config, area)
    src = ROOT / area
    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    projects = []
    if src.is_dir():
        for folder in sorted(p for p in src.iterdir() if p.is_dir()):
            shutil.copytree(folder, out / folder.name, ignore=shutil.ignore_patterns(".gitkeep"))
            meta = project_meta(folder)
            if not meta["hidden"]:
                projects.append(meta)
    # Most recently updated first; undated projects last, alphabetically.
    dated = [p for p in projects if p["updated"]]
    undated = sorted((p for p in projects if not p["updated"]), key=lambda p: p["title"].lower())
    dated.sort(key=lambda p: p["updated"], reverse=True)
    projects = dated + undated

    shutil.copytree(ROOT / "_template" / "assets", out / "_assets")
    (out / "index.html").write_text(render_index(info, projects), encoding="utf-8")
    (out / "404.html").write_text(render_404(info), encoding="utf-8")
    (out / "CNAME").write_text(info["domain"] + "\n", encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {area} → {out} ({len(projects)} listed project(s)) for {info['domain']}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/build_area.py <area> <output-dir>")
    build(sys.argv[1], sys.argv[2])
