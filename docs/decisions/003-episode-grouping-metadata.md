# ADR-003: Episode Grouping Metadata Strategy

**Status:** Accepted
**Date:** 2025-10-13
**Context:** How to link episodes from the same research session in Graphiti

## Context

### The Problem

After implementing one-episode-per-worker chunking (ADR-002), we have 9 episodes for a full research cycle:
- 4 episodes for initial research (one per worker)
- 4 episodes for deep research (one per worker)
- 1 episode for refinement

**Question**: How do we tell the graph that these 9 episodes are related?

When AI queries the graph later:
- "Show me all episodes from Arthur AI research"
- "Find initial research vs deep research"
- "What's the chronological order?"

We need metadata to group and link episodes.

### Graphiti's Metadata Fields

Episodes in Graphiti support:
- `name` - Episode identifier (e.g., "Arthur AI analysis - Academic Research")
- `episode_body` - The actual text content
- `group_id` - Namespace for organizing data
- `source_description` - Free text field for metadata
- `reference_time` - Timestamp
- **Graphiti auto-links episodes temporally**

## Decision

### Three-Layer Metadata Strategy

Use **combination** of `name`, `group_id`, and `source_description` to create queryable relationships:

#### 1. Episode Name Pattern

```
"{session_name} - {worker_role}"
```

Examples:
- "Arthur AI product and market analysis - Academic Research"
- "Arthur AI product and market analysis - Industry Intelligence"
- "Downmarket ICP signals - Academic Research"

**Benefit**: All episodes from same session share prefix → easy to query

#### 2. Hierarchical Group ID

```
"helldiver_research/{session_name}/{research_type}"
```

Examples:
- `helldiver_research/arthur_ai_product_and_market_analysis/initial`
- `helldiver_research/arthur_ai_product_and_market_analysis/deep`
- `helldiver_research/arthur_ai_product_and_market_analysis/refinement`

**Benefit**: AI can filter by hierarchy:
- All Helldiver research: `helldiver_research/*`
- All Arthur AI episodes: `helldiver_research/arthur_ai_product_and_market_analysis/*`
- Just initial research: `helldiver_research/arthur_ai_product_and_market_analysis/initial`

#### 3. Source Description

```
"{research_type} Research | Session: {session_name} | {timestamp}"
```

Example:
```
"Initial Research | Session: Arthur AI product and market analysis | 2025-10-13T15:30:00"
```

**Benefit**: Programmatic linking + human-readable session info

### Complete Example

```python
# Episode for Academic Research worker
episode = {
    "name": "Arthur AI product and market analysis - Academic Research",
    "episode_body": "<worker findings ~1,900 tokens>",
    "group_id": "helldiver_research/arthur_ai_product_and_market_analysis/initial",
    "source_description": "Initial Research | Session: Arthur AI product and market analysis | 2025-10-13T15:30:00",
    "reference_time": datetime.now()
}
```

## How AI Queries This Structure

### Query: "Find all episodes from Arthur AI research"

**Method 1** - Search by name prefix:
```
MATCH (e:Episode) WHERE e.name STARTS WITH "Arthur AI product and market analysis"
```

**Method 2** - Filter by group_id:
```
MATCH (e:Episode) WHERE e.group_id CONTAINS "arthur_ai_product_and_market_analysis"
```

**Method 3** - Search source_description:
```
MATCH (e:Episode) WHERE e.source_description CONTAINS "Arthur AI product and market analysis"
```

### Query: "Show me initial research episodes"

```
MATCH (e:Episode) WHERE e.group_id ENDS WITH "/initial"
```

### Query: "Find Academic Research perspectives across all sessions"

```
MATCH (e:Episode) WHERE e.name CONTAINS "Academic Research"
```

### Query: "What was researched on October 13th?"

```
MATCH (e:Episode) WHERE e.reference_time >= "2025-10-13" AND e.reference_time < "2025-10-14"
```

## Consequences

### Positive

1. **Multiple query paths**: Name, group_id, source_description all provide different angles
2. **Hierarchical organization**: group_id enables filtering by session, research type, or both
3. **Human-readable**: All metadata fields make sense to humans reviewing the graph
4. **Flexible querying**: AI can use whatever field makes sense for the query
5. **Temporal links**: Graphiti auto-connects episodes chronologically as bonus

### Negative

1. **Redundancy**: Session name appears in 3 fields (name, group_id, source_description)
2. **String matching required**: Queries rely on substring matching (could be fragile)

### Neutral

1. **No custom properties needed**: Uses standard Graphiti fields
2. **MCP vs Python API irrelevant**: Same metadata structure works for both

## Implementation

### Python Code

```python
def commit_research_episode(session, research_type, worker_results):
    session_name = session.episode_name  # e.g., "Arthur AI product and market analysis"
    safe_session_name = session_name.replace(" ", "_").replace("/", "_")
    timestamp = datetime.now().isoformat()

    for worker_id, worker_name in workers:
        episode_name = f"{session_name} - {worker_name}"
        group_id = f"helldiver_research/{safe_session_name}/{research_type}"
        source_description = f"{research_type.title()} Research | Session: {session_name} | {timestamp}"

        await graphiti_client.commit_episode(
            name=episode_name,
            episode_body=worker_findings,
            group_id=group_id,
            source_description=source_description,
            reference_time=datetime.now()
        )
```

### Backward Compatibility

Old episodes (before this system):
- Had generic names like "Research: arthur ai based on out nyc"
- Used single `helldiver_research` group_id
- Can coexist with new structure
- New AI queries will naturally exclude old episodes due to different naming

## Alternative Considered: Custom Properties

**Option**: Use Graphiti custom entity types to add `session_id` property

**Why rejected**:
1. Requires defining custom schema upfront
2. Adds complexity to episode creation
3. Standard fields (name, group_id, source_description) are sufficient
4. Custom properties limit flexibility of future schema changes

## Related

- ADR-001: Episode Naming Strategy (provides the {session_name} and {worker_role})
- ADR-002: Graphiti Chunking Strategy (creates multiple episodes that need grouping)
