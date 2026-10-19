"""Check studies against PubMed before anything reaches pemf-research.com.

For every entry with a PMID: the record exists, year / first author / journal match, and every number
quoted in description + summary + importance appears in the abstract (or title). Prints a report and
writes enriched.json (title, journal_full, doi added) next to this script.

Usage: python _src/tools/check_studies.py                 (checks every entry in studies.js)
       python _src/tools/check_studies.py new.json ...    (checks candidate entries before merging)
Flags are for a human to read: numbers that sit only in the full text (PMC) or are spelled out
differently are common and fine once confirmed; an unconfirmed number must be removed from the text.
"""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=40) as r:
                return r.read().decode("utf-8")
        except Exception as e:  # 429s and timeouts: back off and retry
            time.sleep(1.5 * (i + 1))
            err = e
    raise err


def batched(xs, n=40):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


UNITS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen "
                                    "fifteen sixteen seventeen eighteen nineteen".split())}
TENS = {w: 10 * i for i, w in enumerate("_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()) if w != "_"}


def words_to_digits(text):
    """'one hundred eighteen' -> '118', 'twenty-two' -> '22', 'sixteen' -> '16' (enough for abstracts)."""
    tokens = re.split(r"(\s+|-)", text)
    out, cur, active = [], 0, False
    for t in tokens:
        w = t.lower().strip(".,;:()")
        if w in UNITS or w in TENS or (w == "hundred" and active):
            cur = cur * 100 if w == "hundred" else cur + UNITS.get(w, 0) + TENS.get(w, 0)
            active = True
            continue
        if active and (t.isspace() or t == "-" or w == "and"):
            continue
        if active:
            out.append(" %d " % cur)
            cur, active = 0, False
        out.append(t)
    if active:
        out.append(" %d " % cur)
    return "".join(out)


def numbers(text):
    """Numbers worth checking: anything with a digit, normalised (1,197 -> 1197; 79.7% -> 79.7)."""
    out = set()
    for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", text or ""):
        v = m.group(0).replace(",", "")
        if re.fullmatch(r"(19|20)\d\d", v):  # years are checked separately
            continue
        out.add(v.rstrip("."))
    return out


def main(files):
    entries = []
    if not files:
        js = (HERE.parent.parent / "studies.js").read_text(encoding="utf-8")
        for e in json.loads(re.search(r"window\.STUDIES = (\[.*?\n\]);", js, re.S).group(1)):
            e["_file"] = "studies.js"
            entries.append(e)
    for f in files:
        for e in json.loads(Path(f).read_text(encoding="utf-8")):
            e["_file"] = Path(f).name
            entries.append(e)
    pmids = sorted({str(e["pmid"]) for e in entries if e.get("pmid")})
    summ, abstracts = {}, {}
    for chunk in batched(pmids):
        d = json.loads(get(EU + "esummary.fcgi?db=pubmed&retmode=json&id=" + ",".join(chunk)))["result"]
        for p in chunk:
            summ[p] = d.get(p)
        time.sleep(0.6)
        txt = get(EU + "efetch.fcgi?db=pubmed&rettype=abstract&retmode=xml&id=" + ",".join(chunk))
        for art in re.findall(r"<PubmedArticle>.*?</PubmedArticle>", txt, re.S):
            p = re.search(r'<PMID[^>]*>(\d+)</PMID>', art).group(1)
            body = " ".join(re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", art, re.S))
            title = " ".join(re.findall(r"<ArticleTitle>(.*?)</ArticleTitle>", art, re.S))
            abstracts[p] = re.sub(r"<[^>]+>", "", title + " " + body)
        time.sleep(0.6)
    problems = 0
    for e in entries:
        p = str(e.get("pmid") or "")
        tag = "%s %s %s" % (e["_file"], p or e.get("link"), (e.get("headline") or "")[:50])
        if not p:
            print("NO-PMID  ", tag)
            continue
        s = summ.get(p)
        if not s or "error" in s:
            print("MISSING  ", tag)
            problems += 1
            continue
        e["title"] = re.sub(r"\.$", "", s.get("title", "")).strip()
        e["journal_full"] = s.get("fulljournalname", "")
        e["doi"] = next((a["value"] for a in s.get("articleids", []) if a["idtype"] == "doi"), "")
        years = {s.get("pubdate", "")[:4], s.get("epubdate", "")[:4], s.get("sortpubdate", "")[:4]}
        if "year" in e and str(e["year"]) not in years:
            print("YEAR     ", tag, e["year"], "vs", years)
            problems += 1
        first = (s.get("authors") or [{}])[0].get("name", "")
        if e.get("author") and first and e["author"].split()[0].lower() != first.split()[0].lower():
            print("AUTHOR   ", tag, e["author"], "vs", first)
            problems += 1
        if e.get("journal") and s.get("source") and e["journal"].lower().rstrip(".") != s["source"].lower().rstrip("."):
            print("JOURNAL  ", tag, e["journal"], "vs", s["source"])
        ab = abstracts.get(p, "")
        ab = ab + " " + words_to_digits(ab)
        abn = numbers(ab) | {x.lstrip("0") for x in numbers(ab)}
        text = " ".join(str(e.get(k, "")) for k in ("description", "summary", "importance"))
        missing = sorted(x for x in numbers(text) if x not in abn and x.lstrip("0") not in abn)
        if missing:
            print("NUMBERS  ", tag, missing)
            problems += 1
        if not ab.strip():
            print("NO-ABSTR ", tag)
    if files:  # candidates: write them back enriched with title / journal_full / doi for merging
        out = Path(files[0]).with_name("enriched.json")
        out.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf-8")
    print("checked", len(entries), "entries,", problems, "flags")


if __name__ == "__main__":
    main(sys.argv[1:])
