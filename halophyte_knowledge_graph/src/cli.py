"""Command-line entry points for repeatable graph building."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .analysis import write_report
from .extraction import extract_unprocessed
from .graph_store import DEFAULT_DB, GraphStore
from .pubmed_collector import collect_pubmed


def main() -> None:
    parser = argparse.ArgumentParser(description="Halophyte evidence knowledge graph")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite graph path")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed", help="Load the clearly labelled demonstration graph")
    collect = sub.add_parser("collect", help="Collect and cache PubMed records")
    collect.add_argument("--query", required=True)
    collect.add_argument("--retmax", type=int, default=100)
    collect.add_argument("--email", required=True)
    collect.add_argument("--api-key", default=os.getenv("NCBI_API_KEY"))
    extract = sub.add_parser("extract", help="Run grounded LLM extraction for unprocessed papers")
    extract.add_argument("--limit", type=int, default=100)
    extract.add_argument("--model", default="gpt-4.1-mini")
    import_phase1 = sub.add_parser("import-phase1", help="Import existing grass dictionary CSV")
    import_phase1.add_argument("--csv", required=True)
    report = sub.add_parser("report", help="Write transparent research-opportunity report")
    report.add_argument("--output", default=None)
    args = parser.parse_args()
    store = GraphStore(args.db)
    try:
        if args.command == "seed":
            store.seed_demo()
            print(json.dumps(store.dashboard_counts(), indent=2))
        elif args.command == "collect":
            print(json.dumps({"papers_collected": collect_pubmed(args.query, args.retmax, args.email, store, args.api_key)}, indent=2))
        elif args.command == "extract":
            print(json.dumps(extract_unprocessed(store, args.limit, args.model), indent=2))
        elif args.command == "import-phase1":
            print(json.dumps(store.import_phase1_csv(args.csv), indent=2))
        elif args.command == "report":
            print(write_report(store, args.output))
    finally:
        store.close()


if __name__ == "__main__":
    main()
