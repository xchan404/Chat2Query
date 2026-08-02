"""LangGraph orchestrator workflow graph.

Executes DB and Document retrieval concurrently (asyncio.gather) in the hybrid path.
Handles intent routing: general | database | document | hybrid | clarification.
"""

import asyncio
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from agents.nodes.answer_generator import answer_generator_node
from agents.nodes.classifier import classifier_node
from agents.nodes.database import database_node
from agents.nodes.document import document_node
from agents.nodes.hybrid_merger import hybrid_merger_node
from agents.state import AgentState

logger = logging.getLogger(__name__)


async def run_chat_workflow(state: AgentState, session: AsyncSession) -> AgentState:
    """Execute the full agent chat workflow graph."""

    # Node 1: Classification
    classification = await classifier_node(state)
    state.update(classification)

    intent = state.get("intent", "general")

    # Fast path for clarification or general
    if intent in ("clarification", "general"):
        answer_data = await answer_generator_node(state)
        state.update(answer_data)
        return state

    # Branching based on intent
    if intent == "database":
        db_res = await database_node(state, session)
        state.update(db_res)

    elif intent == "document":
        doc_res = await document_node(state, session)
        state.update(doc_res)

    elif intent == "hybrid":
        # CONCURRENT PARALLEL EXECUTION (BUILD_PLAN Phase 6 requirement)
        # Database node and Document node run concurrently via asyncio.gather
        db_task = asyncio.create_task(database_node(state, session))
        doc_task = asyncio.create_task(document_node(state, session))

        db_res, doc_res = await asyncio.gather(db_task, doc_task)
        state.update(db_res)
        state.update(doc_res)

        # Merge results
        merger_res = hybrid_merger_node(state)
        state.update(merger_res)

    # Node 5: Answer & Citations Generator
    final_res = await answer_generator_node(state)
    state.update(final_res)

    return state
