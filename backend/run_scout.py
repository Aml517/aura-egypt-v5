# backend/run_scout.py
"""
Run this ONCE before your demo to populate Pinecone with 50 Egyptian locations.
Usage: python run_scout.py

With SERP_KEY set: discovers real locations from the web
Without SERP_KEY:  uses curated seed data (still works for demo)
"""

import os
from dotenv import load_dotenv
load_dotenv()

from scout_agent import ScoutAgent

if __name__ == "__main__":
    print("=" * 55)
    print("  AuraEgypt Scout Agent — Building location database")
    print("=" * 55)

    scout = ScoutAgent()

    # Run with target of 50 diverse Egyptian locations
    summary = scout.run(target=50)

    print("\n" + "=" * 55)
    print(f"  Done. Results:")
    print(f"  New locations added : {summary['upserted']}")
    print(f"  Rural/community     : {summary['rural_added']}")
    print(f"  Skipped (exists)    : {summary['skipped']}")
    print(f"  Extraction errors   : {summary['errors']}")
    print("=" * 55)

    # Verify with a test query
    print("\nVerification queries:")
    tests = [
        "cosmic alien desert landscape silence",
        "romantic golden hour Nile sunset",
        "ancient mystery dark corridors history",
    ]
    for q in tests:
        results = scout.query(q, top_k=2)
        if results:
            print(f"\n  '{q}'")
            for r in results:
                marker = " [RURAL]" if r.get("is_rural") else ""
                print(f"    -> {r['name']} ({r['city']}) {r['pinecone_score']}%{marker}")
        else:
            print(f"  '{q}' -> no results (index may be empty)")