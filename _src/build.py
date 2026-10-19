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


def load_studies():
    """studies.js holds window.STUDIES and window.CONDITIONS as JSON literals."""
    js = (ROOT / "studies.js").read_text(encoding="utf-8")
    studies = json.loads(re.search(r"window\.STUDIES = (\[.*?\n\]);", js, re.S).group(1))
    conditions = json.loads(re.search(r"window\.CONDITIONS = (\[.*?\]);", js, re.S).group(1))
    return studies, conditions


# One line per condition, written from the studies filed under it (numbers must match studies.js).
SUMMARIES = {
    "oa": "A Cochrane review of 9 trials found more pain relief than placebo. A 2024 review of 17 trials (1,197 patients) reported pain down 60%.",
    "spine": "A meta-analysis of 14 trials (618 people) found more pain relief than placebo in low back pain, particularly chronic low back pain.",
    "msk": "A 2025 US multi-center trial: pain down 36%, against 10% with standard care. A 2025 meta-analysis covers shoulder impingement.",
    "fibro": "Three sham-controlled trials. The largest, in 56 women, improved pain, function and fatigue.",
    "bone": "A meta-analysis of 22 trials (1,468 patients): healing rose to 79.7%, against 64.3% with sham. The first FDA-approved PEMF use, in 1979.",
    "mens": "A meta-analysis of 32 trials (1,986 men): micro-energy treatments, including electromagnetic fields, improved erectile function.",
    "incontinence": "A systematic review of 24 trials: magnetic stimulation of the pelvic floor improved symptoms and quality of life.",
    "headache": "A double-blind trial in 42 migraine sufferers at Madigan Army Medical Center, and a 2024 trial in chronic sinusitis.",
    "wounds": "Reviews of PEMF for pain and swelling after plastic surgery and for slow-healing wounds.",
    "circulation": "Two Mayo Clinic trials, in high blood pressure and in metabolic syndrome.",
    "general": "A community study in 101 adults and a review of the medical uses of PEMF.",
}
BRIEFS = {
    "oa": ("Knee osteoarthritis brief", "https://painfreeusa.health/insights/pemf-knee-osteoarthritis-evidence-brief.html"),
    "spine": ("Low back pain guide", "guides/pemf-chronic-low-back-pain-evidence.html"),
    "msk": ("Shoulder brief", "https://painfreeusa.health/insights/pemf-shoulder-impingement-rotator-cuff-evidence-brief.html"),
}
KIND = {  # study design -> (singular, plural), in the order the condition cards list them
    "Systematic review": ("systematic review", "systematic reviews"),
    "Meta-analysis": ("systematic review", "systematic reviews"),
    "RCT": ("randomized trial", "randomized trials"),
    "Clinical study": ("clinical study", "clinical studies"),
    "Review": ("narrative review", "narrative reviews"),
    "Lab study": ("lab study", "lab studies"),
}
JOURNALS = ["JAMA", "Cochrane Database of Systematic Reviews", "Rheumatology (Oxford)", "Physical Therapy", "The Spine Journal",
            "Journal of Rheumatology", "Clinical Rehabilitation", "Journal of Pain Research", "Pain and Therapy", "Bioelectromagnetics",
            "Clinical Journal of Pain", "World Journal of Men's Health", "Neurourology and Urodynamics", "BMC Geriatrics",
            "Frontiers in Medicine", "PLoS One", "Headache"]


def research_fills():
    studies, conditions = load_studies()
    reviews = sum(1 for s in studies if re.search("meta|systematic", s["design"], re.I))
    rcts = [s for s in studies if s["design"] == "RCT"]
    years = [int(s["year"]) for s in studies if s.get("year")]  # two entries store the year as a string
    figures = """<div class="rs-figures">
  <div><b class="hl">%d</b><span>published studies, each linked to the original</span></div>
  <div><b>%d</b><span>systematic reviews and meta-analyses</span></div>
  <div><b>%d</b><span>randomized trials</span></div>
  <div><b>%d</b><span>first study in the database, in JAMA</span></div>
</div>""" % (len(studies), reviews, len(rcts), min(years))
    journals = '<p class="rs-journals"><span>Published in</span> %s</p>' % " &middot; ".join(html.escape(j) for j in JOURNALS)
    cards = []
    for key, label in conditions:
        rows = [s for s in studies if s.get("condition") == key]
        if not rows:
            continue
        kinds = {}
        for s in rows:
            k = KIND.get(s["design"], ("other study", "other studies"))
            kinds[k] = kinds.get(k, 0) + 1
        order = list(dict.fromkeys(KIND.values()))
        parts = ["%d %s" % (n, one if n == 1 else many)
                 for (one, many), n in sorted(kinds.items(), key=lambda kv: order.index(kv[0]) if kv[0] in order else 99)]
        mix = parts[0] if len(parts) == 1 else "%d studies: %s" % (len(rows), ", ".join(parts))
        links = '<a class="more" href="research.html?c=%s">See the %s</a>' % (key, "study" if len(rows) == 1 else "%d studies" % len(rows))
        if key in BRIEFS:
            t, u = BRIEFS[key]
            links += ' <a class="more%s" href="%s">%s</a>' % (" out" if u.startswith("http") else "", u, html.escape(t))
        cards.append('<li><h3>%s</h3><p class="cn">%s</p><p>%s</p><p class="cl">%s</p></li>'
                     % (html.escape(label), mix, html.escape(SUMMARIES[key]), links))
    small = sum(1 for s in rcts if s.get("n") and s["n"] < 50)
    return {"{{figures}}": figures, "{{journals}}": journals,
            "{{conditions}}": '    <ul class="conds">' + "".join("\n      " + c for c in cards) + "\n    </ul>",
            "{{small_trials}}": str(small), "{{rct_count}}": str(len(rcts))}


def build_pages():
    fills = research_fills()
    for src in sorted((SRC / "pages").rglob("*.html")):
        raw = src.read_text(encoding="utf-8")
        m = META_RE.match(raw)
        meta = json.loads(m.group(1))
        body = raw[m.end():]
        sm = SCRIPTS_RE.search(body)
        scripts = sm.group(1).strip() if sm else ""
        if sm:
            body = body[:sm.start()]
        for k, v in fills.items():
            body = body.replace(k, v)
        rel = src.relative_to(SRC / "pages").as_posix()
        write(rel, render(body, meta, scripts))


if __name__ == "__main__":
    build_pages()
    build_doctor_redirects()
