"""Build pemf-research.com from _src/ into the repo root.

Pages:   _src/pages/**.html  -> same path at the root, wrapped in _src/layout.html
Doctors: moved to painfreeusa.health/doctors/ on 2026-10-18 (Roy: this site carries the studies only);
         doctors/*.html here are redirect stubs so old links keep working.
Folders starting with "_" are ignored by GitHub Pages (Jekyll), so _src is never published.

Run:  python _src/build.py
"""
import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_src"
LAYOUT = (SRC / "layout.html").read_text(encoding="utf-8")
US_DOCTORS = "https://painfreeusa.health/doctors/"
MOVED = ["index.html", "zeilig.html", "grotto.html", "savion.html", "ginzburg.html"]

META_RE = re.compile(r"^<!--meta (\{.*?\}) -->\s*", re.S)
SCRIPTS_RE = re.compile(r"<!--scripts\s*(.*?)-->\s*$", re.S)
NAV_KEYS = ["research", "guides", "safety"]


def render(content, meta, scripts="", head=""):
    path = meta.get("path", "")
    depth = path.count("/")
    root = "../" * depth
    out = LAYOUT
    for k in NAV_KEYS:
        out = out.replace("{{cur_%s}}" % k, ' aria-current="page"' if meta.get("nav") == k else "")
    fills = {
        "title": html.escape(meta["title"], quote=True),
        "description": html.escape(meta["description"], quote=True),
        "path": path,
        "head": head,
        "content": content,
        "scripts": scripts,
    }
    for k, v in fills.items():
        out = out.replace("{{%s}}" % k, v)
    return out.replace("{{root}}", root)


def write(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")
    print("wrote", rel)


REDIRECT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Moved to painfreeusa.health</title>
<meta name="robots" content="noindex, follow">
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url={url}">
</head>
<body><p>This page moved to <a href="{url}">{url}</a>.</p></body>
</html>
"""


def build_doctor_redirects():
    for f in MOVED:
        url = US_DOCTORS + ("" if f == "index.html" else f)
        write("doctors/" + f, REDIRECT.format(url=url))


def build_pages():
    for src in sorted((SRC / "pages").rglob("*.html")):
        raw = src.read_text(encoding="utf-8")
        m = META_RE.match(raw)
        meta = json.loads(m.group(1))
        body = raw[m.end():]
        sm = SCRIPTS_RE.search(body)
        scripts = sm.group(1).strip() if sm else ""
        if sm:
            body = body[:sm.start()]
        rel = src.relative_to(SRC / "pages").as_posix()
        write(rel, render(body, meta, scripts))


if __name__ == "__main__":
    build_pages()
    build_doctor_redirects()
