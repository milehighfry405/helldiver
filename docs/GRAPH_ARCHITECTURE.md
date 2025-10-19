# Graph Architecture Documentation

**Last Updated**: 2025-01-19
**Status**: Under Active Development

---

## Purpose

This document defines the knowledge graph architecture for the Helldiver Research system. The graph serves as the **permanent memory and reasoning substrate** for:

1. **Research Intelligence**: Storing findings from multi-agent research sessions
2. **Cross-Session Synthesis**: Connecting insights across different research topics
3. **Execution Layer**: Providing context for Claude Skills and other execution agents
4. **Long-Term Knowledge**: Building a comprehensive, queryable knowledge base

---

## Design Principles

### 1. **Optimize for Cross-Session Intelligence**
- Research findings should connect across topics
- Enable emergent insights from relationship traversal
- Support "show me everything about X" queries without manual filtering

### 2. **Future-Proof for Execution**
- Graph will power Claude Skills and autonomous agents
- Must support rapid context retrieval (<1s)
- Enable semantic + graph-based reasoning

### 3. **State-of-the-Art Schema Design**
- Custom entities tailored to research + execution workflows
- Leverage Graphiti's temporal awareness (bi-temporal model)
- Support both structured and unstructured data ingestion

---

## Current Architecture Decisions

### Group ID Strategy

**Status**: ⚠️ UNDER REVIEW (as of 2025-01-19)

**Current Implementation**:
```python
# Hierarchical group_id per session and research type
group_id = f"helldiver_research_{session_name}_{type}"

Examples:
- "helldiver_research_Custom_entities_for_Graphiti_knowledge_graphs_initial"
- "helldiver_research_Custom_entities_for_Graphiti_knowledge_graphs_deep"
```

**Problem Identified**:
- Graphiti MCP searches require **explicit group_id filtering**
- No wildcard/pattern matching support
- Cross-session queries require listing all group_ids manually
- Breaks the "omega context" vision - limits discoverability

**Option 1: Single Global Group ID** (RECOMMENDED)
```python
group_id = "helldiver_research"  # Same for ALL research
```

**Pros**:
- ✅ Natural cross-session querying
- ✅ One search finds everything
- ✅ Aligns with "brain" metaphor - unified knowledge base
- ✅ Matches Graphiti's design intent (see quickstart example)
- ✅ Simpler for Claude Skills integration

**Cons**:
- ❌ Can't easily filter by session via group_id alone
- ❌ Must use episode name prefixes or source_description for filtering

**Alternative Filtering Methods**:
```cypher
// Filter by session via episode name
MATCH (e:Episodic)
WHERE e.name STARTS WITH "Custom entities for Graphiti"
RETURN e

// Filter by research type via source_description
MATCH (e:Episodic)
WHERE e.source_description CONTAINS "Initial Research"
RETURN e

// Temporal filtering
MATCH (e:Episodic)
WHERE e.created_at >= datetime('2025-01-19')
RETURN e
```

**Option 2: Keep Hierarchical, Add Cross-Session Tooling**
- Maintain current structure
- Build custom search tools that query across multiple group_ids
- More complex, but preserves strict isolation

**Decision Needed**: Which approach aligns with the "omega context" vision?

---

### Custom Entity Types

**Status**: 🔬 ACTIVE RESEARCH

**Current State**: Using Graphiti's default entity extraction (no custom entities)

**Research Questions**:
1. Should we define custom entities for research workflows? (e.g., `ResearchFinding`, `Critique`, `Hypothesis`)
2. What attributes should custom entities have? (e.g., `confidence_level`, `source_quality`)
3. How does this impact retrieval performance?
4. What's the tradeoff between schema rigidity and flexibility?

**Active Research Sessions**:
- "Custom entities for Graphiti knowledge graphs"
- "Schema design principles for knowledge graphs"

**Next Steps**:
1. Complete custom entities research
2. Design optimal schema for research + execution
3. Test performance with custom vs default entities
4. Document final schema in this file

---

### Episode Structure

**Current Implementation**:
- **One episode per worker** (Academic, Industry, Tool, Critical Analyst)
- **Optimal size**: 1,400-2,600 tokens per episode
- **Why**: Graphiti extracts richer entities from smaller, focused episodes

**Episode Metadata**:
```python
{
    "name": "{Session Name} - {Worker Type}",
    "source_description": "{Type} Research | Session: {Name} | {Timestamp}",
    "group_id": "{strategy TBD}",
    "reference_time": "2025-01-19T21:01:02.026300000Z",  # UTC, timezone-aware
    "valid_at": "2025-01-19T21:01:02.026300000Z"  # Required for MCP search
}
```

**Critical Requirements**:
- ✅ `reference_time` must be timezone-aware (`datetime.now(timezone.utc)`)
- ✅ `valid_at` must be set (Graphiti auto-sets from `reference_time`)
- ✅ `group_id` must not contain slashes (Graphiti validation)

---

### Temporal Model

**Graphiti's Bi-Temporal Tracking**:
- **Event Time** (`valid_at`/`invalid_at`): When the fact was true in reality
- **System Time** (`created_at`): When the fact was ingested into the graph

**Use Cases**:
- Query "what did we know about X on date Y"
- Track evolving understanding over time
- Handle contradictions via temporal edge invalidation

**Example**:
```python
# Initial research: "Schema design prioritizes queries"
valid_at: 2025-01-15

# Deep research contradicts: "Schema design prioritizes information structure"
# Graphiti automatically invalidates the old edge, sets invalid_at: 2025-01-19
```

---

## Integration Points

### Helldiver Research Agent
- **Writes**: Research episodes (initial + deep)
- **Reads**: Existing knowledge for context-aware research
- **Pattern**: Continuous ingestion during refinement phase

### Claude Skills (Planned)
- **Reads**: Query graph for execution context
- **Writes**: Execution results, learned patterns
- **Pattern**: Hybrid retrieval (semantic + graph traversal)

### Other AI Agents (Future)
- **MCP Access**: Via Graphiti MCP server
- **Requirements**: Must use correct `group_id` filtering (TBD)
- **Use Cases**: Cross-agent knowledge sharing, collaborative reasoning

---

## Open Questions

1. **Group ID Strategy**: Single global vs hierarchical?
2. **Custom Entities**: Which types, what attributes?
3. **Schema Evolution**: How to handle schema changes as research evolves?
4. **Performance**: What's the query latency target for execution agents?
5. **Claude Skills Integration**: How should skills query the graph?

---

## Research Roadmap

### Phase 1: Foundation (Current)
- [ ] Finalize group_id strategy
- [ ] Complete custom entities research
- [ ] Design optimal schema
- [ ] Validate MCP compatibility

### Phase 2: Optimization
- [ ] Performance benchmarks (query latency)
- [ ] Schema refinement based on real usage
- [ ] Build custom search recipes for common patterns

### Phase 3: Execution Layer
- [ ] Claude Skills integration design
- [ ] Execution result ingestion patterns
- [ ] Multi-agent coordination via graph

---

## Key Insights from Research

### Graphiti Design Intent
- **Source**: Quickstart example, MCP implementation
- **Finding**: `group_id` is **optional** organizational tool, not required isolation
- **Implication**: Default behavior searches entire graph - aligns with "omega context"

### Enterprise Use (Zep)
- **Pattern**: Per-user isolation (`group_id = f"user_{user_id}"`)
- **Why**: Multi-tenant SaaS - User A can't see User B's data
- **Our Context**: Single user, multiple research topics - different requirements

### Graphiti Best Practices
- **Episode Size**: 1,000-2,000 tokens optimal for entity extraction
- **Temporal Awareness**: Use `reference_time` for point-in-time queries
- **Custom Entities**: Only add when domain structure is clear and stable

---

## Change Log

### 2025-01-19
- Initial document creation
- Documented group_id issue and options
- Added custom entities research status
- Defined open questions and roadmap

---

## References

- [Graphiti Core Repo](https://github.com/getzep/graphiti)
- [Graphiti MCP Server](C:\Users\laxdu\Programming\graphiti\mcp_server\)
- [Helldiver ADR-003: Episode Grouping Metadata](./decisions/003-episode-grouping-metadata.md)
- [Active Research: Custom Entities](../context/Custom_entities_for_Graphiti_knowledge_graphs/)

---

**Next Update**: After custom entities research completes
