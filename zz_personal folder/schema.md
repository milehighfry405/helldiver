Graphiti Schema for Helldiver Research System
Date: 2025-01-20
Purpose: Define custom entity types for Helldiver's knowledge graph storage

Entity Type Definitions
Meta-Entities (Core Workflow)
1. ResearchFinding
Insights discovered through Helldiver research workers.
pythonclass ResearchFinding(BaseModel):
    """Insight discovered through research."""
    topic: str  # What this finding is about
    finding_type: str  # strategic_insight | competitive_analysis | best_practice | limitation | workflow_guide | technical_spec | configuration_spec | prompt_template | integration_pattern | troubleshooting_guide | data_schema
    content_summary: str  # The actual finding (1-5 sentences)
    source_type: str  # academic | industry | tool_docs | critical_analysis
    confidence: str  # high | medium | low
    session_name: str  # Which research session produced this
2. StrategicIntent
Your contextual reasoning about why something matters.
pythonclass StrategicIntent(BaseModel):
    """User's strategic context and reasoning."""
    goal: str  # What we're trying to achieve
    related_topics: list[str]  # Topics this connects to
    priority: str  # critical | important | backlog
    rationale: str  # WHY this matters (2-5 sentences)
    key_decisions: str | None  # Specific decisions made
3. ExecutionOutcome
Learnings from actually doing the work.
pythonclass ExecutionOutcome(BaseModel):
    """Results and learnings from execution."""
    task_description: str  # What was done
    approach_used: str  # How it was done
    what_worked: str  # Successful aspects
    what_failed: str  # What didn't work
    insights_gained: str  # Meta-learnings
    would_repeat: bool  # Would you do this again?
    related_topics: list[str]  # Links back to research/strategy
Domain Entities (GTM Project)
4. Company
Target companies, competitors, customers being researched.
pythonclass Company(BaseModel):
    """Company entity."""
    company_name: str  # Company name (avoid 'name' - protected field)
    stage: str | None  # Seed | Series A | Series B | Series C | Series D+ | Public
    industry: str | None  # Market/vertical
    description: str  # Brief summary (1-2 sentences)
5. Tool
Software, platforms, APIs being researched or used.
pythonclass Tool(BaseModel):
    """Software tool or platform."""
    tool_name: str  # Tool name (avoid 'name' - protected field)
    category: str | None  # data_enrichment | CRM | automation | API
    description: str  # What it does (2-3 sentences)
6. Methodology
Processes, frameworks, workflows being developed or used.
pythonclass Methodology(BaseModel):
    """Process or workflow."""
    methodology_name: str  # Process name (avoid 'name' - protected field)
    step_count: int | None  # Number of steps
    description: str  # What this methodology does

Protected Field Names
Do not use these as custom attribute names:
uuid, name, group_id, labels, created_at, summary, attributes, name_embedding

Usage
Define Entity Types Dictionary
pythonentity_types = {
    "ResearchFinding": ResearchFinding,
    "StrategicIntent": StrategicIntent,
    "ExecutionOutcome": ExecutionOutcome,
    "Company": Company,
    "Tool": Tool,
    "Methodology": Methodology
}
Commit Research to Graphiti
pythonawait graphiti.add_episode(
    name="Helldiver Research Session",
    episode_body=research_output,  # Text from workers
    entity_types=entity_types,  # Pass relevant types
    group_id="helldiver_research",  # Single group for all
    source=EpisodeType.text,
    source_description="Research output from Helldiver workers",
    reference_time=datetime.now(timezone.utc)
)
```

### Entity Type Matrix

**Which entity_types to pass for different episodes:**

| Episode Source | Entity Types | Example |
|---------------|--------------|---------|
| Helldiver Research | ResearchFinding, Company, Tool, Methodology | Workers produce research about Clay + Arthur.ai |
| Strategic Context | StrategicIntent, Company, Tool | You explain why Arthur.ai matters |
| Execution Learnings | ExecutionOutcome, Tool, Methodology | You report what worked in Clay campaign |

**Only pass types actually present in that episode's content.**

---

## Worker Prompt Improvements

Add to system prompts for all 4 Helldiver workers:
```
When presenting research findings:

1. Use clear headers to separate distinct findings
   - Use "## " for major topics
   - Use "### " for sub-findings

2. Signal important findings explicitly
   - Start key insights with "Key finding:" or "Research shows:"
   - Distinguish facts from analysis

3. Use consistent terminology
   - Once you name something (e.g., "Clay API"), use that exact term throughout
   - Be explicit rather than using pronouns

4. Use full names on first mention
   - "Arthur.ai" not "Arthur"
   - "OpenAI GPT-4" not "GPT-4"

5. Format execution knowledge with clear type signals:
   - For step-by-step processes: Use numbered steps ("Step 1:", "Step 2:") or workflow language ("First, then, next, finally")
   - For configuration settings: Use consistent format ("Setting: value" or "Parameter: value")
   - For prompt templates: Clearly label as prompts, show exact text, include context
   - For integrations: Describe data flow and what connects to what
   - For troubleshooting: State problem clearly, provide solution
   - For data structures: Show field names/types, describe relationships

Focus on DEPTH and QUALITY of research. These are structural hints, not constraints.

How Graphiti Works
Deduplication

Graphiti deduplicates entities automatically based on entity name similarity
Uses semantic embeddings to find similar entities
If found, merges them (attributes update to latest values)
This is normal and expected behavior

Temporal Tracking

Relationships (edges) between entities get temporal tracking (valid_at/invalid_at)
Entity attributes update/overwrite when entities merge
This means attribute history is not preserved (usually fine)

Search
python# Search for entities
results = await graphiti.search("Clay API rate limits")

# Search with filters
from graphiti_core.search.search_filters import SearchFilters

results = await graphiti.search(
    query="Clay API",
    filters=SearchFilters(labels=["ResearchFinding"])
)

Implementation Checklist
Phase 1: Schema Definition

 Create Pydantic models for all 6 entity types
 Verify attribute names don't conflict with protected fields

Phase 2: Integration

 Find where Helldiver commits to Graphiti (likely main.py)
 Update add_episode() call to include entity_types dict
 Set group_id to "helldiver_research"
 Set reference_time correctly (UTC timezone-aware)

Phase 3: Worker Prompts

 Add structural hints to all 4 worker system prompts
 Test that outputs use headers and "Key finding:" markers

Phase 4: Testing

 Run one research session
 Commit to Graphiti
 Check Neo4j:

 Entities have labels like ["Entity", "ResearchFinding"]
 Attributes are populated (topic, finding_type, etc.)
 No obvious issues


 Test search: Can you find entities by type?

Phase 5: Manual Episodes (Optional)

 Create workflow for adding StrategicIntent episodes
 Create workflow for adding ExecutionOutcome episodes


Requirements

OpenAI or Gemini (for structured output support)
Neo4j 5.26+
Graphiti v0.20+


That's it. Define types, pass to add_episode, done.