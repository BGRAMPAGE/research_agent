"""Smoke test for the local paper database tool.
Run with: python test_paper_db.py  (requires the Postgres+pgvector container running)
"""
import asyncio
from src.utils.tools import search_paper_database

async def main():
    result = await search_paper_database.ainvoke({"query": "what is chain of thought prompting", "top_k": 3})
    for r in result:
        print(f"- {r['title']}")
        print(f"  url: {r['url']}")
        print(f"  snippet: {r['snippet'][:150]}...")
        print()

if __name__ == "__main__":
    asyncio.run(main())