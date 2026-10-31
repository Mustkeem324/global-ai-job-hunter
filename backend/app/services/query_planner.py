import re
from typing import List, Dict, Any, Set

class QueryPlanningAgent:
    """
    Phase 3: Automatic Keyword Expansion & Multi-Source Query Planning
    Expands up to 5 user seed terms into high-yield domain synonyms based on
    documented AI/LLM evaluation and software engineering taxonomies.
    """

    EXPANSION_TAXONOMY = {
        "ai trainer": [
            "ai trainer", "llm trainer", "ai response evaluator", 
            "ai data quality analyst", "model improvement specialist", "ai content evaluator"
        ],
        "llm evaluator": [
            "llm evaluator", "prompt evaluator", "rlhf specialist", 
            "model benchmarking evaluator", "ai safety evaluator", "human feedback specialist"
        ],
        "ai coding evaluator": [
            "ai coding evaluator", "coding ai trainer", "python code reviewer", 
            "llm code evaluation", "ai benchmark engineer", "coding expert for ai training"
        ],
        "full-stack ai developer": [
            "full-stack ai developer", "full stack developer", "python developer", 
            "django developer", "fastapi developer", "react next.js engineer", "ai application engineer"
        ],
        "generative ai engineer": [
            "generative ai engineer", "llm integration developer", "ai automation engineer", 
            "agentic ai developer", "prompt engineer", "ai solutions architect"
        ]
    }

    def expand_keyword(self, seed: str) -> List[str]:
        """Expand a single seed term into synonyms."""
        cleaned = seed.strip().lower()
        if cleaned in self.EXPANSION_TAXONOMY:
            return self.EXPANSION_TAXONOMY[cleaned]
        
        # Check partial match in taxonomy
        for k, expansions in self.EXPANSION_TAXONOMY.items():
            if k in cleaned or cleaned in k:
                return expansions

        # Default fallback: return seed and clean version
        return [seed]

    def create_query_plan(self, seed_terms: List[str], max_terms: int = 5) -> Dict[str, Any]:
        """
        Produce a structured query plan containing:
        - seed_terms (max 5)
        - expanded_terms (deduplicated)
        - target_adapters
        - concurrency_budget
        """
        valid_seeds = [s.strip() for s in seed_terms if s.strip()][:max_terms]
        if not valid_seeds:
            valid_seeds = [
                "AI Trainer", "LLM Evaluator", "AI Coding Evaluator", 
                "Full-Stack AI Developer", "Generative AI Engineer"
            ]

        expanded_set: Set[str] = set()
        for s in valid_seeds:
            for exp in self.expand_keyword(s):
                expanded_set.add(exp)

        return {
            "seed_terms": valid_seeds,
            "expanded_queries": sorted(list(expanded_set)),
            "total_queries": len(expanded_set),
            "priority_sources": [
                "greenhouse", "lever", "ashby", "himalayas", "jobicy", "remotive", "arbeitnow", "catalog"
            ],
            "concurrency_limit": 5,
            "cache_ttl_seconds": 3600
        }

query_planner = QueryPlanningAgent()
