"""
Unified research execution cycle.

ONE function that handles ALL research (initial, deep, doesn't matter).
The pattern is always the same:

1. User input → refinement conversation (optional)
2. Trigger research → 3 workers + critical (saves files during execution)
3. Distill refinement context
4. Save refinement files
5. Commit 5 episodes to graph (3 workers + 1 critical + 1 refinement)
6. Return to refinement state

This is the core loop. Everything else is just setup/teardown.
"""

import os
import asyncio
from datetime import datetime
from typing import Dict

from core.session import ResearchSession
from workers.research import execute_research
from utils.files import (
    format_conversation_for_display,
    convert_tasking_to_conversation,
    distill_conversation
)
from graph.client import GraphClient


async def run_research_cycle(
    session: ResearchSession,
    graph_client: GraphClient,
    query: str,
    tasking_summary: str = ""
) -> Dict:
    """
    Execute one complete research cycle.

    Args:
        session: Current research session
        graph_client: Graph connection
        query: What to research
        tasking_summary: Why we're researching this (from tasking/refinement conversation)

    Returns:
        Dict with status, episode_name, episode_count

    Process:
        1. Distill refinement context (extract gold from conversation)
        2. Execute research (3 workers → critical → synthesis)
        3. Save files (5 files: 3 workers + 1 critical + 1 refinement_distilled)
        4. Commit to graph (5 episodes: same as files)
        5. Update session state

    Why this is ONE function for all research:
    - Initial research? Just research with tasking context
    - Deep research? Just research with refinement context
    - Pattern is identical, only context source differs
    """
    print(f"\n[RESEARCH CYCLE] Starting research: {query}")

    # ========================================
    # Step 1: Create research directory
    # ========================================
    # Need to create directory BEFORE research (workers save files during execution)
    episode_name = query
    research_dir = session.next_episode_dir(episode_name)
    os.makedirs(research_dir, exist_ok=True)

    # ========================================
    # Step 2: Execute research (saves worker files + critical to research_dir)
    # ========================================
    worker_results, critical_analysis = execute_research(query, tasking_summary, research_dir)

    # ========================================
    # Step 2: Prepare refinement context
    # ========================================
    # Figure out what conversation led to this research
    # Initial research: use tasking conversation
    # Deep research: use pending_refinement (conversation since last research)

    conversation_for_distillation = []
    conversation_for_display = ""

    if session.episode_count == 0:
        # Initial research: convert tasking context
        if session.tasking_context:
            conversation_for_distillation = convert_tasking_to_conversation(session.tasking_context)
            conversation_for_display = format_conversation_for_display(conversation_for_distillation)
    else:
        # Deep research: use pending refinement
        conversation_for_distillation = session.pending_refinement
        conversation_for_display = format_conversation_for_display(session.pending_refinement)

    # Distill conversation to extract signal/gold
    print("[DISTILLING] Extracting gold from conversation...")
    refinement_distilled = distill_conversation(conversation_for_distillation)

    # ========================================
    # Step 3: Save refinement files to disk
    # ========================================
    # Worker files and critical analysis already saved during research execution
    # Just need to save refinement context files

    print(f"[REFINEMENT] Saving refinement context...")

    # Save full refinement context (audit trail)
    with open(os.path.join(research_dir, "refinement_context.txt"), 'w', encoding='utf-8') as f:
        f.write("REFINEMENT CONTEXT - Full Conversation (Audit Trail)\n")
        f.write("="*80 + "\n")
        f.write("This is the full conversation that led to this research being executed.\n")
        f.write("For the distilled version (what goes to graph), see refinement_distilled.txt\n")
        f.write("="*80 + "\n\n")
        f.write(conversation_for_display)

    # Save distilled refinement (what goes to graph as Episode 5)
    with open(os.path.join(research_dir, "refinement_distilled.txt"), 'w', encoding='utf-8') as f:
        f.write("REFINEMENT CONTEXT - Distilled (Committed to Graph)\n")
        f.write("="*80 + "\n")
        f.write("This is the extracted gold/signal from the conversation.\n")
        f.write("This version is committed to the knowledge graph as Episode 5.\n")
        f.write("WEIGHTING: This context is weighted HIGHER than raw research findings.\n")
        f.write("="*80 + "\n\n")
        f.write(refinement_distilled)

    # ========================================
    # Step 4: Commit to knowledge graph
    # ========================================
    # Group ID: Single global value for all research
    # Enables cross-session entity synthesis and "omega context" search
    group_id = "helldiver_research"

    print(f"[GRAPH] Committing to knowledge graph (group_id: {group_id})...")
    result = await graph_client.commit_research_episode(
        session_name=session.original_query,
        episode_name=episode_name,
        group_id=group_id,
        worker_results=worker_results,
        critical_analysis=critical_analysis,
        refinement_distilled=refinement_distilled
    )

    if result["status"] == "success":
        print(f"[SUCCESS] Research complete: {result['episode_count']} episodes committed")
    else:
        print(f"[WARN] Graph commit had errors: {result.get('errors', [])}")

    # ========================================
    # Step 5: Update session state
    # ========================================
    session.episode_count += 1
    session.episode_name = episode_name
    session.research_findings = worker_results
    session.query = query  # Update current query
    session.clear_refinement()  # Clear pending refinement (it's been saved)
    session.state = "REFINEMENT"  # Back to refinement state
    session.save()

    return {
        "status": result["status"],
        "episode_name": episode_name,
        "episode_count": result["episode_count"]
    }


# Note: Removed print_research_summary - no narrative generated
# User will interact with the agent that has all research loaded in context
