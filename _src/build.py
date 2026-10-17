"""Build pemf-research.com from _src/ into the repo root.

Pages:   _src/pages/**.html  -> same path at the root, wrapped in _src/layout.html
Doctors: _src/doctors.json + ../pemf-research-content/<slug>.en.md -> doctors/<file>.html and doctors/index.html
Folders starting with "_" are ignored by GitHub Pages (Jekyll), so _src is never published.

Run:  python _src/build.py
"""
import html
import json
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_src"
LAYOUT = (SRC / "layout.html").read_text(encoding="utf-8")
DOCTORS = json.loads((SRC / "doctors.json").read_text(encoding="utf-8"))
CONTENT = ROOT.parent / "pemf-research-content"  # translations + translator notes; kept OUTSIDE the public repo

META_RE = re.compile(r"^<!--meta (\{.*?\}) -->\s*", re.S)
SCRIPTS_RE = re.compile(r"<!--scripts\s*(.*?)-->\s*$", re.S)
FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
NAV_KEYS = ["research", "doctors", "safety", "about"]


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


def strip_front(md):
    """Drop YAML front matter and translator comments (<!-- ... -->), which are internal notes, not page text."""
    m = FRONT_RE.match(md)
    body = md[m.end():] if m else md
    body = re.sub(r"<!--.*?-->\s*", "", body, flags=re.S)
    return body, (m.group(1) if m else "")


def doctor_card(d, root):
    img = ('<img class="ph" src="%sassets/%s" alt="%s" loading="lazy">' % (root, d["photo"], html.escape(d["name"]))
           if d.get("photo") else '<span class="ini" aria-hidden="true">%s</span>' % html.escape(d["initials"]))
    link = ('<a class="more" href="%s">%s</a>' % (d["file"], html.escape(d["link_text"]))) if d.get("file") else ""
    src = ""
    if d.get("sources"):
        src = '<p class="srcs">Independent sources: ' + " · ".join(
            '<a href="%s" rel="noopener">%s</a>' % (html.escape(u, quote=True), html.escape(t)) for t, u in d["sources"]) + "</p>"
    return ('<li>%s<div><h3>%s</h3><p class="role">%s</p><p class="what">%s</p>%s</div>%s</li>'
            % (img, html.escape(d["name"]), html.escape(d["title"]), html.escape(d["summary"]), src, link))


def build_doctors():
    cards = "\n".join(doctor_card(d, "../") for d in DOCTORS["people"])
    content = """
<div class="page-head">
  <div class="wrap">
    <p class="crumbs"><a href="../">PEMF Research</a> / Physicians</p>
    <p class="label">Physicians and letters</p>
    <h1>The physicians who reviewed PEMF, and what they wrote.</h1>
    <p class="lede">These reviews, opinions and statements were written in Hebrew for PainFree's Israeli site, painfree.org.il. Each one is translated into English here and links back to the Hebrew original.</p>
  </div>
</div>
<section style="padding:clamp(36px,5vw,64px) 0 clamp(72px,8vw,110px)">
  <div class="wrap">
    <ul class="people">
%s
    </ul>
  </div>
</section>""" % cards
    meta = {"title": "Physicians and letters — PEMF Research | PainFree",
            "description": "English translations of the Israeli physicians' reviews and opinions on PEMF therapy: Prof. Gabi Zeilig, Prof. Itamar Grotto and the physicians who work with PainFree.",
            "path": "doctors/", "nav": "doctors"}
    write("doctors/index.html", render(content, meta))

    for d in DOCTORS["people"]:
        if not d.get("file"):
            continue
        md, _ = strip_front((CONTENT / d["source_md"]).read_text(encoding="utf-8"))
        md = re.sub(r"^#\s+.*\n", "", md, count=1)  # page title comes from doctors.json
        body = markdown.markdown(md, extensions=["tables", "sane_lists"])
        photo = ('<img src="../assets/%s" alt="%s">' % (d["photo"], html.escape(d["name"]))) if d.get("photo") else ""
        aside = """<aside>%s<b>%s</b>%s
  <dl><dt>Document</dt><dd>%s</dd><dt>Original (Hebrew)</dt><dd><a href="%s">painfree.org.il</a></dd></dl>
</aside>""" % (photo, html.escape(d["name"]), html.escape(d["title"]), html.escape(d["doc_type"]), d["source_url"])
        content = """
<div class="page-head">
  <div class="wrap">
    <p class="crumbs"><a href="../">PEMF Research</a> / <a href="./">Physicians</a> / %s</p>
    <p class="label">%s</p>
    <h1>%s</h1>
  </div>
</div>
<div class="wrap letter">
%s
  <article class="prose">
%s
    <p class="translation-note">English translation of the Hebrew original published on painfree.org.il. Names, titles, numbers and study references are kept exactly as in the original.</p>
  </article>
</div>""" % (html.escape(d["name"]), html.escape(d["doc_type"]), html.escape(d["headline"]), aside, body)
        meta = {"title": "%s — %s | PEMF Research" % (d["headline"], d["name"]),
                "description": d["summary"], "path": "doctors/" + d["file"], "nav": "doctors"}
        write("doctors/" + d["file"], render(content, meta))

    extra = DOCTORS.get("pages", [])
    for p in extra:
        md, _ = strip_front((CONTENT / p["source_md"]).read_text(encoding="utf-8"))
        md = re.sub(r"^#\s+.*\n", "", md, count=1)
        body = markdown.markdown(md, extensions=["tables", "sane_lists"])
        content = """
<div class="page-head">
  <div class="wrap">
    <p class="label">%s</p>
    <h1>%s</h1>
    <p class="lede">%s</p>
  </div>
</div>
<div class="wrap" style="padding:clamp(40px,6vw,72px) var(--gutter) clamp(72px,8vw,110px)">
  <article class="prose">
%s
    <p class="translation-note">Translated from the Hebrew original on <a href="%s">painfree.org.il</a>.</p>
  </article>
</div>""" % (html.escape(p["label"]), html.escape(p["headline"]), html.escape(p["lede"]), body, p["source_url"])
        meta = {"title": p["title"], "description": p["lede"], "path": p["file"], "nav": p.get("nav", "")}
        write(p["file"], render(content, meta))


def build_pages():
    root_cards = "\n        ".join(
        '<li><a href="doctors/%s"><div><h3>%s</h3><p>%s</p></div><span class="go">&rarr;</span></a></li>'
        % (d["file"], html.escape(d["name"]), html.escape(d["title"])) for d in DOCTORS["people"] if d.get("file"))
    q = DOCTORS["home_quote"]
    quote = ('<blockquote class="quote">%s</blockquote><p class="quote-by"><b>%s</b>%s</p>'
             % (html.escape(q["text"]), html.escape(q["name"]), html.escape(q["title"])))
    patients = (SRC / "patients.html").read_text(encoding="utf-8") if (SRC / "patients.html").exists() else ""
    for src in sorted((SRC / "pages").rglob("*.html")):
        raw = src.read_text(encoding="utf-8")
        m = META_RE.match(raw)
        meta = json.loads(m.group(1))
        body = raw[m.end():]
        sm = SCRIPTS_RE.search(body)
        scripts = sm.group(1).strip() if sm else ""
        if sm:
            body = body[:sm.start()]
        body = (body.replace("{{zeilig_quote}}", quote)
                    .replace("{{doctor_links}}", root_cards)
                    .replace("{{patients_section}}", patients))
        rel = src.relative_to(SRC / "pages").as_posix()
        write(rel, render(body, meta, scripts))


if __name__ == "__main__":
    build_pages()
    build_doctors()
