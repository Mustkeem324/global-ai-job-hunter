#!/usr/bin/env python3
"""
Verify and filter global AI job openings database.
Author: Mustkeem Ahmad
"""

import json
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "opportunities.json")

def load_opportunities():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        sys.exit(1)
    with open(DB_PATH, "r") as f:
        return json.load(f)

def display_summary(opportunities):
    print(f"\n=======================================================")
    print(f"  GLOBAL AI JOB HUNTER — DATABASE VERIFICATION SUMMARY")
    print(f"=======================================================")
    print(f"Total Tracked Opportunities: {len(opportunities)}")
    
    categories = {}
    for op in opportunities:
        cat = op.get("category", "General")
        categories[cat] = categories.get(cat, 0) + 1
        
    print("\n[Opportunities by Category]:")
    for cat, count in categories.items():
        print(f"  • {cat:<25}: {count} openings")
        
    print("\n[Top Match Opportunities (>= 90/100)]:")
    top_matches = [op for op in opportunities if op.get("match_score", 0) >= 90]
    for op in sorted(top_matches, key=lambda x: x["match_score"], reverse=True):
        print(f"  [{op['match_score']}/100] {op['company']:<20} | {op['title']:<45} | {op['compensation']}")

def main():
    opportunities = load_opportunities()
    display_summary(opportunities)

if __name__ == "__main__":
    main()
