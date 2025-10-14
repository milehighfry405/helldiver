"""
Graphiti knowledge graph integration for episodic memory storage.
"""

import os

# Try to import Graphiti, fall back to mock if unavailable
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
        if GRAPHITI_AVAILABLE:
            self.graphiti = Graphiti(
                uri=os.environ.get("NEO4J_URI", "neo4j://127.0.0.1:7687"),
                user=os.environ.get("NEO4J_USER", "neo4j"),
                password=os.environ.get("NEO4J_PASSWORD", "password")
            )
        else:
            self.graphiti = None
            print("⚠️ Graphiti client initialized in mock mode")

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
            original_query: The original research query
            tasking_context: Dictionary with tasking conversation details
            findings_narrative: The full narrative findings
            user_context: Optional user-provided context (e.g., "for AI agent memory")

        Returns:
            Dictionary with status and any errors
        """
        try:
            # Extract key information from tasking context
            refinement_turns = tasking_context.get('refinement_turns', 0)
            summary = tasking_context.get('summary', 'No specific tasking details')
            weighting = tasking_context.get('weighting', '')

            # Extract key takeaway from narrative (first sentence often works)
            key_takeaway = findings_narrative.split('.')[0] if findings_narrative else "Research completed"

            # Construct episodic narrative for Graphiti
            episode_body = f"""User researched: {original_query}

Context: {user_context if user_context else 'General research'}

Tasking details: {summary}

Key findings:
{findings_narrative}

Evolution: User conducted research, """

            # Add refinement evolution if applicable
            if refinement_turns > 0:
                episode_body += f"refined understanding through {refinement_turns} conversation turns, "

            if weighting:
                episode_body += f"with {weighting} applied to synthesis, "

            episode_body += f"and concluded that {key_takeaway}."

            # Create episode name
            episode_name = f"Research: {original_query[:50]}"

            # Add episode to Graphiti
            if self.graphiti:
                await self.graphiti.add_episode(
                    name=episode_name,
                    episode_body=episode_body,
                    group_id=GROUP_ID,
                    source="text",
                    source_description="Helldiver research mission"
                )

                return {
                    "status": "success",
                    "episode_name": episode_name,
                    "message": f"✓ Committed to Graphiti as '{episode_name}'"
                }
            else:
                # Mock mode - just log what would have been saved
                print(f"\n📝 MOCK GRAPH WRITE:")
                print(f"Episode Name: {episode_name}")
                print(f"Episode Body:\n{episode_body[:500]}...")

                return {
                    "status": "success",
                    "episode_name": episode_name,
                    "message": f"✓ [MOCK] Committed to Graphiti as '{episode_name}' (Graphiti unavailable - simulated write)"
                }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Error writing to graph: {str(e)}"
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
