# Graphiti Architectural Constraints

**Date**: 2025-01-25
**Context**: Proof of Concept testing to validate edge-rich property graph architecture
**Status**: Documented constraints based on empirical testing and source code analysis

---

## Executive Summary

Graphiti has **two fundamental architectural constraints** that prevent both the original node-based approach (ResearchFinding/StrategicIntent/ExecutionOutcome as entity nodes) and the edge-rich approach (findings as custom edge types):

1. **Named Entity Recognition (NER) only** - Cannot extract conceptual entities that ARE the text structure
2. **Verb-based relationship extraction** - Cannot create edge types from nouns (RESEARCH_FINDING isn't a verb)

---

## Constraint 1: Entity Extraction is NER-Only (Why Original Plan Failed)

### What We Tried (Session 8)
```python
# Original entity schema - meta-entities as nodes
class ResearchFinding(BaseModel):
    finding_type: str
    confidence: float
    key_insight: str
```

Expected Neo4j result:
```
(:ResearchFinding {
    finding_type: "capability_assessment",
    confidence: 0.95,
    key_insight: "Arthur.ai has strong ML drift detection"
})
```

### What Actually Happened
- **NO ResearchFinding nodes created** ❌
- Generic `Entity` nodes created instead (no labels, no custom attributes)
- Extraction prompt ignores meta-entities entirely

### Why It Failed: NER Architecture

**Graphiti's extraction prompt** (from `graphiti_core/prompts/extract_nodes.py:169-196`):
```
Given the above text, extract entities from the TEXT that are
explicitly or implicitly **mentioned**.
```

Key word: **"mentioned"**

This is Named Entity Recognition - looking for **proper nouns referenced in text**:
- "Arthur.ai" is mentioned ✅ → Company node
- "Clay" is mentioned ✅ → Tool node
- "Kubernetes" is mentioned ✅ → Tool node

**ResearchFinding is NOT mentioned** - it IS the text itself ❌

### Two-Stage Extraction Problem

Graphiti extracts entities in two stages:

**Stage 1**: Extract entity **names** from text
```python
class ExtractedEntity(BaseModel):
    name: str  # REQUIRED - must have a name!
    entity_type_id: int
```

**Stage 2**: For each named entity, extract attributes
```python
new_node = EntityNode(
    name=extracted_entity.name,  # Must have a name!
    labels=['Entity', entity_type_name],
    attributes={...}  # Custom fields extracted here
)
```

**ResearchFinding has no "name" in the text** to extract in Stage 1 → extraction fails before Stage 2.

### Empirical Evidence

PoC test (Session 8, 2025-01-24):
```
Episode text: "Key finding about Arthur.ai: They have strong capabilities
in ML model drift detection with 95% confidence."

Expected: ResearchFinding node with confidence=0.95
Actual: NO ResearchFinding node
Result: Company node (Arthur.ai) + Methodology node (ML drift detection)
```

**Conclusion**: Graphiti's NER cannot extract conceptual entities (findings, intents, outcomes) that represent the structure/meaning of text rather than concrete things mentioned in text.

---

## Constraint 2: Edge Types Must Be Verbs (Why Edge-Rich Plan Failed)

### What We Tried (This Session)
```python
# Edge-rich schema - findings as edge types
EDGE_TYPES = {
    "RESEARCH_FINDING": ResearchFinding,
    "STRATEGIC_INTENT": StrategicIntent,
    "EXECUTION_OUTCOME": ExecutionOutcome,
}
```

Expected Neo4j result:
```
(Episode)-[:RESEARCH_FINDING {
    finding_type: "capability_assessment",
    confidence: 0.95
}]->(Arthur.ai)
```

### What Actually Happened
- **NO `RESEARCH_FINDING` edge type created** ❌
- **NO `STRATEGIC_INTENT` edge type created** ❌
- **NO `EXECUTION_OUTCOME` edge type created** ❌
- Generic `RELATES_TO` edges created instead
- **NO custom properties** (finding_type, confidence) extracted

### Why It Failed: Relationship Semantics

**Valid Neo4j relationship types are VERBS**:
- Arthur.ai `-[:USES]->` Kubernetes ✅
- Arthur.ai `-[:COMPETES_WITH]->` Competitor ✅
- Episode `-[:MENTIONS]->` Arthur.ai ✅

**Invalid relationship types (NOUNS)**:
- Episode `-[:RESEARCH_FINDING]->` Arthur.ai ❌ (not a verb)
- Episode `-[:STRATEGIC_INTENT]->` Arthur.ai ❌ (not a verb)
- Episode `-[:EXECUTION_OUTCOME]->` Arthur.ai ❌ (not a verb)

User's key insight: *"I personally don't see how 'research finding' is a type of relationship? Like there isn't a verb there, like 'relates' or 'mentions' - how could that be an edge?"*

### What Graphiti Actually Does

Graphiti extracts **semantic verb-based relationships**:

```
Neo4j Edge TYPE: RELATES_TO (generic container)
Edge NAME property: USES, TECH_DEPENDENCY, HAS_CAPABILITY (semantic verbs)
Edge FACT property: "Arthur.ai uses Kubernetes for infrastructure..."
```

Example from PoC:
```cypher
(Arthur.ai)-[:RELATES_TO {
    name: "USES",
    fact: "Arthur.ai uses Kubernetes for infrastructure."
}]->(Kubernetes)
```

### Custom Edge Types Parameter Status

The `edge_types` parameter exists in Graphiti's API:
```python
await graphiti.add_episode(
    entity_types=ENTITY_TYPES,
    edge_types=EDGE_TYPES,  # Parameter exists!
    edge_type_map=EDGE_TYPE_MAP
)
```

**BUT**: Our testing shows it does NOT:
1. Create custom Neo4j relationship types (still creates `RELATES_TO`)
2. Extract custom properties from Pydantic models (no `confidence`, `finding_type`, etc.)

**Hypothesis**: This parameter may be:
- Future functionality (not fully implemented)
- Requires additional configuration we haven't found
- Works differently than blueprint assumed

**Evidence**: PoC test showed ZERO custom edge types or properties created despite passing all parameters.

---

## What DOES Work in Graphiti

### ✅ Concrete Entity Extraction (NER)

**Works perfectly for entities that are MENTIONED**:
- Companies (Arthur.ai, Clearbit, ZoomInfo)
- Tools (Clay, Kubernetes)
- Methodologies (competitive analysis, ML drift detection)
- Projects (if named: "Project Nightingale")
- People (if named: "John Smith from Arthur.ai")

**Extraction quality**: High - Graphiti correctly identifies:
- Entity type classification (Company vs Tool vs Person)
- Optional attributes (industry, stage, vendor)
- Cross-references (Arthur.ai mentioned in multiple episodes → same node)

### ✅ Semantic Relationship Extraction

**Works for verb-based relationships**:
```
Arthur.ai -[:RELATES_TO {name: "USES"}]-> Kubernetes
Arthur.ai -[:RELATES_TO {name: "FOCUSED_ON"}]-> financial services
Clay -[:RELATES_TO {name: "PARTNERS_WITH"}]-> Clearbit
```

**Edge properties available**:
- `name`: Semantic relationship type (verb)
- `fact`: Full text description of relationship
- `valid_at`: Temporal tracking (when fact was true)
- `uuid`, `group_id`: Standard Graphiti metadata

### ✅ Temporal Tracking

**Bi-temporal model works**:
- `valid_at`: When fact was true in reality
- `created_at`: When ingested into graph
- `invalid_at`: When fact was superseded/contradicted

**Use case**: Track how understanding evolves over time
```cypher
// Get facts about Arthur.ai valid in March 2024
MATCH ()-[r]->(:Company {name: "Arthur.ai"})
WHERE r.valid_at >= datetime('2024-03-01')
  AND r.valid_at < datetime('2024-04-01')
RETURN r.fact
```

### ✅ Episode Containers

**Episodes as structural nodes**:
```
(:Episodic {
    name: "poc_edge_extraction_test",
    group_id: "helldiver_research",
    source_description: "Edge Extraction PoC Test",
    content: "Full episode text..."
})
```

**Episode links entities via MENTIONS**:
```
(Episode)-[:MENTIONS]->(Arthur.ai)
(Episode)-[:MENTIONS]->(Clay)
```

---

## What Does NOT Work

### ❌ Meta-Entity Nodes

**Cannot extract**:
- ResearchFinding as entity node
- StrategicIntent as entity node
- ExecutionOutcome as entity node
- Any conceptual entity that IS the text structure rather than being mentioned IN the text

**Why**: NER architecture requires extractable "names" - meta-entities have no name to extract.

### ❌ Custom Edge Types (Nouns as Relationships)

**Cannot create**:
- `-[:RESEARCH_FINDING]->` as edge type
- `-[:STRATEGIC_INTENT]->` as edge type
- `-[:EXECUTION_OUTCOME]->` as edge type

**Why**: Not valid relationship semantics (nouns, not verbs)

### ❌ Custom Edge Properties (from Pydantic Models)

**Cannot extract** (based on PoC testing):
- `finding_type` property on edges
- `confidence` property on edges
- `methodology_used` property on edges
- Any custom Pydantic model fields for edge types

**Current state**: `edge_types` parameter exists but does not populate custom properties in practice.

---

## Architectural Boundaries for Schema Design

### What You CAN Model in Graphiti

**1. Domain Entities (Concrete Nouns)**
- ✅ Companies, tools, people, projects mentioned by name
- ✅ Methodologies, technologies referenced in text
- ✅ Markets, verticals, industries named explicitly

**2. Relationships Between Entities (Verbs)**
- ✅ Company USES Tool
- ✅ Company COMPETES_WITH Company
- ✅ Person WORKS_AT Company
- ✅ Tool INTEGRATES_WITH Tool

**3. Relationship Context (Text Descriptions)**
- ✅ Full text fact stored on each edge
- ✅ Temporal validity (when relationship was true)
- ✅ Source episodes (which episodes mentioned this)

**4. Temporal Evolution**
- ✅ Track when facts became true (valid_at)
- ✅ Track when facts were superseded (invalid_at)
- ✅ Query point-in-time state of knowledge

### What You CANNOT Model (Directly)

**1. Findings as First-Class Objects**
- ❌ ResearchFinding as separate node type
- ❌ Finding properties (confidence, type) as structured fields
- ❌ Findings-about-findings (meta-relationships)

**2. Intent/Outcome as Separate Entities**
- ❌ StrategicIntent node with status, priority, owner fields
- ❌ ExecutionOutcome node with metrics, blockers fields
- ❌ Typed edges FROM these to entities they target

**3. Structured Finding Properties**
- ❌ confidence: 0.95 as queryable field
- ❌ finding_type: "capability_assessment" as filterable property
- ❌ Custom edge properties from Pydantic models

---

## Workarounds and Alternatives

### Option 1: Findings in Episode Content (Current Graphiti Capability)

**Store findings as structured text in episodes**:
```python
episode_body = """
FINDING: Arthur.ai has strong ML drift detection (confidence: 0.95)
FINDING_TYPE: capability_assessment
METHODOLOGY: competitive_analysis, product_trials

Arthur.ai focuses on ML monitoring for financial services...
"""
```

**Pros**:
- Works with Graphiti's current architecture
- Still get entity extraction (Arthur.ai → Company node)
- Still get relationships (Arthur.ai FOCUSED_ON financial services)
- Temporal tracking via episode valid_at

**Cons**:
- Findings not first-class queryable (need text search)
- No structured confidence filtering (can't query "confidence > 0.9")
- Finding metadata mixed with content

### Option 2: Findings in Episode Attributes (Custom Metadata)

**Extend Episode nodes with custom properties**:
```python
# Hypothetical - would need custom episode ingestion
episode = EpisodicNode(
    name="Arthur AI Research",
    content="...",
    custom_attributes={
        "findings": [
            {"type": "capability", "confidence": 0.95, "entity": "Arthur.ai"},
            {"type": "partnership", "confidence": 0.9, "entity": "Clay"}
        ]
    }
)
```

**Pros**:
- Structured storage
- Queryable via Neo4j (episode.custom_attributes.findings)

**Cons**:
- Not standard Graphiti pattern (requires customization)
- Findings not connected to entity nodes via edges
- Unclear if Graphiti supports custom episode properties

### Option 3: Pre-Extract Findings, Attach to Edges (Hybrid)

**Use Claude to extract findings BEFORE Graphiti**:
```python
# Step 1: Extract findings with Claude
findings = await claude.extract_findings(episode_text)
# Returns: [{"entity": "Arthur.ai", "confidence": 0.95, "type": "capability"}]

# Step 2: Add to Graphiti (entities + relationships extracted)
await graphiti.add_episode(episode_body=episode_text, ...)

# Step 3: Query edges, attach finding metadata
# (Requires post-processing or custom Neo4j writes)
```

**Pros**:
- Structured finding extraction (Claude is good at this)
- Graphiti handles entities/relationships
- Finding metadata could be attached to edges

**Cons**:
- Two-pass process (Claude + Graphiti)
- Extra complexity
- Need to map findings to extracted edges

### Option 4: Use Graphiti for Entities Only, Custom Layer for Findings

**Graphiti**: Entity extraction, deduplication, temporal tracking
**Custom**: Finding storage, structured properties, meta-relationships

**Pros**:
- Use each tool for what it does well
- Full control over finding schema
- Can model findings however needed

**Cons**:
- Two systems to maintain
- Need integration layer
- More complex architecture

---

## Recommendations for Deep Research

### Constraint Your Research With These Knowns

**Graphiti CAN**:
1. Extract concrete entities mentioned in text (companies, tools, people, methodologies)
2. Extract semantic verb-based relationships between entities
3. Store relationship descriptions as text (`fact` property)
4. Track temporal validity of relationships
5. Deduplicate entities across episodes
6. Link episodes to entities via MENTIONS

**Graphiti CANNOT** (validated via PoC):
1. Extract meta-entities (findings, intents, outcomes) as nodes
2. Create custom edge types from nouns (RESEARCH_FINDING as edge type)
3. Extract structured properties for edge types (confidence, finding_type)
4. Model findings as first-class graph objects with queryable attributes

### Questions for Your Research

**1. Schema Design**
- Can findings be represented as **verb-based relationships**?
  - Example: Episode `-[:DISCOVERED_CAPABILITY]->` Arthur.ai (instead of RESEARCH_FINDING)
- Can we use **entity attributes** instead of separate finding nodes?
  - Example: Arthur.ai node with `capabilities: ["ML drift detection"]` attribute
- Can **Episode nodes carry structured finding metadata**?

**2. Retrieval Patterns**
- Is text search on `fact` properties sufficient for finding retrieval?
- Do we need structured confidence filtering? (If yes, Graphiti alone won't work)
- Can we achieve "entity-centric retrieval" with current entity+relationship extraction?

**3. Hybrid Approaches**
- Should we pre-extract findings with Claude, then use Graphiti for entities?
- Can we post-process Graphiti's output to add finding metadata?
- Do we need a separate finding storage layer outside Graphiti?

**4. Alternative Tools**
- Would direct Neo4j + custom extraction give more flexibility?
- Are there other graph libraries better suited for conceptual entities?
- Is the edge-rich pattern achievable outside Graphiti?

---

## Source Code References

**Entity Extraction**: `graphiti_core/utils/maintenance/node_operations.py:88-199`
- extract_nodes() function
- Two-stage extraction (names, then attributes)

**Extraction Prompt**: `graphiti_core/prompts/extract_nodes.py:169-196`
- "extract entities...explicitly or implicitly mentioned"
- NER-focused design

**Edge Extraction**: `graphiti_core/graphiti.py:378-411`
- _extract_and_resolve_edges() method
- extract_edges() call with edge_types parameter

**API Signature**: `graphiti_core/graphiti.py:611`
- add_episode() parameters including edge_types, edge_type_map

---

## Test Results Summary

**Test Date**: 2025-01-25
**Test Script**: `test_edge_extraction.py`
**Episode Content**: Research about Arthur.ai, Clay, Kubernetes

### Entities Extracted ✅
- Arthur.ai (Company)
- Clay (Tool)
- Kubernetes (Tool)
- Clearbit (Company)
- ZoomInfo (Company)
- machine learning model drift detection (Methodology)
- 7 additional generic Entity nodes

### Relationships Extracted ✅
- 10 RELATES_TO edges with semantic names:
  - USES, TECH_DEPENDENCY, HAS_CAPABILITY
  - PRIMARY_USE_CASE, FOCUSED_ON, VALIDATED_BY
- 13 MENTIONS edges (episode → entities)

### Custom Edge Types ❌
- ZERO RESEARCH_FINDING edges
- ZERO STRATEGIC_INTENT edges
- ZERO EXECUTION_OUTCOME edges
- ZERO custom properties (finding_type, confidence, etc.)

### Conclusion
Graphiti's `edge_types` parameter **does not create custom edge types or extract custom properties** as the blueprint architecture assumed.

---

**End of Constraints Document**
