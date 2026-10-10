"""Paper Library (RAG) chat mode for the Chainlit app."""

import asyncio
import logging
import re

import chainlit as cl
from langchain_core.messages import SystemMessage, HumanMessage

from src.config import config
from src.agents import get_llm
from src.utils.paper_db import get_paper_retriever, get_context_builder, format_authors

logger = logging.getLogger(__name__)

RESEARCH_PROFILE = "Deep Research"
RAG_PROFILE = "Paper Library"

# Below this best-match similarity the corpus probably doesn't cover the question.
# BGE-m3 cosine scores for on-topic matches are typically well above this; tune on your data.
LOW_RELEVANCE_THRESHOLD = 0.45

RAG_SYSTEM_PROMPT = """You answer questions about AI/ML research papers using ONLY the provided context excerpts.

Rules:
- Ground every claim in the excerpts and cite with [SOURCE N] matching the excerpt numbers.
- If the excerpts do not contain the answer, say so plainly. Never use outside knowledge.
- Be concise and specific: include mechanisms, numbers, and names when the excerpts have them.
- If excerpts are partial or disagree, say so instead of smoothing it over."""


async def rag_welcome_message():
    await cl.Message(
        content=(
            "# Paper Library\n\n"
            "Ask questions about the curated corpus of AI/ML arXiv papers. "
            "Answers come **only** from retrieved paper excerpts, with numbered citations.\n\n"
            "Try: *What is the main idea behind self-consistency in chain-of-thought reasoning?*\n\n"
            "For broader web-based reports, switch to the **Deep Research** profile."
        )
    ).send()


async def answer_from_papers(question: str):
    retriever = get_paper_retriever()
    if retriever is None:
        await cl.Message(
            content="The paper library is currently unavailable (database disabled or unreachable). "
                    "The **Deep Research** profile still works."
        ).send()
        return

    async with cl.Step(name="Searching paper library") as step:
        results = await asyncio.to_thread(retriever.search, question, config.rag_top_k)
        step.output = f"Retrieved {len(results)} excerpts"

    if not results:
        await cl.Message(content="No excerpts were retrieved for that question.").send()
        return

    best = max(r["similarity"] for r in results)
    context = get_context_builder().build(results)

    async with cl.Step(name="Writing answer") as step:
        llm = get_llm(temperature=0.2)
        response = await llm.ainvoke([
            SystemMessage(content=RAG_SYSTEM_PROMPT),
            HumanMessage(content=f"Question: {question}\n\nContext:\n{context}"),
        ])
        # Some local models (e.g. qwen3) emit <think> blocks; strip them
        answer = re.sub(r"<think>.*?</think>", "", str(response.content), flags=re.DOTALL).strip()
        step.output = "Done"

    note = ""
    if best < LOW_RELEVANCE_THRESHOLD:
        note = ("> **Low relevance:** the closest excerpt scored "
                f"{best:.2f}. This corpus may not cover your question; treat the answer with caution.\n\n")

    sources = "\n".join(
        f"**[SOURCE {i}]** {r['title']} — {format_authors(r['authors'])} "
        f"(similarity {r['similarity']:.2f}) "
        + (f"[link]({r['source_url']})" if r.get("source_url") else "")
        for i, r in enumerate(results, 1)
    )

    await cl.Message(content=f"{note}{answer}\n\n---\n**Sources**\n\n{sources}").send()