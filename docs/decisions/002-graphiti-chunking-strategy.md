# ADR-002: Graphiti Chunking Strategy

**Status:** Accepted
**Date:** 2025-10-13
**Context:** Based on Graphiti best practices research

## Context

### The Problem

Graphiti is a knowledge graph system (backed by Neo4j) that extracts entities and relationships from text. The size of text chunks (episodes) dramatically affects extraction quality.

From Graphiti's own research on Russian election interference graph:
- **Large episodes (10,000+ tokens)**: Sparse, high-level entity extraction
- **Small episodes (1,000-2,000 tokens)**: Rich, detailed entity extraction with strong relationships

### Our Initial Approach (Wrong)

We were combining ALL worker reports into ONE episode per research session:

```
Episode 1: Initial Research (Combined)
- Academic research: ~2,500 tokens
- Industry intelligence: ~3,000 tokens
- Tool analysis: ~2,200 tokens
- Critical analysis: ~1,400 tokens
TOTAL: ~9,100 tokens ❌ TOO BIG
```

This would produce sparse entity extraction in the graph.

### Token Counts (Measured)

Actual worker report sizes from `Arthur_AI_product_and_market_analysis` session:
- Academic: ~1,910 tokens
- Industry: ~2,569 tokens
- Tool: ~2,235 tokens
- Critical: ~1,411 tokens
- Refinement distilled: ~1,500 tokens (after distillation)

**All reports fall in the 1,400-2,600 token range** - perfect for Graphiti!

## Decision

### One Episode Per Worker

Commit each worker report as a separate episode to Graphiti:

```
Initial Research Session:
├── Episode 1: "Arthur AI analysis - Academic Research" (~1,910 tokens)
├── Episode 2: "Arthur AI analysis - Industry Intelligence" (~2,569 tokens)
├── Episode 3: "Arthur AI analysis - Tool Analysis" (~2,235 tokens)
└── Episode 4: "Arthur AI analysis - Critical Analysis" (~1,411 tokens)

Deep Research Session:
├── Episode 5: "Downmarket ICP signals - Academic Research"
├── Episode 6: "Downmarket ICP signals - Industry Intelligence"
├── Episode 7: "Downmarket ICP signals - Tool Analysis"
└── Episode 8: "Downmarket ICP signals - Critical Analysis"

Refinement:
└── Episode 9: "Arthur AI analysis - User Context" (~1,500 tokens)
```

**Total for full research cycle: 9 episodes**

### Why This Works

1. **Optimal token range**: Each episode is 1,400-2,600 tokens (Graphiti sweet spot)
2. **Natural boundaries**: Worker roles provide logical chunking
3. **Perspective isolation**: Each worker has distinct focus (academic vs industry vs tools)
4. **Rich extraction**: Smaller episodes = more granular entity extraction
5. **Human auditable**: Easy to understand "this is the academic perspective"

### Refinement Episode

Distilled refinement context is ALREADY optimal size (~1,500 tokens) due to:
- LLM distillation with max_tokens=1500
- Extracting only mental models, reframings, constraints, priorities
- Filtering out conversational noise

No need to chunk refinement - commit as single episode.

## Consequences

### Positive

1. **Rich entity extraction**: Graphiti can extract detailed entities from focused text
2. **Better relationship mapping**: Each worker's entities connect meaningfully
3. **Queryable by perspective**: "Show me academic findings" vs "Show me industry findings"
4. **Optimal graph performance**: Episode sizes match Graphiti's design intent
5. **Natural chunking**: Worker architecture provides clean boundaries

### Negative

1. **More graph writes**: 4x episodes per research vs 1x (still fast, asynchronous)
2. **Slightly more complex**: Need to track multiple episode IDs per session

### Neutral

1. **Same total content**: Just organized differently for better extraction
2. **Backward compatible**: Old combined episodes can coexist with new structure

## Implementation

### Code Changes

**Before** (one big episode):
```python
episode_body = f"""
Narrative: {narrative}
Critical Analysis: {critical_analysis}
Worker Summaries: {all_workers_combined}
"""

commit_episode(episode_body)  # 9,000+ tokens
```

**After** (one episode per worker):
```python
for worker_id, worker_name in workers:
    episode_body = f"""
Research Query: {query}
Worker Role: {worker_name}

{worker_findings}  # 1,400-2,600 tokens
"""
    commit_episode(episode_body)
```

### Metadata for Grouping

See ADR-003 for how episodes from the same session are linked via metadata.

## Validation

### Before Chunking
- Episode size: 9,000+ tokens
- Expected extraction: Sparse, high-level entities
- Example: "Company" entity without specific details

### After Chunking
- Episode size: 1,400-2,600 tokens per worker
- Expected extraction: Rich, detailed entities
- Example: "Arthur AI" entity with funding stage, market position, product details

## References

- Graphiti Russian Election Interference project: "chunking articles into multiple Episodes produced significantly better results"
- Graphiti best practices: 1,000-2,000 token range for optimal extraction
- Our measurement: Worker reports naturally fall in this range

## Related

- ADR-001: Episode Naming Strategy (how episodes are named)
- ADR-003: Episode Grouping Metadata (how episodes link together)
