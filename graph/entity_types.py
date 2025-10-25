"""
Entity type definitions for Helldiver's Graphiti knowledge graph.

These custom entities enable richer extraction and querying of research outputs,
strategic context, and execution learnings.

See: zz_personal folder/schema.md for design rationale
"""

from pydantic import BaseModel


# ============================================================================
# Meta-Entities (Core Workflow)
# ============================================================================

class ResearchFinding(BaseModel):
    """Insight discovered through research."""
    topic: str  # What this finding is about
    finding_type: str  # strategic_insight | competitive_analysis | best_practice | limitation | workflow_guide | technical_spec | configuration_spec | prompt_template | integration_pattern | troubleshooting_guide | data_schema
    content_summary: str  # The actual finding (1-5 sentences)
    source_type: str  # academic | industry | tool_docs | critical_analysis
    confidence: str  # high | medium | low
    session_name: str  # Which research session produced this


class StrategicIntent(BaseModel):
    """User's strategic context and reasoning."""
    goal: str  # What we're trying to achieve
    related_topics: list[str]  # Topics this connects to
    priority: str  # critical | important | backlog
    rationale: str  # WHY this matters (2-5 sentences)
    key_decisions: str | None  # Specific decisions made


class ExecutionOutcome(BaseModel):
    """Results and learnings from execution."""
    task_description: str  # What was done
    approach_used: str  # How it was done
    what_worked: str  # Successful aspects
    what_failed: str  # What didn't work
    insights_gained: str  # Meta-learnings
    would_repeat: bool  # Would you do this again?
    related_topics: list[str]  # Links back to research/strategy


# ============================================================================
# Domain Entities (GTM Project)
# ============================================================================

class Company(BaseModel):
    """Company entity."""
    company_name: str  # Company name (avoid 'name' - protected field)
    stage: str | None  # Seed | Series A | Series B | Series C | Series D+ | Public
    industry: str | None  # Market/vertical
    description: str  # Brief summary (1-2 sentences)


class Tool(BaseModel):
    """Software tool or platform."""
    tool_name: str  # Tool name (avoid 'name' - protected field)
    category: str | None  # data_enrichment | CRM | automation | API
    description: str  # What it does (2-3 sentences)


class Methodology(BaseModel):
    """Process or workflow."""
    methodology_name: str  # Process name (avoid 'name' - protected field)
    step_count: int | None  # Number of steps
    description: str  # What this methodology does


# ============================================================================
# Entity Types Dictionary
# ============================================================================

ENTITY_TYPES = {
    "ResearchFinding": ResearchFinding,
    "StrategicIntent": StrategicIntent,
    "ExecutionOutcome": ExecutionOutcome,
    "Company": Company,
    "Tool": Tool,
    "Methodology": Methodology,
}

# Entity types for research episodes (4 workers + refinement)
RESEARCH_ENTITY_TYPES = {
    "ResearchFinding": ResearchFinding,
    "Company": Company,
    "Tool": Tool,
    "Methodology": Methodology,
}
