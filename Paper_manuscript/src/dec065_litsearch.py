"""DEC-065 reproducible literature search (Crossref REST + arXiv API).  Queries, filters, date, hit counts and every returned record are logged; screening is rule-based and logged.
Outputs (exclusive write): IEEE39_DEC065_search_log.json, IEEE39_DEC065_search_candidates.csv.   Run:  python dec065_litsearch.py write
Limits: no IEEE Xplore / Scopus / Web of Science access; Crossref abstracts are partial; OpenAlex was not used (shared anonymous budget)."""
from __future__ import annotations

import csv
import datetime
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import dec055_common as C55

ISSN = {"TPWRS": ["0885-8950", "1558-0679"], "TSG": ["1949-3053", "1949-3061"], "TSTE": ["1949-3029", "1949-3037"], "TEC": ["0885-8969", "1558-0059"], "TPEL": ["0885-8993", "1941-0107"],
        "Automatica": ["0005-1098", "1873-2836"], "TAC": ["0018-9286", "1558-2523"], "TCST": ["1063-6536", "1558-0865"], "IJEPES": ["0142-0615", "1879-3517"], "EPSR": ["0378-7796", "1873-2046"]}
QUERIES = {
    "Q1": "distributed secondary frequency voltage control capability curve synchronous generators inverters",
    "Q2": "control barrier function frequency control power system safety",
    "Q3": "preventive dispatch post-contingency transient limits generator",
    "Q4": "frequency nadir RoCoF constrained unit commitment dispatch",
    "Q5": "projected primal-dual distributed frequency control capacity constraints transient",
    "Q6": "generator power limit violation after disturbance secondary control set-point saturation",
    "Q7": "grid-forming inverter current limit security constrained optimal power flow",
    "Q8": "transient stability constrained optimal power flow preventive control",
    "Q9": "distributed integral control input constraints power system stability invariance",
    "Q10": "dynamic security constrained rescheduling differential algebraic trajectory sensitivity",
}
ARXIV_Q = {"A1": "distributed secondary control capability limits grid-forming synchronous generators", "A2": "preventive dispatch post-contingency admissibility generator limits", "A3": "control barrier function secondary frequency control power systems"}
INCLUDE = ("distributed", "barrier", "preventive", "dispatch", "capab", "constrain", "secondary", "nadir", "rocof", "transient", "security", "projected", "invarian", "limit", "saturat", "grid-forming")
EXCLUDE = ("wind turbine blade", "battery thermal", "motor drive fault", "microgrid cyber", "electric vehicle charging scheduling", "hvac")


def get(url):
    import subprocess
    for k in range(4):                                  # python has no CA bundle here: use curl; retry transient resolution errors
        r = subprocess.run(["curl", "-sL", "-m", "40", "-A", "dec065-litsearch", url], capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout
        time.sleep(3 * (k + 1))
    raise RuntimeError(f"curl failed ({r.returncode}) for {url[:80]}")


def crossref(q, rows=25):
    flt = ",".join([f"issn:{i}" for v in ISSN.values() for i in v] + ["from-pub-date:2021-01-01", "until-pub-date:2026-12-31", "type:journal-article"])
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode({"query.bibliographic": q, "filter": flt, "rows": rows, "select": "DOI,title,container-title,issued,author,abstract,ISSN"})
    d = json.loads(get(url))["message"]
    out = []
    for it in d["items"]:
        out.append({"doi": it.get("DOI"), "title": (it.get("title") or [""])[0], "venue": (it.get("container-title") or [""])[0], "year": (it.get("issued", {}).get("date-parts") or [[None]])[0][0],
                    "first_author": (it.get("author") or [{}])[0].get("family", ""), "has_abstract": bool(it.get("abstract")), "abstract": (it.get("abstract") or "")[:600]})
    return d["total-results"], out


def arxiv(q, rows=15):
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": f"all:{q}", "start": 0, "max_results": rows, "sortBy": "relevance"})
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(get(url))
    out = []
    for e in root.findall("a:entry", ns):
        out.append({"id": e.find("a:id", ns).text, "title": " ".join(e.find("a:title", ns).text.split()), "year": int(e.find("a:published", ns).text[:4]), "abstract": " ".join(e.find("a:summary", ns).text.split())[:600]})
    return len(out), [o for o in out if o["year"] >= 2021]


def main(write=False):
    log = {"date": datetime.date.today().isoformat(), "tool": "Crossref REST /works (query.bibliographic) + arXiv API", "journal_filter": ISSN, "window": "2021-01-01..2026-12-31", "queries": {}, "arxiv": {}}
    rows = {}
    for k, q in QUERIES.items():
        n, items = crossref(q)
        log["queries"][k] = {"query": q, "total_results_in_filter": n, "returned": len(items), "dois": [i["doi"] for i in items]}
        for i in items:
            rows.setdefault(i["doi"], {**i, "queries": []})["queries"].append(k)
        time.sleep(1.0)
    for k, q in ARXIV_Q.items():
        n, items = arxiv(q)
        log["arxiv"][k] = {"query": q, "returned": n, "kept_2021_plus": len(items), "ids": [i["id"] for i in items]}
        for i in items:
            rows.setdefault(i["id"], {"doi": i["id"], "title": i["title"], "venue": "arXiv", "year": i["year"], "first_author": "", "has_abstract": True, "abstract": i["abstract"], "queries": []})["queries"].append(k)
        time.sleep(3.0)
    cand = []
    for r in rows.values():
        t = r["title"].lower()
        r["screen"] = "EXCLUDE_RULE" if any(x in t for x in EXCLUDE) else ("INCLUDE_TITLE_KEYWORD" if any(x in t for x in INCLUDE) else "EXCLUDE_NO_KEYWORD")
        cand.append(r)
    log["totals"] = {"unique_records": len(cand), "title_screen_pass": sum(r["screen"] == "INCLUDE_TITLE_KEYWORD" for r in cand)}
    print(json.dumps(log["totals"]), {k: (v["total_results_in_filter"], v["returned"]) for k, v in log["queries"].items()})
    if write:
        with open(C55.ART / "IEEE39_DEC065_search_log.json", "x", encoding="utf-8") as f:
            json.dump(log, f, indent=1)
        with open(C55.ART / "IEEE39_DEC065_search_candidates.csv", "x", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["doi_or_arxiv", "year", "venue", "first_author", "title", "queries", "title_screen", "crossref_abstract_available"])
            for r in sorted(cand, key=lambda r: (r["screen"], -(r["year"] or 0))):
                w.writerow([r["doi"], r["year"], r["venue"], r["first_author"], r["title"], ";".join(r["queries"]), r["screen"], r["has_abstract"]])
    return cand


if __name__ == "__main__":
    main("write" in sys.argv)
