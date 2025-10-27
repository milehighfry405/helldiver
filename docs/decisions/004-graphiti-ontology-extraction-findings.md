# ADR 004: Graphiti Ontology Extraction Findings

**Date**: 2025-01-26
**Status**: Validated via Testing
**Context**: Validating edge-rich ontology architecture for Helldiver research intelligence system

---

## Executive Summary

We tested Graphiti's custom entity and edge type capabilities to validate an ontology-driven knowledge graph architecture. This document captures critical findings that inform implementation decisions.

---

## Test Setup

### Test Environment
- **Graphiti Version**: 0.22.0
- **Neo4j**: Local instance (bolt://localhost:7687)
- **Test Date**: 2025-01-26
- **Test Files**:
  - `test_ontology_extraction.py` (extraction test)
  - `validate_ontology_results.py` (Neo4j validation)
  - `context/test_ontology_extraction/academic_researcher_verbalized.txt` (test data)

### Ontology Configuration
**Entity Types**: 9 types
- Strategic: ResearchObjective, Hypothesis, Finding, Methodology, Implementation
- Domain: Company, Tool, Market, Capability

**Edge Types**: 12 types
- INVESTIGATES, TESTS, REVEALS, SUPPORTS, CONTRADICTS, IMPLEMENTS, INFORMS
- TARGETS, COMPETES_WITH, USES, ENABLES, REQUIRES

---

## Key Finding 1: Strategic Entities Require Deliberate Verbalization

### What We Tested

**Natural prose** (from actual research outputs):
```
Key finding: Arthur's March 2025 launch represents a strategic inflection point
that creates a viable path to downmarket expansion...
```

**Verbalized format** (explicit entity naming):
```
Finding F1 'Strategic inflection point' reveals that Arthur's March 2025 launch
represents a viable path to downmarket expansion...
```

### Results

| Entity Type | Natural Prose | Verbalized Format |
|-------------|---------------|-------------------|
| ResearchObjective | ❌ Does NOT extract | ✅ Extracts perfectly |
| Hypothesis | ❌ Does NOT extract | ✅ Extracts perfectly |
| Finding | ❌ Does NOT extract | ✅ Extracts perfectly |
| Company | ✅ Extracts (proper noun) | ✅ Extracts (proper noun) |
| Tool | ✅ Extracts (proper noun) | ✅ Extracts (proper noun) |

### Extraction Statistics (Verbalized Test)
- **Total entities extracted**: 25
- **Strategic entities**: 11 (ResearchObjective: 1, Hypothesis: 3, Finding: 4, Methodology: 2, Implementation: 3)
- **Domain entities**: 14 (Company: 4, Tool: 1, Market: 1, Capability: 5)

### Why This Happens

**Named Entity Recognition (NER)** extracts **proper nouns**, not abstract concepts:
- ✅ "Arthur.ai" → Proper noun (company name)
- ✅ "Kubernetes" → Proper noun (tool name)
- ❌ "key finding" → Descriptive phrase (not a named entity)

**Deliberate verbalization transforms abstract concepts into named entities:**
- "Finding F1 'Downmarket self-serve requirement'" → NER treats "Downmarket self-serve requirement" as a named Finding entity
- This is similar to how NER extracts "Project Apollo" as a project name

### Implementation Requirement

**CRITICAL**: Worker prompts MUST be modified to use deliberate verbalization for strategic entities to extract.

**Required format**:
```
Finding F1 'name' reveals that [context]
Hypothesis H1 'name' proposes that [context]
Methodology M1 'name' was implemented to [context]
This finding SUPPORTS Hypothesis H1 with high confidence
```

**Without this format**: Only domain entities (companies, tools) will extract. Strategic research context (findings, hypotheses, methodologies) will be lost.

---

## Key Finding 2: Custom Edge Properties Do NOT Extract

### What We Tested

**Edge type definition**:
```python
class Supports(BaseModel):
    """Finding supports hypothesis"""
    confidence: Optional[str] = Field(None, description="high, medium, low")

edge_types = {"SUPPORTS": Supports}
```

**Verbalized text**:
```
This finding supports Hypothesis H1 'Product-led growth critical for SMB' with high confidence.
```

### Expected Behavior (Based on Ontology Architecture)
- ✅ Edge created with semantic type `SUPPORTS`
- ✅ Edge has `confidence="high"` property for structured queries

### Actual Behavior (Validated in Neo4j)

**Edge properties found**:
```python
{
  'name': 'SUPPORTS',              # ✅ Semantic type works
  'fact': 'Finding X supports...',  # ✅ Natural language context
  'source_node_uuid': '...',
  'target_node_uuid': '...',
  'valid_at': DateTime(...),
  'created_at': DateTime(...),
  'group_id': 'test_ontology',
  'episodes': [...],
  'fact_embedding': [...]
  # ❌ NO 'confidence' property
}
```

**Edge properties NOT found**:
- ❌ `confidence` (custom field defined in Pydantic model)
- ❌ Any other custom properties defined in edge type models

### Why This Happens

**Graphiti's edge extraction has two layers**:

1. **Semantic classification** (relationship type detection):
   - LLM identifies relationship verbs: SUPPORTS, CONTRADICTS, INFORMS
   - Stores in `name` property: `r.name = "SUPPORTS"`
   - ✅ **This works**

2. **Property extraction** (custom attributes):
   - Code exists in `edge_operations.py` line 583-603 to extract attributes
   - LLM is supposed to populate `attributes` dict with custom properties
   - Result: `attributes = {}` (empty dict every time)
   - ❌ **This does NOT work in practice**

**This is by design** (per Graphiti GitHub docs):
> "Custom relationships are under the 'name' attribute of the 'RELATES_TO' edge"

The expectation is that all semantic information goes into the `name` and `fact` properties as natural language, not structured fields.

### Impact on Architecture

**What you CANNOT do**:
```cypher
// ❌ Structured property queries don't work
MATCH (f:Finding)-[r:SUPPORTS]->(h:Hypothesis)
WHERE r.confidence = "high"
RETURN f, h

// ❌ Property-based filtering doesn't work
MATCH (f:Finding)-[r]->(i:Implementation)
WHERE r.priority = "high"
RETURN f, i
```

**What you CAN do**:
```cypher
// ✅ Semantic type filtering works
MATCH (f:Finding)-[r]->(h:Hypothesis)
WHERE r.name = "SUPPORTS"
RETURN f, h, r.fact

// ✅ Text-based context retrieval works
MATCH (f:Finding)-[r]->(h:Hypothesis)
WHERE r.name = "SUPPORTS" AND r.fact CONTAINS "high confidence"
RETURN f, h, r.fact
```

### Implementation Decision

**Accept text-based properties instead of structured fields:**
- Store "high confidence" in `r.fact` natural language
- Parse text at query time if precision is needed
- Use semantic relationship types (`r.name`) for primary filtering

**Rationale**: For the use case (reconstructing full research narrative for execution), natural language context in `r.fact` is sufficient. You're not building a precision query system; you're building a conversational context retrieval system.

---

## Key Finding 3: Semantic Relationship Types Work Perfectly

### What We Tested

12 custom edge types with explicit verbalization:
- SUPPORTS, CONTRADICTS, INFORMS, IMPLEMENTS, REVEALS, TESTS
- TARGETS, COMPETES_WITH, USES, ENABLES, REQUIRES, INVESTIGATES

### Results

**Extraction statistics**:
```
SUPPORTS: 2          ✅ Finding → Hypothesis
CONTRADICTS: 1       ✅ Finding → Hypothesis
INFORMS: 3           ✅ Finding → Implementation
IMPLEMENTS: 3        ✅ Methodology → Finding
TESTS: 1             ✅ Hypothesis testing
REVEALS: 1           ✅ Finding → Entity
REQUIRES: 1          ✅ Capability requirements
COMPETES_WITH: 3     ✅ Company → Company
TARGETS: 3           ✅ Company → Market
USES: 1              ✅ Company → Tool
RELATES_TO: 3        ✅ Fallback for unclear patterns
```

**Context quality sample**:
```
Finding 'Downmarket self-serve requirement' supports hypothesis
'Product-led growth critical for SMB'
```

### Why This Works

**Relationship detection is NOT NER-based** - it's semantic pattern matching:
- LLM reads: "Finding F1 SUPPORTS Hypothesis H1"
- LLM identifies verb: "supports"
- LLM maps to edge type: `SUPPORTS`
- LLM stores semantic classification in: `r.name = "SUPPORTS"`

**This is the core value of custom edge_types** - not property extraction, but semantic classification.

---

## Neo4j Schema Reality

### All Edges Are Generic RELATES_TO

**What you might expect**:
```cypher
(Finding)-[:SUPPORTS {confidence: "high"}]->(Hypothesis)
(Finding)-[:CONTRADICTS]->(Hypothesis)
```

**What actually exists**:
```cypher
(Finding)-[:RELATES_TO {name: "SUPPORTS", fact: "..."}]->(Hypothesis)
(Finding)-[:RELATES_TO {name: "CONTRADICTS", fact: "..."}]->(Hypothesis)
```

**All edges use**:
- Generic relationship type: `RELATES_TO`
- Semantic classification stored in property: `name`
- Context stored in property: `fact`

**Why this matters**:
- ❌ Can't use Neo4j relationship type filtering: `-[:SUPPORTS]->` (doesn't exist)
- ✅ Must use property filtering: `-[r]->` WHERE `r.name = "SUPPORTS"`

---

## Architecture Validation: Is This Sufficient?

### Use Case Requirements

**Primary goal**: Turn GTM research hypothesis into Clay execution
- Need to reconstruct: Full research narrative (findings, reasoning, priorities)
- Need to answer: "What findings support this hypothesis?" "What implementations are recommended?"
- Need to support: Conversational context retrieval, not precision filtering

### What the Ontology Provides

✅ **Entity extraction**: All strategic entities (Objectives, Hypotheses, Findings, Methodologies, Implementations)
✅ **Relationship classification**: Semantic types (SUPPORTS, CONTRADICTS, INFORMS)
✅ **Rich context**: Natural language in `r.fact` explains WHY relationships exist
✅ **Temporal tracking**: `valid_at` timestamps enable time-based queries
✅ **Graph structure**: Can traverse "Finding → Hypothesis → Implementation" paths

❌ **Structured property queries**: Cannot filter by `confidence="high"` or `priority="critical"`
❌ **Typed relationships**: All edges are RELATES_TO (semantic type in `name` property)

### Decision: PROCEED with Ontology Implementation

**Verdict**: The ontology architecture is **sufficient and viable** for the use case.

**Rationale**:
1. Text-based properties support conversational retrieval (the actual requirement)
2. Semantic relationship types enable narrative reconstruction
3. Loss of structured properties is acceptable given the use case doesn't require precision filtering
4. The architecture turns Graphiti's constraint (NER-only) into a design feature (deliberate verbalization)

---

## Implementation Checklist

### Phase 1: Worker Prompt Modification (Required)

**Modify worker prompts** in `workers/research.py` to output deliberate verbalization:

**Academic Research Worker**:
```python
system_prompt = """
When presenting findings, use this format:
- "Finding F1 'name' reveals that [context]"
- "Hypothesis H1 'name' proposes that [context]"
- "Methodology M1 'name' was implemented to [context]"
- "This finding SUPPORTS/CONTRADICTS Hypothesis H1"
- "Finding F1 INFORMS Implementation I1: [action]"
"""
```

Apply similar changes to:
- Industry Intelligence Worker
- Tool Analyzer Worker
- Critical Analyst Worker

### Phase 2: Entity/Edge Type Configuration

**Create** `graph/ontology.py`:
```python
from pydantic import BaseModel, Field
from typing import Optional

# Entity types
class Company(BaseModel):
    company_name: str
    industry: Optional[str] = None

class ResearchObjective(BaseModel):
    objective_id: str
    objective_name: str
    description: Optional[str] = None

class Finding(BaseModel):
    finding_id: str
    finding_name: str
    description: Optional[str] = None

# Edge types (properties won't extract, but define for API)
class Supports(BaseModel):
    """Finding supports hypothesis - confidence will be in fact text"""
    pass

class Contradicts(BaseModel):
    """Finding contradicts hypothesis - reasoning will be in fact text"""
    pass

# Export configurations
ENTITY_TYPES = {
    "Company": Company,
    "Tool": Tool,
    "ResearchObjective": ResearchObjective,
    "Hypothesis": Hypothesis,
    "Finding": Finding,
    # ... rest of entity types
}

EDGE_TYPES = {
    "SUPPORTS": Supports,
    "CONTRADICTS": Contradicts,
    "INFORMS": Informs,
    # ... rest of edge types
}

EDGE_TYPE_MAP = {
    ("Finding", "Hypothesis"): ["SUPPORTS", "CONTRADICTS"],
    ("Finding", "Implementation"): ["INFORMS"],
    ("Methodology", "Finding"): ["IMPLEMENTS"],
    # ... rest of edge mappings
}
```

### Phase 3: Update Graph Client

**Modify** `graph/client.py` to use ontology:
```python
from graph.ontology import ENTITY_TYPES, EDGE_TYPES, EDGE_TYPE_MAP

async def add_episode(...):
    result = await self.client.add_episode(
        name=name,
        episode_body=episode_body,
        source=EpisodeType.text,
        source_description=source_description,
        reference_time=reference_time,
        group_id=group_id,
        entity_types=ENTITY_TYPES,      # ← Add this
        edge_types=EDGE_TYPES,          # ← Add this
        edge_type_map=EDGE_TYPE_MAP,    # ← Add this
    )
```

### Phase 4: Query Pattern Updates

**Document query patterns** for the new architecture:

**Finding → Hypothesis relationships**:
```cypher
MATCH (f:Finding)-[r]->(h:Hypothesis)
WHERE r.name IN ["SUPPORTS", "CONTRADICTS"]
RETURN f.name, r.name, r.fact, h.name
```

**Implementation recommendations from findings**:
```cypher
MATCH (f:Finding)-[r]->(i:Implementation)
WHERE r.name = "INFORMS"
RETURN f.name, r.fact, i.name
ORDER BY r.created_at DESC
```

**Full research narrative reconstruction**:
```cypher
MATCH path = (o:ResearchObjective)-[*]->(i:Implementation)
WHERE o.group_id CONTAINS "arthur_gtm"
RETURN path
```

---

## Testing Validation

### Test Results Summary

**Test 1**: Strategic entity extraction with verbalization
- ✅ PASS: All 11 strategic entities extracted
- ✅ PASS: Entity types correctly classified
- ✅ PASS: Entity names preserved accurately

**Test 2**: Semantic relationship extraction
- ✅ PASS: 19 custom semantic relationships extracted
- ✅ PASS: Relationship types correctly classified
- ✅ PASS: Context preserved in `r.fact` property

**Test 3**: Custom edge property extraction
- ❌ FAIL: Properties defined in Pydantic models don't populate
- ✅ ACCEPTABLE: Text-based properties in `r.fact` sufficient for use case

**Test 4**: Domain entity extraction (baseline)
- ✅ PASS: Companies, tools, markets extract from both natural and verbalized text
- ✅ PASS: Proper noun NER works consistently

---

## Key Learnings

1. **Deliberate verbalization is REQUIRED** for strategic entity extraction
2. **Custom edge properties do NOT extract** - only semantic types in `name` property
3. **Text-based properties are sufficient** for conversational context retrieval
4. **Semantic relationship types work perfectly** for narrative reconstruction
5. **Worker prompts are the implementation lever** - prompt engineering enables the architecture

---

## References

- **Test file**: `test_ontology_extraction.py`
- **Validation script**: `validate_ontology_results.py`
- **Test data**: `context/test_ontology_extraction/academic_researcher_verbalized.txt`
- **Neo4j validation**: Direct queries on `group_id='test_ontology'`
- **Previous sessions**: SESSION_SUMMARY_8 (Graphiti NER investigation)
- **Graphiti docs**: GitHub community docs on custom relationship types

---

## Next Steps

1. ✅ Findings documented (this ADR)
2. ⏭️ Discuss verbalization overhead with user
3. ⏭️ Clarify episode metadata storage strategy
4. ⏭️ Plan implementation timeline (Phase 0 validation recommended)
5. ⏭️ Address MCP integration requirements
6. ⏭️ Design confidence propagation algorithm
7. ⏭️ Test community detection for strategic reasoning

---

## Key Finding 4: Episode Metadata Strategy

### The Question

Where do we store episode metadata like:
- `objective_id`: Links to ResearchObjective
- `hypothesis_ids`: Hypotheses tested in this episode
- `finding_ids`: Findings discovered
- `worker_type`: academic, industry, tool, critical
- `session_phase`: discovery, validation, execution
- `priority`: high, medium, low

### The Constraint

Graphiti's `add_episode()` has these parameters:
- `name` (episode name)
- `episode_body` (content)
- `source_description` (description)
- `group_id` (grouping)

**No `metadata` parameter exists.**

### Options Evaluated

**Option 1: Encode in `source_description`** (CHOSEN)
```python
source_description = f"""
[METADATA]
Research Objective: {objective_id}
Hypotheses: {', '.join(hypothesis_ids)}
Findings: {', '.join(finding_ids)}
Worker: {worker_type}
Phase: {session_phase}
Priority: {priority}

[CONTEXT]
{rich_description_of_what_this_episode_contains}
"""
```

**Option 2: Encode in `episode_body`** (top of content)
- Metadata as first section of episode body
- Gets extracted as entities if verbalized
- Bloats episode content

**Option 3: Store separately** (JSON file, separate DB)
- Link by episode UUID
- Requires maintaining separate storage
- Not integrated with Graphiti queries

### Decision: Option 1 (source_description)

**Rationale**:
1. ✅ `source_description` is indexed by Graphiti's search
2. ✅ Structured format is parseable if needed
3. ✅ Human-readable in Neo4j
4. ✅ No separate storage system needed
5. ✅ Matches retrieval pattern: "Match descriptions" (from ontology doc)
6. ✅ Don't need precise filtering (WHERE priority = "high") - need context reconstruction
7. ✅ Simple, maintainable, aligns with Graphiti's design

**When querying**:
- "Arthur AI GTM strategy" matches description text
- Sees linked objective/hypothesis IDs
- Returns episode with full context
- Can traverse to related entities (Objective, Hypothesis nodes)

**Implementation location**: `graph/client.py` - update `add_episode()` calls to generate structured `source_description`

---

## Key Finding 5: Confidence Propagation Strategy

### The Question

How do we handle confidence across multi-hop reasoning?

**Example**:
- Finding F1 supports Hypothesis H1 (confidence: high)
- Hypothesis H1 informs Implementation I1 (validation: strong)
- What's the overall confidence in Implementation I1?

### The Constraint

Graphiti has no built-in confidence propagation. Custom edge properties don't extract (they would stay empty).

### Options Evaluated

**Option 1: Numeric confidence with propagation algorithm**
- Store confidence as numbers (0.0-1.0)
- Multiply along paths: 0.8 * 0.9 = 0.72
- Requires parsing, computation, scoring logic

**Option 2: Text-based confidence in `r.fact`** (CHOSEN)
- Store: "Finding F1 SUPPORTS Hypothesis H1 with high confidence because..."
- Claude reads full `r.fact` text at retrieval time
- Claude interprets "high confidence" in context
- No algorithm needed

### Decision: Option 2 (Text-Based)

**Rationale**:
1. ✅ Use case is **context reconstruction**, not precision filtering
2. ✅ You want the FULL NARRATIVE, not "show only confidence > 0.7"
3. ✅ Natural language confidence ("high", "medium", "low") is sufficient
4. ✅ The reasoning in `r.fact` is more valuable than a score
5. ✅ Claude can interpret nuanced confidence from text better than numbers
6. ✅ No additional computation or parsing infrastructure needed

**Example**:
```
r.fact = "Finding F1 'Self-serve requirement' SUPPORTS Hypothesis H1
'Product-led growth' with high confidence because empirical data from
47 companies shows consistent 60-80% CAC reduction with PLG motions."
```

When reconstructing context for Clay execution:
- Claude retrieves all findings + relationships
- Reads the full `r.fact` text
- Sees "high confidence" + the evidence
- Makes informed decision based on narrative, not score

**If precision scoring is needed later**: Can add a simple parser to extract "high/medium/low" from text and map to numbers. But start with text-only.

---

## Key Finding 6: Community Detection Not Critical

### The Question

Should we use Graphiti's community detection (Leiden algorithm) for strategic reasoning?

### What Community Detection Does

- Clusters densely connected entities into communities
- Creates hierarchical summaries of related concepts
- Example: Might cluster Arthur.ai + Arize AI + WhyLabs as "ML monitoring vendors" community

### What We Actually Need

**Query pattern**: "Arthur AI GTM strategy"
**Want**: All findings, hypotheses, implementations related to Arthur AI
**Goal**: Reconstruct narrative for Clay execution

### Decision: Skip Community Detection (For Now)

**Rationale**:
1. ✅ Community detection is for **global exploration** ("What are all my research themes?")
2. ✅ We need **specific context reconstruction** ("Give me everything about Arthur AI")
3. ✅ Community detection helps at scale (100+ research sessions)
4. ✅ We're not at that scale yet
5. ✅ Specific queries work fine without clustering
6. ✅ Can add later when we have 50+ sessions and need global synthesis

**When to revisit**:
- Have 50+ research sessions
- Need cross-session pattern discovery
- Want "show me all companies researched across all sessions"
- Need global thematic summaries

**For now**: Focus on entity extraction, relationship classification, and retrieval quality for specific queries.

---

**Status**: Ready for implementation with constraints understood
