"""
Research session state management.

A session tracks one continuous research conversation from start to finish.
Each session can have multiple research episodes (initial + N deep dives).

Session lifecycle:
    TASKING → RESEARCH → REFINEMENT → (RESEARCH → REFINEMENT)* → COMPLETE
"""

import json
import os
from datetime import datetime
from typing import Optional, List, Dict


class ResearchSession:
    """
    Represents a single research conversation session.

    Key concepts:
    - Session: The entire conversation (1 initial research + N deep researches)
    - Episode: One research execution (creates 5 graph episodes: 3 workers + 1 critical + 1 refinement)
    - Refinement: Conversation between research executions

    Why this matters:
    - Separates "what we're researching" (query) from "conversation context" (refinement)
    - Tracks state to know what to do next
    - Provides continuity across multiple research cycles
    """

    def __init__(
        self,
        session_dir: str,
        query: str,
        state: str = "TASKING"
    ):
        # Core identification
        self.session_dir = session_dir  # Where all files live
        self.query = query  # Current research focus
        self.original_query = query  # Never changes - what user originally asked

        # State machine (where we are in the lifecycle)
        self.state = state  # TASKING | RESEARCH | REFINEMENT | COMPLETE

        # Episode tracking (what we've researched so far)
        self.episode_count = 0  # Total research episodes executed
        self.episode_name = ""  # Clean name for current episode (e.g., "Custom entities for Graphiti")

        # Conversation context (the refinement between researches)
        self.tasking_context = {}  # Initial conversation that defined the research
        self.pending_refinement = []  # Conversation since last research

        # Research outputs (what we found)
        self.narrative = ""  # Synthesized findings from last research
        self.research_findings = {}  # Raw worker outputs from last research

    def save(self):
        """
        Persist session state to disk.

        Why: Sessions can be resumed across restarts, continuity matters.
        Where: session_dir/session.json
        """
        session_file = os.path.join(self.session_dir, "session.json")

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump({
                "query": self.query,
                "original_query": self.original_query,
                "state": self.state,
                "episode_count": self.episode_count,
                "episode_name": self.episode_name,
                "tasking_context": self.tasking_context,
                "pending_refinement": self.pending_refinement,
                "created_at": datetime.now().isoformat()
            }, f, indent=2)

    @staticmethod
    def load(session_dir: str) -> 'ResearchSession':
        """
        Load existing session from disk.

        Args:
            session_dir: Path to session directory

        Returns:
            ResearchSession instance

        Raises:
            FileNotFoundError: If session.json doesn't exist
        """
        session_file = os.path.join(session_dir, "session.json")

        if not os.path.exists(session_file):
            raise FileNotFoundError(f"No session.json in {session_dir}")

        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Create session with loaded data
        session = ResearchSession(
            session_dir=session_dir,
            query=data.get("query", ""),
            state=data.get("state", "TASKING")
        )

        # Restore state
        session.original_query = data.get("original_query", data.get("query", ""))
        session.episode_count = data.get("episode_count", 0)
        session.episode_name = data.get("episode_name", "")
        session.tasking_context = data.get("tasking_context", {})
        session.pending_refinement = data.get("pending_refinement", [])

        return session

    def add_refinement_turn(self, user_input: str, assistant_response: str):
        """
        Record one turn of refinement conversation.

        Why: This context gets distilled and committed to graph as Episode 5.
        The refinement explains WHY we're doing the next research.

        Args:
            user_input: What the user said
            assistant_response: How we responded
        """
        self.pending_refinement.append({
            "user_input": user_input,
            "assistant_response": assistant_response,
            "timestamp": datetime.now().isoformat()
        })

    def clear_refinement(self):
        """
        Clear pending refinement after it's been saved to research folder.

        Why: Refinement is per-research, not cumulative.
        When: Called after each research execution.
        """
        self.pending_refinement = []

    def next_episode_dir(self, topic: str) -> str:
        """
        Generate directory path for next research episode.

        Args:
            topic: Clean topic name (e.g., "Custom entities for Graphiti")

        Returns:
            Path like: session_dir/Custom_entities_for_Graphiti/

        Why: Each research gets its own folder with 5 files (3 workers + 1 critical + 1 refinement)
        """
        # Use EXACT same logic as old code - just replace spaces and slashes
        safe_name = topic.replace(" ", "_").replace("/", "_")
        return os.path.join(self.session_dir, safe_name)
