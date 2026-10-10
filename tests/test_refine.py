"""Standalone smoke test for ResearchPlanner.refine_plan() — Step 2 verification.
Run with: python test_refine.py
"""

import asyncio
import logging

from src.state import ResearchState, ResearchPlan, SearchQuery
from src.agents import ResearchPlanner

logging.basicConfig(level=logging.INFO)


async def main():
    # Fake a plan as if the FIRST pass already ran and completed.
    fake_plan = ResearchPlan(
    topic="OpenAI's internal safety testing process",
    objectives=["Describe publicly known safety testing practices"],
    search_queries=[
        SearchQuery(query="OpenAI safety testing red teaming", purpose="baseline", completed=True),
    ],
    report_outline=["Overview", "Process", "Conclusion"],
)
    fake_findings = [
    "OpenAI publishes system cards describing external red-teaming before major model releases [1]",
]
    fake_gaps = [
    "No source specifies the exact internal headcount of OpenAI's safety team as of this month",  # not publicly searchable
    "No source clarifies whether OpenAI's next unreleased model will change this process",  # unknowable/future
]
    state = ResearchState(
        research_topic=fake_plan.topic,
        plan=fake_plan,
        key_findings=fake_findings,
        research_gaps=fake_gaps,
        synthesis_confidence="medium",
        refinement_count=0,
    )

    planner = ResearchPlanner()
    result = await planner.refine_plan(state)

    print("\n" + "=" * 60)
    print("REFINE_PLAN RESULT")
    print("=" * 60)
    for key, value in result.items():
        print(f"\n[{key}]")
        print(value)
    print("=" * 60)

    # Basic pass/fail checks
    assert "current_stage" in result, "Missing current_stage in result"
    if result.get("plan"):
        new_queries = result["plan"].search_queries
        print(f"\n✅ Got {len(new_queries)} follow-up queries:")
        for q in new_queries:
            print(f"   - query: {q.query}")
            print(f"     purpose: {q.purpose}")
        assert len(new_queries) <= 2, "Should generate at most 2 follow-up queries"
        assert result["current_stage"] == "searching", "Should route to searching when queries exist"
    else:
        print(f"\n⚠️  No new plan returned — current_stage = {result.get('current_stage')}")
        print("   (This is OK if the model decided no gap was specific enough to search for.)")


if __name__ == "__main__":
    asyncio.run(main())