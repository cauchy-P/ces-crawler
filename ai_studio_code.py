"""
Simple crawler for CES exhibitors search results.

It hits the same JSON endpoint the site uses:
https://exhibitors.ces.tech/8_0/ajax/remote-proxy.cfm?action=search
and writes the exhibitor section to a CSV file.
"""

import argparse
import csv
from typing import Any, Dict, List

import requests


BASE_URL = "https://exhibitors.ces.tech/8_0"
SEARCH_ENDPOINT = f"{BASE_URL}/ajax/remote-proxy.cfm"
DEFAULT_PAGE_SIZE = 200
SEARCH_HEADERS = {"X-Requested-With": "XMLHttpRequest"}
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def bootstrap_session() -> requests.Session:
    """Create a session and hydrate it with the cookies the API expects."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    # Initial GET sets CFID/CFTOKEN cookies so the search endpoint returns JSON.
    session.get(f"{BASE_URL}/", timeout=15)
    return session


def fetch_exhibitors(
    session: requests.Session,
    keyword: str,
    page_size: int = DEFAULT_PAGE_SIZE,
    searchtype: str = "keyword",
    show: str = "exhibitor",
) -> List[Dict[str, Any]]:
    """Fetch all exhibitor hits for a given keyword."""
    hits: List[Dict[str, Any]] = []
    start = 0
    total = None

    while True:
        params = {
            "action": "search",
            "search": keyword,
            "searchtype": searchtype,
            "searchsize": page_size,
            "start": start,
            "show": show,
        }
        resp = session.get(
            SEARCH_ENDPOINT,
            params=params,
            headers=SEARCH_HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        payload = resp.json()

        if not payload.get("SUCCESS"):
            raise RuntimeError(f"Search failed: {payload}")

        result = payload["DATA"]["results"][show]
        batch = result.get("hit", [])
        hits.extend(batch)

        total = result.get("found", len(hits))
        start += len(batch)
        if start >= total or not batch:
            break

    return hits


def strip_randomstring(value: str) -> str:
    """API appends 'randomstring' to booth text; remove it and trim."""
    return value.replace("randomstring", "").strip()


def hit_to_row(hit: Dict[str, Any]) -> Dict[str, str]:
    fields = hit.get("fields", {})

    booths_raw = fields.get("boothsdisplay_la") or []
    booths = "; ".join(strip_randomstring(b) for b in booths_raw if b)
    halls = "; ".join(fields.get("hallid_la") or [])
    tags = fields.get("exhtags_la") or fields.get("tags") or []

    return {
        "exhibitor_id": fields.get("exhid_l", ""),
        "name": fields.get("exhname_t", ""),
        "booths": booths,
        "hall": halls,
        "description": fields.get("exhdesc_t", ""),
        "seeking_funding": fields.get("seekfunding_t", ""),
        "funding_amount": fields.get("fundingamount_t", ""),
        "investment_stage": fields.get("investmentstage_l", ""),
        "revenue": fields.get("revenue_t", ""),
        "logo_file": fields.get("exhlogo_t", ""),
        "featured": fields.get("exhfeatured_t", ""),
        "tags": "; ".join(tags),
    }


def write_csv(rows: List[Dict[str, str]], output_path: str) -> None:
    fieldnames = [
        "exhibitor_id",
        "name",
        "booths",
        "hall",
        "description",
        "seeking_funding",
        "funding_amount",
        "investment_stage",
        "revenue",
        "logo_file",
        "featured",
        "tags",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Crawl CES exhibitor search results into a CSV file.",
    )
    parser.add_argument(
        "--keyword",
        help="Search keyword (if omitted, you will be prompted)",
    )
    parser.add_argument(
        "--output",
        help="Where to write the CSV (default: exhibitors_<keyword>.csv)",
    )
    parser.add_argument(
        "--show",
        default="exhibitor",
        help="Search section (default: exhibitor)",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help="Number of results to fetch per request (default: 200)",
    )
    args = parser.parse_args()

    keyword = (args.keyword or input("Enter search keyword: ").strip())
    if not keyword:
        raise SystemExit("Keyword is required.")

    output_path = args.output or f"exhibitors_{keyword}.csv"

    session = bootstrap_session()
    hits = fetch_exhibitors(
        session,
        keyword,
        page_size=args.page_size,
        show=args.show,
    )
    rows = [hit_to_row(hit) for hit in hits]
    write_csv(rows, output_path)
    print(f"Wrote {len(rows)} exhibitors to {output_path}")


if __name__ == "__main__":
    main()
