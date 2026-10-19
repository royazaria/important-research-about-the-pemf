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
    "oa": "PEMF: a Cochrane review and a meta-analysis of 16 placebo-controlled trials found less pain; gains in function were less clear. Shockwave: a meta-analysis of 14 knee trials found less pain and better function.",
    "spine": "A meta-analysis of 14 PEMF trials found more pain relief than placebo in low back pain. A 2026 network meta-analysis of 50 trials compares magnetic stimulation, shockwave and PEMF.",
    "msk": "Shockwave beat placebo in a JAMA trial of calcific shoulder tendinitis and a 250-patient heel-pain trial, but other trials in tennis elbow and heel pain found no difference. PEMF trials here are smaller and mixed.",
    "fibro": "Four studies of PEMF and magnetic stimulation. A 2025 meta-analysis of 6 sham-controlled trials found pain relief in the short term.",
    "bone": "A meta-analysis of 22 trials found higher fracture healing rates with PEMF, while reviews found no effect on fresh fractures or spinal fusion rates. Shockwave matched surgery in one nonunion trial.",
    "mens": "Mostly shockwave: five sham-controlled trials in erectile dysfunction (one negative), several meta-analyses, and a 2025 Cochrane review that rates the benefit as small and the evidence as low certainty. In Peyronie's disease, shockwave eased pain but not curvature.",
    "pelvic": "In men with chronic pelvic pain, a Cochrane review rates the short-term benefit of shockwave as high-quality evidence; evidence for magnetic chairs is uncertain. One trial combined the two.",
    "incontinence": "A review of 24 trials found magnetic stimulation improved urinary incontinence. Of two sham-controlled trials in women, the larger (120 women) was positive and the other was not.",
    "headache": "A double-blind trial in 42 migraine sufferers at Madigan Army Medical Center, Tacoma.",
    "wounds": "Shockwave closed more diabetic foot ulcers than sham in two phase III trials. PEMF eased pain after cesarean section and breast reconstruction; Cochrane found no clear benefit for pressure or venous ulcers.",
    "neuro": "Shockwave and magnetic stimulation both reduced spasticity after stroke in meta-analyses. A large PEMF trial in diabetic nerve pain was negative.",
    "circulation": "Two Mayo Clinic trials, in high blood pressure and in metabolic syndrome.",
    "general": "The 1980 Lancet report that began medical shockwave use, PEMF trials in chronic sinusitis and older adults, and a review of PEMF's medical uses.",
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
JOURNALS = ["JAMA", "The Lancet", "BMJ", "Annals of Internal Medicine", "Cochrane Database of Systematic Reviews",
            "Journal of Bone and Joint Surgery", "American Journal of Sports Medicine", "European Urology", "Journal of Urology",
            "Journal of Sexual Medicine", "Stroke", "Plastic and Reconstructive Surgery", "Osteoarthritis and Cartilage",
            "Rheumatology (Oxford)", "Physical Therapy", "Archives of Physical Medicine and Rehabilitation", "The Spine Journal",
            "Clinical Rehabilitation", "Bioelectromagnetics"]


def research_fills():
    studies, conditions = load_studies()
    reviews = sum(1 for s in studies if re.search("meta|systematic", s["design"], re.I))
    rcts = [s for s in studies if s["design"] == "RCT"]
    figures = """<div class="rs-figures">
  <div><b class="hl">%d</b><span>published studies, each linked to the original</span></div>
  <div><b>%d</b><span>systematic reviews and meta-analyses</span></div>
  <div><b>%d</b><span>randomized trials</span></div>
  <div><b>%d</b><span>on shockwave, or shockwave combined with PEMF</span></div>
</div>""" % (len(studies), reviews, len(rcts), sum(1 for s in studies if s.get("technology") in ("shockwave", "combined")))
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
            "{{small_trials}}": str(small), "{{rct_count}}": str(len(rcts)), "{{study_count}}": str(len(studies)),
            "{{shockwave_count}}": str(sum(1 for s in studies if s.get("technology") == "shockwave")),
            "{{combined_count}}": str(sum(1 for s in studies if s.get("technology") == "combined"))}


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


TECH = {"pemf": "PEMF", "shockwave": "Shockwave", "combined": "PEMF and shockwave"}
DESIGN_RANK = {"Meta-analysis": 0, "Systematic review": 0, "RCT": 1, "Clinical study": 2, "Review": 3, "Lab study": 4}
SITE = "https://pemf-research.com/"


SMALL = {"of", "and", "the", "in", "for", "on", "to", "a", "an", "at", "by", "with", "&"}


def journal_name(s):
    """PubMed stores some full journal names in lowercase; title-case them for display."""
    name = s.get("journal_full") or s.get("journal", "")
    name = re.sub(r"\s*\([^)]*\)\s*$", "", re.sub(r"\s+:\s.*$", "", name))  # drop ": Official journal of..." and "(Oxford, England)"
    words = name.split()
    if not any(w[:1].islower() and w.lower() not in SMALL for w in words[1:]) and words[:1] != [words[0].lower()]:
        return name
    return " ".join(w if (i and w.lower() in SMALL) else (w[:1].upper() + w[1:]) for i, w in enumerate(words))


def study_url(s):
    return "studies/%s.html" % s["slug"]


def build_study_pages():
    """One page per study: plain-English summary, why it matters, the citation and related studies."""
    studies, conditions = load_studies()
    label = dict(conditions)
    slugs = [s.get("slug") for s in studies]
    dupes = {x for x in slugs if x and slugs.count(x) > 1}
    assert not dupes, "duplicate study slugs: %s" % dupes
    for s in studies:
        if not (s.get("slug") and s.get("summary") and s.get("importance")):
            continue
        rel = study_url(s)
        same = [o for o in studies if o is not s and o.get("condition") == s.get("condition") and o.get("slug")]
        same.sort(key=lambda o: (DESIGN_RANK.get(o["design"], 9), -int(o["year"])))
        related = "".join('<li><a href="%s.html"><div><h3>%s</h3><p>%s &middot; %s</p></div><span class="go">&rarr;</span></a></li>'
                          % (o["slug"], html.escape(o["headline"]), html.escape(o["design"]), o["year"]) for o in same[:6])
        facts = [("Study type", s["design"]), ("Year", str(s["year"])),
                 ("Participants", "{:,}".format(s["n"]) if isinstance(s.get("n"), int) else "Not stated in the abstract"),
                 ("Condition", label.get(s.get("condition"), "")), ("Technology", TECH.get(s.get("technology"), "PEMF")),
                 ("Journal", journal_name(s)), ("Institution", s.get("location", "")),
                 ("First author", s.get("author", ""))]
        dl = "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (k, html.escape(v)) for k, v in facts if v)
        src_name = "PubMed" if "pubmed" in s["link"] else "the publisher"
        title_line = ('<p class="orig"><span>Original title</span>%s</p>' % html.escape(s["title"])) if s.get("title") else ""
        content = """
<div class="page-head">
  <div class="wrap">
    <p class="crumbs"><a href="../">PEMF Research</a> / <a href="../research.html">Research database</a> / %(design)s, %(year)s</p>
    <p class="label">%(tech)s &middot; %(cond)s</p>
    <h1>%(headline)s</h1>
    %(orig)s
  </div>
</div>
<div class="wrap letter study">
  <aside>
    <dl class="study-facts">%(dl)s</dl>
    <p style="margin-top:22px"><a class="btn" href="%(link)s" target="_blank" rel="noopener">Read it on %(src)s</a></p>
  </aside>
  <article class="prose">
    <h2>In short</h2>
    <p>%(summary)s</p>
    <h2>Why it matters</h2>
    <p>%(importance)s</p>
    <p class="translation-note">A plain-English summary written from the published abstract by the editors of this site. It describes this study, not any particular device or clinic, and it is not medical advice. Read the original on %(src)s for the full methods and results.</p>
  </article>
</div>
<section class="sec alt">
  <div class="wrap">
    <div class="head"><p class="label">Related studies</p><h2>More on %(cond_lc)s.</h2></div>
    <ul class="index">%(related)s</ul>
    <p style="margin-top:28px"><a class="more" href="../research.html?c=%(ckey)s">All studies on %(cond_lc)s</a></p>
  </div>
</section>""" % {
            "design": html.escape(s["design"]), "year": s["year"], "tech": TECH.get(s.get("technology"), "PEMF"),
            "cond": html.escape(label.get(s.get("condition"), "")), "cond_lc": html.escape(label.get(s.get("condition"), "").lower()),
            "ckey": s.get("condition", ""), "headline": html.escape(s["headline"]), "orig": title_line, "dl": dl,
            "link": html.escape(s["link"], quote=True), "src": src_name, "summary": html.escape(s["summary"]),
            "importance": html.escape(s["importance"]), "related": related}
        about = {"@type": "ScholarlyArticle", "name": s.get("title") or s["headline"], "url": s["link"],
                 "datePublished": str(s["year"]), "author": s.get("author", "")}
        if s.get("journal_full") or s.get("journal"):
            about["isPartOf"] = {"@type": "Periodical", "name": journal_name(s)}
        ld = {"@context": "https://schema.org", "@type": "WebPage", "name": s["headline"], "url": SITE + rel,
              "description": s["summary"], "about": about}
        head = '<script type="application/ld+json">%s</script>' % json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
        desc = s["summary"] if len(s["summary"]) <= 158 else s["summary"][:155].rsplit(" ", 1)[0] + "..."
        meta = {"title": "%s (%s, %s) | PEMF Research" % (s["headline"], s.get("journal", ""), s["year"]),
                "description": desc, "path": rel, "nav": "research"}
        write(rel, render(content, meta, head=head))


def build_sitemap():
    """Static pages, every guide on disk (Jack adds guides) and every study page."""
    old = (ROOT / "sitemap.xml").read_text(encoding="utf-8") if (ROOT / "sitemap.xml").exists() else ""
    lastmod = dict(re.findall(r"<loc>(.*?)</loc><lastmod>(.*?)</lastmod>", old))
    urls = [SITE, SITE + "research.html", SITE + "safety.html", SITE + "guides/"]
    urls += [SITE + "guides/" + p.name for p in sorted((ROOT / "guides").glob("*.html")) if p.name != "index.html"]
    studies, _ = load_studies()
    urls += [SITE + study_url(s) for s in studies if s.get("slug") and s.get("summary")]
    rows = "".join("  <url><loc>%s</loc>%s</url>\n" % (u, "<lastmod>%s</lastmod>" % lastmod[u] if u in lastmod else "") for u in urls)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s</urlset>\n' % rows)


if __name__ == "__main__":
    build_pages()
    build_doctor_redirects()
    build_study_pages()
    build_sitemap()
