"""
Graphiti knowledge graph client.

Handles all Neo4j/Graphiti interactions with proper connection management.

Key responsibilities:
- Commit research episodes (always 5 per research: 3 workers + 1 critical + 1 refinement)
- Maintain connection health (reconnect if dead)
- Build indexes automatically

Why 5 episodes per research:
- Episodes 1-3: Worker findings (academic, industry, tool)
- Episode 4: Critical analysis
- Episode 5: Refinement context (THE GOLD - captures user's strategic framing and WHY)
"""

import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Try to import Graphiti, gracefully handle if unavailable
try:
    from graphiti_core import Graphiti
    GRAPHITI_AVAILABLE = True
except ImportError:
    GRAPHITI_AVAILABLE = False
    Graphiti = None

# Import ontology configuration for custom entity/edge extraction
from .ontology import ENTITY_TYPES, EDGE_TYPES, EDGE_TYPE_MAP


async def retry_with_backoff(func, max_retries=3, initial_delay=60):
    """
    Retry an async function with exponential backoff on rate limit errors.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 60s = 1 minute)

    Returns:
        Result from the function if successful

    Raises:
        Last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            last_exception = e
            error_msg = str(e).lower()

            # Check if it's a rate limit error
            if "rate limit" in error_msg or "429" in error_msg:
                if attempt < max_retries:
                    print(f"  [RETRY] Rate limit hit, waiting {delay}s before retry {attempt + 1}/{max_retries}...")
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff: 60s, 120s, 240s
                else:
                    print(f"  [FAILED] Max retries reached after {max_retries} attempts")
                    raise last_exception
            else:
                # Not a rate limit error, don't retry
                raise e

    raise last_exception


class GraphClient:
    """
    Clean interface to Graphiti knowledge graph.

    Handles connection lifecycle, automatic reconnection, and episode commits.
    """

    def __init__(self):
        """Initialize connection to Neo4j via Graphiti."""
        self._uri = os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7687")
        self._user = os.environ.get("NEO4J_USER", "neo4j")
        self._password = os.environ.get("NEO4J_PASSWORD", "password")
        self._indexes_built = False  # Track if indexes are created

        if not GRAPHITI_AVAILABLE:
            print("[WARN] Graphiti not available - running in mock mode")
            self.graphiti = None
            return

        try:
            # Use default OpenAI client
            # Rate limiting controlled by SEMAPHORE_LIMIT environment variable
            self.graphiti = Graphiti(
                uri=self._uri,
                user=self._user,
                password=self._password
            )
            print("[OK] Connected to Neo4j with OpenAI")
        except Exception as e:
            print(f"[ERROR] Failed to connect to Neo4j: {e}")
            print("[WARN] Falling back to mock mode")
            self.graphiti = None

    def _ensure_connection(self) -> bool:
        """
        Verify connection is alive, reconnect if dead.

        Returns:
            True if connection is healthy, False if unavailable

        Why this matters:
        - Connections can time out during long refinement conversations
        - Need to detect dead connections and recreate them
        - Can't just check if driver exists - need to verify_connectivity()
        """
        if not self.graphiti:
            return False

        try:
            # Check if driver exists
            if not hasattr(self.graphiti, 'driver') or self.graphiti.driver is None:
                print("[INFO] Driver missing, reconnecting...")
                self._reconnect()
                return True

            # Verify connection is actually alive
            try:
                self.graphiti.driver.verify_connectivity()
                return True
            except Exception:
                # Connection dead, recreate
                print("[INFO] Connection lost, reconnecting...")
                self._reconnect()
                return True

        except Exception as e:
            print(f"[ERROR] Connection verification failed: {e}")
            return False

    def _reconnect(self):
        """
        Recreate Graphiti connection.

        Why: Old connection is dead, need fresh one.
        Side effect: Resets _indexes_built flag so indexes get rebuilt.
        """
        try:
            # Close old connection (if exists)
            # Note: graphiti.close() is async, but we're recreating anyway
            # so we just let the old connection get garbage collected

            # Create new connection with default OpenAI client
            self.graphiti = Graphiti(
                uri=self._uri,
                user=self._user,
                password=self._password
            )
            self._indexes_built = False  # Rebuild indexes on new connection
            print("[OK] Reconnected to Neo4j with OpenAI")

        except Exception as e:
            print(f"[ERROR] Reconnection failed: {e}")
            self.graphiti = None

    async def commit_research_episode(
        self,
        session_name: str,
        episode_name: str,
        group_id: str,
        worker_results: Dict[str, str],
        critical_analysis: str,
        refinement_distilled: str
    ) -> Dict:
        """
        Commit one research episode to graph (5 graph episodes total).

        Args:
            session_name: Session identifier (e.g., "Brain memory for LLMs")
            episode_name: Episode identifier (e.g., "Custom entities for Graphiti")
            group_id: Group ID for filtering (e.g., "helldiver_research_Session_initial")
            worker_results: Dict with academic_researcher, industry_intelligence, tool_analyzer
            critical_analysis: Critical analyst output
            refinement_distilled: Distilled conversation context

        Returns:
            Dict with status, episode_count, errors

        Commits:
            1. Episode 1: Academic Research
            2. Episode 2: Industry Intelligence
            3. Episode 3: Tool Analysis
            4. Episode 4: Critical Analysis
            5. Episode 5: Refinement Context (THE GOLD - user's strategic framing)

        Why 5 episodes:
        - Graphiti extracts richer entities from 1,400-2,600 token chunks
        - One episode per worker gives optimal extraction
        - Refinement context explains WHY (more important than WHAT)
        """
        if not self._ensure_connection():
            return {
                "status": "error",
                "error": "Neo4j unavailable",
                "episode_count": 0
            }

        # Build indexes on first write (idempotent, safe to call multiple times)
        if not self._indexes_built:
            print("[INFO] Building Neo4j indexes...")
            await self.graphiti.build_indices_and_constraints()
            self._indexes_built = True
            print("[OK] Indexes verified")

        timestamp = datetime.now(timezone.utc)
        episodes_committed = []
        errors = []

        # Episodes 1-3: Worker findings
        worker_names = {
            "academic_researcher": "Academic Research",
            "industry_intelligence": "Industry Intelligence",
            "tool_analyzer": "Tool Analysis"
        }

        for worker_key, worker_label in worker_names.items():
            content = worker_results.get(worker_key, "")
            if not content:
                continue

            ep_name = f"{episode_name} - {worker_label}"

            # Generate structured source_description with metadata
            source_desc = f"""[METADATA]
Research Session: {session_name}
Episode: {episode_name}
Worker: {worker_label}
Group ID: {group_id}
Timestamp: {timestamp.isoformat()}

[CONTEXT]
This episode contains {worker_label.lower()} findings for the research question: "{episode_name}".
Part of the {session_name} research session using Helldiver's multi-agent research system."""

            print(f"  [PROCESSING] {worker_label}... (extracting entities)")
            try:
                # Wrap in retry logic for rate limit handling
                await retry_with_backoff(lambda: self.graphiti.add_episode(
                    name=ep_name,
                    episode_body=content,
                    entity_types=ENTITY_TYPES,
                    edge_types=EDGE_TYPES,
                    edge_type_map=EDGE_TYPE_MAP,
                    source_description=source_desc,
                    reference_time=timestamp,
                    group_id=group_id
                ))
                episodes_committed.append(ep_name)
                print(f"[EPISODE] ✓ {ep_name}")

            except Exception as e:
                error_msg = f"Failed to commit {ep_name}: {str(e)}"
                errors.append(error_msg)
                print(f"[ERROR] {error_msg}")

        # Episode 4: Critical Analysis
        if critical_analysis:
            ep_name = f"{episode_name} - Critical Analysis"

            source_desc = f"""[METADATA]
Research Session: {session_name}
Episode: {episode_name}
Worker: Critical Analysis
Group ID: {group_id}
Timestamp: {timestamp.isoformat()}

[CONTEXT]
This episode contains critical analysis synthesizing findings from academic research, industry intelligence, and tool analysis.
Reviews evidence quality, identifies contradictions, filters noise, and highlights key insights."""

            print(f"  [PROCESSING] Critical Analysis... (extracting entities)")
            try:
                # Wrap in retry logic for rate limit handling
                await retry_with_backoff(lambda: self.graphiti.add_episode(
                    name=ep_name,
                    episode_body=critical_analysis,
                    entity_types=ENTITY_TYPES,
                    edge_types=EDGE_TYPES,
                    edge_type_map=EDGE_TYPE_MAP,
                    source_description=source_desc,
                    reference_time=timestamp,
                    group_id=group_id
                ))
                episodes_committed.append(ep_name)
                print(f"[EPISODE] ✓ {ep_name}")

            except Exception as e:
                error_msg = f"Failed to commit {ep_name}: {str(e)}"
                errors.append(error_msg)
                print(f"[ERROR] {error_msg}")

        # Episode 5: Refinement Context (THE GOLD - user's strategic framing)
        if refinement_distilled:
            ep_name = f"{episode_name} - Refinement Context"

            source_desc = f"""[METADATA]
Research Session: {session_name}
Episode: {episode_name}
Type: Refinement Context (THE GOLD)
Group ID: {group_id}
Timestamp: {timestamp.isoformat()}

[CONTEXT]
This episode captures the user's mental models, reframings, constraints, priorities, and synthesis instructions
that led to this research being executed. This is the WHY behind the research - the user's strategic framing
and execution guidance.

Contains: Mental models, strategic reframings, hard constraints, priority hierarchies, synthesis rules."""

            # Build episode body
            context_body = f"""Research Query: {episode_name}
Episode Type: Refinement Context

DISTILLED CONTEXT (The "Why" Behind This Research):
{refinement_distilled}

This episode captures the user's mental models, key questions, and strategic framing
that led to this research being executed."""

            print(f"  [PROCESSING] Refinement Context (THE GOLD)... (extracting entities)")
            try:
                # Wrap in retry logic for rate limit handling
                await retry_with_backoff(lambda: self.graphiti.add_episode(
                    name=ep_name,
                    episode_body=context_body,
                    entity_types=ENTITY_TYPES,
                    edge_types=EDGE_TYPES,
                    edge_type_map=EDGE_TYPE_MAP,
                    source_description=source_desc,
                    reference_time=timestamp,
                    group_id=group_id
                ))
                episodes_committed.append(ep_name)
                print(f"[EPISODE] ✓ {ep_name} (THE GOLD)")

            except Exception as e:
                error_msg = f"Failed to commit {ep_name}: {str(e)}"
                errors.append(error_msg)
                print(f"[ERROR] {error_msg}")

        return {
            "status": "success" if episodes_committed else "error",
            "episode_count": len(episodes_committed),
            "episodes": episodes_committed,
            "errors": errors
        }

    def close(self):
        """
        Close Graphiti connection gracefully.

        Note: Graphiti.close() is async and can't be called from sync context.
        Connection cleanup happens automatically on process exit.
        """
        # graphiti.close() is async - can't call from sync method
        # Connection gets cleaned up on process exit
        pass
