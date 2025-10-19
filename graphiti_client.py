"""
Graphiti knowledge graph integration for episodic memory storage.
"""

import os

# Check for force mock mode (for testing)
FORCE_MOCK_MODE = os.environ.get("GRAPHITI_MOCK_MODE", "").lower() in ["true", "1", "yes"]

# Try to import Graphiti, fall back to mock if unavailable
if FORCE_MOCK_MODE:
    print("WARNING: FORCE_MOCK_MODE enabled - all graph writes will be simulated")
    GRAPHITI_AVAILABLE = False
    Graphiti = None
else:
    try:
        from graphiti_core import Graphiti
        GRAPHITI_AVAILABLE = True
    except Exception as e:
        print(f"Warning: Graphiti import failed: {e}")
        print("Using mock Graphiti client. Graph writes will be simulated.")
        GRAPHITI_AVAILABLE = False
        Graphiti = None


# Group ID for all Helldiver research sessions
GROUP_ID = "helldiver_research"


class GraphitiClient:
    """Client for interacting with Graphiti knowledge graph"""

    def __init__(self):
        """Initialize Graphiti connection"""
        if GRAPHITI_AVAILABLE and not FORCE_MOCK_MODE:
            try:
                self.graphiti = Graphiti(
                    uri=os.environ.get("NEO4J_URI", "bolt://127.0.0.1:7687"),
                    user=os.environ.get("NEO4J_USER", "neo4j"),
                    password=os.environ.get("NEO4J_PASSWORD", "password")
                )
                print("SUCCESS: Graphiti client connected to Neo4j")
            except Exception as e:
                print(f"WARNING: Failed to connect to Neo4j: {e}")
                print("WARNING: Falling back to mock mode")
                self.graphiti = None
        else:
            self.graphiti = None
            print("WARNING: Graphiti client initialized in mock mode")

    async def commit_episode(
        self,
        agent_id: str,
        original_query: str,
        tasking_context: dict,
        findings_narrative: str,
        user_context: str = ""
    ) -> dict:
        """
        Write a research episode to the knowledge graph.

        Args:
            agent_id: ID of the agent that conducted research
            original_query: The episode name (e.g., "Session Name - Worker Role")
            tasking_context: Dictionary with metadata (type, worker, session, group_id, etc.)
            findings_narrative: The full episode body
            user_context: Source description for linking episodes

        Returns:
            Dictionary with status and any errors
        """
        try:
            # Extract metadata from tasking_context
            research_type = tasking_context.get('type', 'unknown')
            worker_name = tasking_context.get('worker', 'Unknown Worker')
            session_name = tasking_context.get('session', 'Unknown Session')
            group_id = tasking_context.get('group_id', GROUP_ID)
            source_description = tasking_context.get('source_description', 'Helldiver research')
            parent_episode = tasking_context.get('parent_episode', 'root')

            # Episode name comes from original_query (already formatted as "Session - Worker")
            episode_name = original_query

            # Add episode to Graphiti
            if self.graphiti:
                try:
                    from datetime import datetime, timezone

                    await self.graphiti.add_episode(
                        name=episode_name,
                        episode_body=findings_narrative,
                        source_description=source_description,
                        reference_time=datetime.now(timezone.utc),
                        group_id=group_id
                    )

                    return {
                        "status": "success",
                        "episode_name": episode_name,
                        "message": f"✓ Committed to Graphiti as '{episode_name}'"
                    }
                except Exception as graph_error:
                    # Graph write failed - show detailed error
                    error_msg = str(graph_error)
                    print(f"\n[X] GRAPH WRITE ERROR:")
                    print(f"Error: {error_msg}")
                    print(f"Episode: {episode_name}")
                    return {
                        "status": "error",
                        "error": error_msg,
                        "message": f"Error writing to graph: {error_msg}"
                    }
            else:
                # Mock mode - show detailed simulated write
                print(f"\n[MOCK] GRAPH WRITE:")
                print(f"{'='*80}")
                print(f"Episode Name: {episode_name}")
                print(f"Research Type: {research_type}")
                print(f"Worker: {worker_name}")
                print(f"Session: {session_name}")
                print(f"Group ID: {group_id}")
                print(f"Parent Episode: {parent_episode}")
                print(f"Source Description: {source_description}")
                print(f"{'='*80}")
                print(f"Episode Body (first 500 chars):")
                print(findings_narrative[:500])
                print("...")
                print(f"{'='*80}\n")

                return {
                    "status": "success",
                    "episode_name": episode_name,
                    "message": f"[MOCK] Committed to Graphiti as '{episode_name}'"
                }

        except Exception as e:
            # Unexpected error in commit_episode function itself
            error_msg = str(e)
            print(f"\n[ERROR] UNEXPECTED ERROR IN commit_episode:")
            print(f"Error: {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": error_msg,
                "message": f"Error in commit function: {error_msg}"
            }

    async def search_episodes(self, query: str, limit: int = 5) -> list:
        """
        Search for relevant episodes in the knowledge graph.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of relevant episodes
        """
        try:
            results = await self.graphiti.search(
                query=query,
                group_id=GROUP_ID,
                limit=limit
            )
            return results

        except Exception as e:
            return [{"error": str(e)}]

    def close(self):
        """Close Graphiti connection"""
        if hasattr(self.graphiti, 'close'):
            self.graphiti.close()
