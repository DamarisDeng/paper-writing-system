#!/usr/bin/env python3
"""
fetch_references.py — Fetch real paper metadata from Semantic Scholar and PubMed.

All BibTeX is generated from API-returned structured metadata.
The LLM must NEVER write BibTeX entries directly — only search query strings.

Usage (CLI):
    python fetch_references.py "COVID-19 vaccine mandates healthcare workers" 10 out.bib

Usage (import):
    from fetch_references import search_semantic_scholar, semantic_scholar_to_bibtex
    from fetch_references import search_pubmed, pubmed_to_bibtex
"""

import os
import re
import sys
import time
import argparse
import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
S2_BASE = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = (
    "title,authors,year,journal,volume,pages,"
    "externalIds,publicationVenue,referenceCount,citationCount"
)
PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cite_key(author_last: str, year) -> str:
    """Build a clean cite key: FirstAuthorLastYear."""
    key = re.sub(r"[^A-Za-z0-9]", "", author_last)
    return f"{key}{year}" if year else key


def _format_authors(names: list[str], max_named: int = 6) -> str:
    """Convert ['First Last', ...] → 'Last, First and Last, First and others'."""
    parts = []
    for name in names:
        tokens = name.strip().rsplit(" ", 1)
        if len(tokens) == 2:
            parts.append(f"{tokens[1]}, {tokens[0]}")
        else:
            parts.append(name)
    out = " and ".join(parts[:max_named])
    if len(names) > max_named:
        out += " and others"
    return out


def _bibtex_entry(cite_key: str, entry_type: str, fields: dict) -> str:
    """Render a single BibTeX entry from a dict of fields."""
    lines = [f"@{entry_type}{{{cite_key},"]
    for k, v in fields.items():
        if v:
            lines.append(f"  {k:<8} = {{{v}}},")
    lines.append("}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Semantic Scholar
# ---------------------------------------------------------------------------

def search_semantic_scholar(
    query: str,
    limit: int = 5,
    api_key: str | None = None,
    retry: int = 1,
) -> list[dict]:
    """
    Search Semantic Scholar and return raw paper dicts.
    Set S2_API_KEY env var (or pass api_key) for higher rate limits.
    Without a key the API allows ~1 req/s; retry=1 with a short wait.
    """
    key = api_key or os.environ.get("S2_API_KEY")
    headers = {"x-api-key": key} if key else {}
    params = {"query": query, "limit": limit, "fields": S2_FIELDS}

    for attempt in range(retry + 1):
        resp = requests.get(
            f"{S2_BASE}/paper/search", params=params, headers=headers, timeout=15
        )
        if resp.status_code == 429:
            wait = 5 * (attempt + 1)
            print(f"  [S2] rate limited, waiting {wait}s…", file=sys.stderr)
            time.sleep(wait)
            continue
        if resp.status_code == 400:
            # query too long or malformed — skip silently
            print(f"  [S2] 400 bad request, skipping query", file=sys.stderr)
            return []
        resp.raise_for_status()
        return resp.json().get("data", [])
    print(f"  [S2] gave up after {retry} retries", file=sys.stderr)
    return []


def semantic_scholar_to_bibtex(paper: dict) -> str:
    """
    Convert a Semantic Scholar paper dict → BibTeX string.
    All field values come from the API response, never from LLM generation.
    Returns empty string if the paper lacks minimum required fields.
    """
    authors_raw = [a.get("name", "") for a in paper.get("authors", [])]
    if not authors_raw:
        return ""

    year = paper.get("year") or ""
    first_last = (authors_raw[0].strip().rsplit(" ", 1) or [""])[- 1]
    cite_key = _make_cite_key(first_last, year)

    title = paper.get("title") or ""
    if not title:
        return ""

    # Resolve journal name
    venue = paper.get("publicationVenue") or {}
    journal_obj = paper.get("journal") or {}
    journal = venue.get("name") or journal_obj.get("name") or ""

    volume = paper.get("volume") or journal_obj.get("volume") or ""
    pages  = paper.get("pages")  or journal_obj.get("pages")  or ""

    ext = paper.get("externalIds") or {}
    doi = ext.get("DOI") or ""
    pmid = ext.get("PubMed") or ""

    fields = {
        "author":  _format_authors(authors_raw),
        "title":   title,
        "journal": journal,
        "year":    str(year) if year else "",
        "volume":  str(volume) if volume else "",
        "pages":   str(pages)  if pages  else "",
        "doi":     doi,
    }
    if pmid:
        fields["note"] = f"PMID: {pmid}"

    return _bibtex_entry(cite_key, "article", fields)

# ---------------------------------------------------------------------------
# PubMed (NCBI E-utilities)
# ---------------------------------------------------------------------------

def search_pubmed(
    query: str,
    limit: int = 5,
    api_key: str | None = None,
) -> list[dict]:
    """
    Search PubMed via E-utilities and return esummary result dicts.
    Pass NCBI_API_KEY env var or api_key for higher rate limits (10 req/s vs 3).
    """
    key = api_key or os.environ.get("NCBI_API_KEY")

    # Step 1: esearch
    search_params: dict = {"db": "pubmed", "term": query, "retmax": limit, "retmode": "json"}
    if key:
        search_params["api_key"] = key

    resp = requests.get(f"{PUBMED_BASE}/esearch.fcgi", params=search_params, timeout=15)
    resp.raise_for_status()
    ids = resp.json().get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    # Step 2: esummary
    summary_params: dict = {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}
    if key:
        summary_params["api_key"] = key

    resp = requests.get(f"{PUBMED_BASE}/esummary.fcgi", params=summary_params, timeout=15)
    resp.raise_for_status()
    result = resp.json().get("result", {})
    return [result[pmid] for pmid in ids if pmid in result]


def _format_pubmed_authors(names: list[str], max_named: int = 6) -> str:
    """
    PubMed esummary returns author names as "LastName Initials" (e.g. "Petrie JG").
    Convert to BibTeX format: "LastName, Initials and LastName, Initials …"
    """
    parts = []
    for name in names:
        tokens = name.strip().rsplit(" ", 1)
        if len(tokens) == 2:
            # tokens[0] = LastName, tokens[1] = Initials
            parts.append(f"{tokens[0]}, {tokens[1]}")
        else:
            parts.append(name)
    out = " and ".join(parts[:max_named])
    if len(names) > max_named:
        out += " and others"
    return out


def pubmed_to_bibtex(paper: dict) -> str:
    """
    Convert a PubMed esummary dict → BibTeX string.
    All field values come from the API response, never from LLM generation.
    Returns empty string if the paper lacks minimum required fields.
    PubMed name format is "LastName Initials" (e.g. "Petrie JG").
    """
    authors_raw = [a.get("name", "") for a in paper.get("authors", [])]
    if not authors_raw:
        return ""

    year = (paper.get("pubdate") or "")[:4]
    # First token of the first name is the last name in PubMed format
    first_last = authors_raw[0].strip().split(" ")[0]
    cite_key = _make_cite_key(first_last, year)

    title = (paper.get("title") or "").rstrip(". ")
    if not title:
        return ""

    journal = paper.get("fulljournalname") or paper.get("source") or ""
    volume  = paper.get("volume") or ""
    issue   = paper.get("issue") or ""
    pages   = paper.get("pages") or ""

    article_ids = paper.get("articleids") or []
    doi  = next((a["value"] for a in article_ids if a.get("idtype") == "doi"),  "")
    pmid = next((a["value"] for a in article_ids if a.get("idtype") == "pubmed"), "")

    fields = {
        "author":  _format_pubmed_authors(authors_raw),
        "title":   title,
        "journal": journal,
        "year":    year,
        "volume":  volume,
        "number":  issue,
        "pages":   pages,
        "doi":     doi,
        "pmid":    pmid,
    }
    return _bibtex_entry(cite_key, "article", fields)

# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def deduplicate_bibtex(entries: list[str]) -> list[str]:
    """
    Remove duplicate entries by cite key (keep first occurrence).
    Also renames colliding keys by appending a/b/c…
    """
    seen: dict[str, int] = {}
    out = []
    for entry in entries:
        if not entry.strip():
            continue
        m = re.match(r"@\w+\{(\S+),", entry.strip())
        if not m:
            out.append(entry)
            continue
        key = m.group(1)
        if key not in seen:
            seen[key] = 0
            out.append(entry)
        else:
            seen[key] += 1
            suffix = chr(ord("a") + seen[key] - 1)
            new_key = key + suffix
            out.append(entry.replace(f"{{{key},", f"{{{new_key},", 1))
    return out

# ---------------------------------------------------------------------------
# Multi-source search
# ---------------------------------------------------------------------------

def search_and_collect(
    queries: list[str],
    per_query: int = 5,
    sources: list[str] | None = None,
) -> list[str]:
    """
    Run a list of search queries across enabled sources.
    Returns a deduplicated list of BibTeX strings.

    sources: ['s2', 'pubmed'] (default: both, S2 first)
    """
    if sources is None:
        sources = ["s2", "pubmed"]

    raw_entries: list[str] = []

    for query in queries:
        print(f"  Searching: {query!r}", file=sys.stderr)

        if "s2" in sources:
            try:
                papers = search_semantic_scholar(query, limit=per_query)
                for p in papers:
                    bib = semantic_scholar_to_bibtex(p)
                    if bib:
                        raw_entries.append(bib)
                time.sleep(1)  # be polite
            except Exception as e:
                print(f"  [S2] error: {e}", file=sys.stderr)

        if "pubmed" in sources and len(raw_entries) < per_query:
            try:
                papers = search_pubmed(query, limit=per_query)
                for p in papers:
                    bib = pubmed_to_bibtex(p)
                    if bib:
                        raw_entries.append(bib)
                time.sleep(0.4)
            except Exception as e:
                print(f"  [PubMed] error: {e}", file=sys.stderr)

    return deduplicate_bibtex(raw_entries)

# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fetch real paper metadata and write BibTeX. No LLM-generated entries."
    )
    parser.add_argument("query", help="Search query string")
    parser.add_argument("limit", type=int, nargs="?", default=10, help="Max results")
    parser.add_argument("output", nargs="?", default="-", help="Output .bib file (- for stdout)")
    parser.add_argument("--sources", default="s2,pubmed", help="Comma-separated: s2,pubmed")
    args = parser.parse_args()

    sources = [s.strip() for s in args.sources.split(",")]
    entries = search_and_collect([args.query], per_query=args.limit, sources=sources)

    bib_text = "\n\n".join(entries) + "\n"

    if args.output == "-":
        print(bib_text)
    else:
        with open(args.output, "w") as f:
            f.write(bib_text)
        print(f"  Wrote {len(entries)} entries to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
