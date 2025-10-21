"""
Knowledge graph integration for Helldiver.

Handles all Graphiti/Neo4j interactions:
- Episode commits (always 5 episodes per research: 3 workers + 1 critical + 1 refinement)
- Connection management
- Index building
"""
