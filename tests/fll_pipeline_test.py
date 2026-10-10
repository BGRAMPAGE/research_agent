"""Full-pipeline smoke test for the adaptive refinement loop — Step 3 verification.
Run with: python test_graph.py
"""

import asyncio
import logging

from src.graph import run_research

logging.basicConfig(level=logging.INFO)


async def main():
    topic = "Comparison of vector database indexing algorithms (HNSW vs IVF)"
    result = await run_research(topic, verbose=True, use_cache=False, use_checkpoints=False)

    print("\n" + "=" * 60)
    print("FULL PIPELINE RESULT")
    print("=" * 60)
    print(f"refinement_count: {result.get('refinement_count')}")
    print(f"synthesis_confidence: {result.get('synthesis_confidence')}")
    print(f"research_gaps (final): {result.get('research_gaps')}")
    print(f"total search_results: {len(result.get('search_results', []))}")
    print(f"total key_findings: {len(result.get('key_findings', []))}")
    print(f"llm_calls: {result.get('llm_calls')}")
    print(f"error: {result.get('error')}")
    print(f"final_report length: {len(result.get('final_report') or '')}")


if __name__ == "__main__":
    asyncio.run(main())