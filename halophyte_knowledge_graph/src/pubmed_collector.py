"""Small NCBI E-utilities client using only the Python standard library."""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from .graph_store import GraphStore, ROOT

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _get(endpoint: str, params: dict[str, str]) -> bytes:
    url = f"{BASE}/{endpoint}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "HalophyteKnowledgeGraph/1.0 (academic project)"})
    with urllib.request.urlopen(request, timeout=45) as response:  # nosec B310 - fixed official NCBI endpoint
        return response.read()


def collect_pubmed(query: str, retmax: int, email: str, store: GraphStore, api_key: str | None = None) -> int:
    if not email or "@" not in email:
        raise ValueError("A contact email is required by NCBI E-utilities policy.")
    common = {"db": "pubmed", "term": query, "retmax": str(retmax), "retmode": "json", "email": email}
    if api_key:
        common["api_key"] = api_key
    search = json.loads(_get("esearch.fcgi", common))
    ids = search["esearchresult"].get("idlist", [])
    if not ids:
        return 0
    raw_dir = ROOT / "data" / "raw_pubmed"
    raw_dir.mkdir(exist_ok=True)
    added = 0
    for start in range(0, len(ids), 50):
        batch = ids[start:start + 50]
        params = {"db": "pubmed", "id": ",".join(batch), "retmode": "xml", "email": email}
        if api_key:
            params["api_key"] = api_key
        xml = _get("efetch.fcgi", params)
        (raw_dir / f"pubmed_{batch[0]}_{batch[-1]}.xml").write_bytes(xml)
        for paper in parse_pubmed_xml(xml):
            store.upsert_paper(paper)
            added += 1
        time.sleep(0.34 if not api_key else 0.12)
    return added


def _text(element: ET.Element | None) -> str:
    return "" if element is None else " ".join(element.itertext()).strip()


def parse_pubmed_xml(xml: bytes) -> list[dict[str, str | int | None]]:
    root = ET.fromstring(xml)
    records = []
    for article in root.findall(".//PubmedArticle"):
        medline = article.find("MedlineCitation")
        article_data = medline.find("Article") if medline is not None else None
        pmid = _text(medline.find("PMID") if medline is not None else None)
        title = _text(article_data.find("ArticleTitle") if article_data is not None else None)
        abstract = " ".join(_text(x) for x in (article_data.findall("Abstract/AbstractText") if article_data is not None else []))
        journal = _text(article_data.find("Journal/Title") if article_data is not None else None)
        year_text = _text(article_data.find("Journal/JournalIssue/PubDate/Year") if article_data is not None else None)
        authors = "; ".join(
            " ".join(filter(None, [_text(a.find("ForeName")), _text(a.find("LastName"))]))
            for a in (article_data.findall("AuthorList/Author") if article_data is not None else [])
        )
        doi = next((_text(x) for x in article.findall(".//ArticleId") if x.attrib.get("IdType") == "doi"), None)
        if pmid and title:
            records.append({"external_id": f"PMID:{pmid}", "title": title, "abstract": abstract, "authors": authors,
                            "year": int(year_text) if year_text.isdigit() else None, "journal": journal, "doi": doi,
                            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"})
    return records
