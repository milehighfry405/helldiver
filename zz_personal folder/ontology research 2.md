# Optimal Knowledge Graph Ontology for Research Intelligence Systems

Graphiti's temporal knowledge graph framework combined with strategic research intelligence creates unique design challenges. This specification provides a production-ready ontology that encodes research findings, strategic context, and execution guidance within Graphiti's NER-based constraints.

## Core Design Philosophy

**The central tension:** Graphiti requires entities to be mentioned in text, yet research intelligence demands capturing abstract strategic concepts like hypotheses and insights. The solution lies in **grounding abstractions through deliberate verbalization** in research agent outputs and episode descriptions.

Your closed system advantage means you can **optimize what research agents write** to match ontology needs. Agents should explicitly mention strategic concepts they're reasoning about, making abstract entities extractable while maintaining semantic richness.

## Entity Type Specification

### Tier 1: Concrete Domain Entities (Always Mentioned)

**1. Company** 
```python
class Company(BaseModel):
    """Organization being researched or analyzed"""
    name: str = Field(description="Full company name")
    industry: str | None = Field(description="Primary industry vertical")
    stage: str | None = Field(description="e.g., Series A, Public, Bootstrap")
    employee_count: int | None = Field(description="Team size")
    founded_year: int | None = Field(description="Year established")
```
*Extraction guidance:* Workers naturally mention companies when researching GTM strategies.

**2. Tool** 
```python
class Tool(BaseModel):
    """Software, platform, or technology being analyzed"""
    name: str = Field(description="Product/tool name")
    category: str | None = Field(description="e.g., Clay, Outreach, Analytics")
    pricing_model: str | None = Field(description="Freemium, Enterprise, Usage-based")
    key_capabilities: str | None = Field(description="Core features extracted")
```
*Extraction guidance:* Tools are explicitly named in tool research agent outputs.

**3. Person**
```python
class Person(BaseModel):
    """Individual mentioned in research"""
    name: str = Field(description="Full name")
    role: str | None = Field(description="Job title or function")
    company: str | None = Field(description="Current organization")
    expertise_area: str | None = Field(description="Domain specialization")
```
*Extraction guidance:* CEO quotes, case study subjects, expert sources.

### Tier 2: Strategic Concept Entities (Requires Deliberate Verbalization)

**4. ResearchObjective**
```python
class ResearchObjective(BaseModel):
    """Named strategic question or goal being investigated"""
    name: str = Field(description="Concise objective identifier, e.g., 'Arthur.ai downmarket GTM strategy'")
    objective_type: str | None = Field(description="market_analysis, competitive_research, tool_evaluation, strategic_planning")
    priority: str | None = Field(description="critical, high, medium, low")
    status: str | None = Field(description="active, completed, parked")
```
*Extraction pattern:* Structure refinement conversations to explicitly state: "The research objective 'Arthur.ai downmarket GTM using Clay' aims to..." This makes the objective entity extractable.

**5. Hypothesis**
```python
class Hypothesis(BaseModel):
    """Specific testable assumption or strategic premise"""
    name: str = Field(description="Short hypothesis identifier")
    statement: str = Field(description="Full hypothesis statement")
    confidence: float | None = Field(description="Belief strength 0-1")
    validation_status: str | None = Field(description="unvalidated, partially_validated, validated, refuted")
```
*Extraction pattern:* Agents explicitly write: "Hypothesis H1 'Clay enables faster ICP building' is being tested..." Creating named hypotheses makes them first-class entities.

**6. Methodology**
```python
class Methodology(BaseModel):
    """Specific approach, workflow, or playbook"""
    name: str = Field(description="Method identifier, e.g., 'Clay-to-Outreach workflow'")
    method_type: str | None = Field(description="workflow, framework, analysis_technique")
    maturity: str | None = Field(description="experimental, proven, best_practice")
    implementation_complexity: str | None = Field(description="low, medium, high")
```
*Extraction pattern:* When describing implementation: "The Clay-to-Outreach workflow methodology involves..." Naming the methodology creates extractable entity.

### Tier 3: Execution and Outcome Entities

**7. Implementation**
```python
class Implementation(BaseModel):
    """Concrete execution attempt of a methodology"""
    name: str = Field(description="Execution identifier with date/context")
    outcome: str | None = Field(description="success, partial_success, failure")
    metrics_achieved: str | None = Field(description="Quantitative results")
    lessons_learned: str | None = Field(description="Key takeaways")
    executed_date: datetime | None = Field(description="When implementation occurred")
```
*Extraction pattern:* When logging outcomes: "Implementation 'Clay workflow Jan 2025' resulted in..." Creates traceable execution records.

**8. Finding**
```python
class Finding(BaseModel):
    """Discrete insight or discovery from research"""
    name: str = Field(description="Short finding identifier")
    finding_type: str | None = Field(description="insight, data_point, pattern, risk")
    novelty: str | None = Field(description="novel, confirming, contradicting")
    actionability: str | None = Field(description="immediate, strategic, informational")
    confidence: float | None = Field(description="Reliability score 0-1")
```
*Extraction pattern:* Agents explicitly label findings: "Finding F1: 'Downmarket requires self-serve onboarding' shows that..."

**9. Market**
```python
class Market(BaseModel):
    """Market segment, vertical, or opportunity space"""
    name: str = Field(description="Market identifier")
    size: str | None = Field(description="TAM/market size estimate")
    growth_rate: str | None = Field(description="Annual growth estimate")
    maturity: str | None = Field(description="emerging, growth, mature, declining")
```

**10. Capability**
```python
class Capability(BaseModel):
    """Organizational or product capability"""
    name: str = Field(description="Capability identifier")
    capability_type: str | None = Field(description="technical, operational, strategic")
    maturity_level: str | None = Field(description="nascent, developing, established")
```

## Relationship Type Specification

### Structural Relationships

**1. INVESTIGATES** (ResearchObjective → Company/Tool/Market)
```python
class Investigates(BaseModel):
    """Links research objectives to their targets"""
    priority: str | None = Field(description="Research priority level")
    started_date: datetime | None = Field(description="When research began")
```
*Semantic meaning:* "We are investigating X for purpose Y"

**2. TESTS** (Methodology/Implementation → Hypothesis)
```python
class Tests(BaseModel):
    """Links execution to hypotheses being validated"""
    validation_outcome: str | None = Field(description="supports, refutes, inconclusive")
    evidence_strength: float | None = Field(description="0-1 strength")
```
*Semantic meaning:* "This approach tests whether X is true"

**3. IMPLEMENTS** (Implementation → Methodology)
```python
class Implements(BaseModel):
    """Links concrete executions to abstract methods"""
    fidelity: str | None = Field(description="How closely execution matched plan")
    adaptations: str | None = Field(description="Changes made during execution")
```

### Discovery Relationships

**4. REVEALS** (Finding → Company/Tool/Market/Capability)
```python
class Reveals(BaseModel):
    """Finding uncovers information about entity"""
    revelation_type: str | None = Field(description="capability, limitation, opportunity, risk")
    impact: str | None = Field(description="high, medium, low")
```
*Semantic meaning:* "Research finding reveals that Company X has capability Y"

**5. SUPPORTS** (Finding → Hypothesis)
```python
class Supports(BaseModel):
    """Finding provides evidence for hypothesis"""
    evidence_type: str | None = Field(description="quantitative, qualitative, anecdotal")
    strength: float | None = Field(description="0-1 evidence strength")
```

**6. CONTRADICTS** (Finding → Finding/Hypothesis)
```python
class Contradicts(BaseModel):
    """Identifies conflicting information"""
    resolution_status: str | None = Field(description="unresolved, resolved, accepted_conflict")
    resolution_notes: str | None = Field(description="How conflict was addressed")
```

### Execution Relationships

**7. ENABLES** (Tool/Capability → Methodology)
```python
class Enables(BaseModel):
    """Tool/capability makes methodology possible"""
    criticality: str | None = Field(description="required, enhances, optional")
    maturity: str | None = Field(description="How proven the enablement is")
```
*Semantic meaning:* "Clay enables the downmarket outreach methodology"

**8. REQUIRES** (Methodology → Capability/Tool)
```python
class Requires(BaseModel):
    """Dependency relationship"""
    requirement_type: str | None = Field(description="prerequisite, complementary, alternative")
    availability: str | None = Field(description="available, needs_acquisition, needs_development")
```

**9. INFORMS** (Implementation → ResearchObjective)
```python
class Informs(BaseModel):
    """Execution outcomes feed back to strategy"""
    insight_quality: str | None = Field(description="high_confidence, moderate, low_confidence")
    next_actions: str | None = Field(description="What this suggests doing next")
```

### Strategic Relationships

**10. TARGETS** (Company → Market)
```python
class Targets(BaseModel):
    """Company's go-to-market focus"""
    penetration_level: str | None = Field(description="early, growing, dominant")
    strategy_type: str | None = Field(description="land_and_expand, enterprise_first, product_led")
```

**11. COMPETES_WITH** (Company → Company)
```python
class CompetesWith(BaseModel):
    """Competitive relationship"""
    competitive_intensity: str | None = Field(description="direct, indirect, tangential")
    differentiation: str | None = Field(description="How they differ")
```

## Episode Structuring Strategy

Episodes in Graphiti are your **primary semantic encoding mechanism**. Since episode names, descriptions, and grouping influence retrieval, structure them intentionally.

### Episode Type Taxonomy

**Type 1: Research Session Episodes**
- **Name pattern:** `[Objective_Name]_Research_[Worker_Type]_[Date]`
- **Example:** `Arthur_GTM_Research_Industry_2025-01-15`
- **Description template:** "Industry worker researching Arthur.ai's downmarket GTM strategy using Clay, investigating hypothesis H1 about ICP targeting efficiency"
- **Content:** Raw research findings from a single worker
- **Extraction expectation:** Company, Tool, Finding entities + REVEALS, INVESTIGATES edges

**Type 2: Refinement Conversation Episodes**
- **Name pattern:** `[Objective_Name]_Refinement_[Session_Number]`
- **Example:** `Arthur_GTM_Refinement_Session_3`
- **Description template:** "Strategic refinement for Arthur.ai GTM research. Prioritizing findings F1 and F3, testing hypothesis H1, deciding on next research directions"
- **Content:** Human-AI conversation clarifying strategy, priority, next steps
- **Extraction expectation:** ResearchObjective, Hypothesis entities + INVESTIGATES, SUPPORTS edges + strategic metadata

**Type 3: Execution Log Episodes**
- **Name pattern:** `[Methodology_Name]_Implementation_[Date]`
- **Example:** `Clay_Workflow_Implementation_2025-01-20`
- **Description template:** "Implementation of Clay-to-Outreach workflow for Arthur.ai downmarket GTM. Testing hypothesis H1. Outcome: partial success with 40% conversion improvement"
- **Content:** Structured execution log with outcomes, metrics, lessons learned
- **Extraction expectation:** Implementation, Methodology entities + IMPLEMENTS, TESTS, INFORMS edges

**Type 4: Synthesis Episodes**
- **Name pattern:** `[Objective_Name]_Synthesis_[Date]`
- **Example:** `Arthur_GTM_Synthesis_2025-01-25`
- **Description template:** "Cross-worker synthesis of Arthur.ai GTM research. Validated hypotheses H1 and H2, identified methodology M1 as best approach, uncovered findings F1-F5"
- **Content:** LLM-generated synthesis across all research workers
- **Extraction expectation:** High-confidence Finding entities + all relationship types

### Episode Metadata for Retrieval

**Critical metadata fields:**
```python
episode_metadata = {
    "objective_id": "arthur_gtm_clay",  # Links to ResearchObjective
    "worker_type": "industry",  # academic, industry, tool, critical
    "session_phase": "discovery",  # discovery, validation, execution, synthesis
    "priority": "high",  # Surfaces in priority-filtered queries
    "validated": True,  # Execution-backed vs exploratory
    "hypothesis_ids": ["H1", "H2"],  # Explicit hypothesis linking
    "finding_ids": ["F1", "F3"],  # Explicit finding linking
}
```

**Retrieval impact:** When querying "Arthur.ai downmarket GTM strategy using Clay," Graphiti will:
1. **Match episode names semantically** (keyword overlap)
2. **Match descriptions** (contextual similarity) 
3. **Extract entities mentioned** (Company: Arthur.ai, Tool: Clay)
4. **Traverse relationships** (INVESTIGATES, ENABLES, IMPLEMENTS)
5. **Return aggregated context:** Facts about entities + strategic hypotheses + execution outcomes

## Encoding Strategy for Multi-Level Information

### Layer 1: Entity Facts (Direct Properties)

Store **stable, factual attributes** directly on entity nodes:
- Company revenue, employee count, tech stack
- Tool pricing, capabilities, integrations
- Market size, growth rate

**Example extraction from episode:**
```
"Arthur.ai is a Series B ML observability company with 50 employees, 
 targeting the enterprise ML market."
```
**Extracted:** Company(name="Arthur.ai", stage="Series B", employee_count=50)  
**Edge:** TARGETS(Market: "enterprise ML")

### Layer 2: Strategic Context (Relationship Properties + Abstract Entities)

Store **interpretation, priority, confidence** as relationship properties and explicit strategic entities:

**Example extraction from refinement episode:**
```
"Research objective 'Arthur.ai downmarket GTM' is investigating whether 
 hypothesis H1 'Clay enables faster ICP discovery' holds. Priority: high. 
 Initial findings suggest Clay's data enrichment capability strongly enables 
 this approach."
```

**Extracted entities:**
- ResearchObjective(name="Arthur.ai downmarket GTM", priority="high")
- Hypothesis(name="H1", statement="Clay enables faster ICP discovery", confidence=0.7)
- Capability(name="Clay data enrichment")

**Extracted edges:**
- ResearchObjective INVESTIGATES Company(Arthur.ai) [priority="high"]
- Hypothesis TESTS ResearchObjective
- Capability(Clay enrichment) ENABLES Methodology(ICP discovery)

### Layer 3: Execution Outcomes (Implementation Entities + Temporal Properties)

Store **validation results, lessons learned** as Implementation entities with temporal tracking:

**Example extraction from execution log:**
```
"Implementation 'Clay workflow Jan 2025' of the Clay-to-Outreach methodology 
 tested hypothesis H1. Result: 40% faster ICP building, validating the hypothesis. 
 Lesson: Requires data quality validation step."
```

**Extracted entities:**
- Implementation(name="Clay workflow Jan 2025", outcome="success", 
                metrics_achieved="40% faster ICP building", 
                executed_date="2025-01-20")

**Extracted edges:**
- Implementation IMPLEMENTS Methodology(Clay-to-Outreach)
- Implementation TESTS Hypothesis(H1) [validation_outcome="supports", evidence_strength=0.85]
- Implementation INFORMS ResearchObjective [insight_quality="high_confidence"]

### Cross-Layer Retrieval Pattern

**Query:** "Arthur.ai downmarket GTM strategy using Clay"

**Retrieval process:**
1. **Semantic search** on episode descriptions + entity names
   - Matches: ResearchObjective("Arthur.ai downmarket GTM"), Company(Arthur.ai), Tool(Clay)
   
2. **Graph traversal** (1-2 hops):
```cypher
MATCH (obj:ResearchObjective {name: "Arthur.ai downmarket GTM"})
MATCH (obj)-[r1:INVESTIGATES]->(target)
MATCH (obj)<-[:TESTS]-(hypothesis:Hypothesis)
MATCH (hypothesis)<-[r2:SUPPORTS|TESTS]-(evidence)
MATCH (method:Methodology)<-[:ENABLES]-(tool:Tool)
WHERE tool.name = "Clay"
MATCH (method)<-[:IMPLEMENTS]-(impl:Implementation)
RETURN obj, target, hypothesis, evidence, method, tool, impl
```

3. **Result aggregation:**
   - **Entity facts:** Arthur.ai attributes, Clay capabilities, market characteristics
   - **Strategic context:** Hypotheses being tested, research priority, findings supporting direction
   - **Execution guidance:** Validated methodologies, implementation lessons, success metrics

**Synthesized output format:**
```
ENTITY FACTS:
- Arthur.ai: Series B ML observability, 50 employees, targeting enterprise
- Clay: Data enrichment platform, usage-based pricing, strong API ecosystem

STRATEGIC CONTEXT:
- Research Objective: Arthur.ai downmarket GTM (Priority: HIGH)
- Hypothesis H1: "Clay enables faster ICP discovery" (Confidence: 0.85, Status: VALIDATED)
- Finding F1: "Downmarket requires self-serve onboarding" (Novelty: NOVEL, Actionability: IMMEDIATE)

EXECUTION GUIDANCE:
- Methodology: Clay-to-Outreach workflow (Maturity: PROVEN)
- Implementation Jan 2025: 40% faster ICP building, requires data quality validation
- Next action: Scale with automated data validation layer
```

## Implementation Approach Within Graphiti Constraints

### Phase 1: Agent Output Engineering (Week 1)

**Modify research agents to explicitly verbalize strategic concepts:**

```python
# Bad (won't extract strategic entities):
research_output = "We found that downmarket needs self-serve features"

# Good (explicitly names entities):
research_output = """
Finding F1 'Downmarket self-serve requirement' reveals that companies targeting 
downmarket segments require self-serve onboarding capabilities. This finding 
supports hypothesis H1 'Product-led growth critical for SMB' with high confidence.

Research objective 'Arthur.ai downmarket GTM' investigates whether Clay's 
data enrichment capability enables faster ICP discovery for companies like 
Arthur.ai targeting the downmarket ML segment.
"""
```

**Implementation checklist:**
- [ ] Add "strategic concept prompts" to research agent system prompts
- [ ] Template refinement conversations to explicitly state objectives and hypotheses
- [ ] Structure execution logs to name implementations and reference methodologies
- [ ] Include explicit entity mentions in episode descriptions

### Phase 2: Ontology Implementation (Week 1-2)

**Define custom Pydantic entity types:**
```python
from graphiti import Graphiti
from pydantic import BaseModel, Field

entity_types = [
    Company, Tool, Person, Market, Capability,  # Concrete
    ResearchObjective, Hypothesis, Methodology, Finding,  # Strategic
    Implementation  # Execution
]

edge_type_map = {
    ("ResearchObjective", "Company"): [Investigates],
    ("ResearchObjective", "Tool"): [Investigates],
    ("Hypothesis", "ResearchObjective"): [Tests],
    ("Finding", "Company"): [Reveals],
    ("Finding", "Hypothesis"): [Supports],
    ("Implementation", "Methodology"): [Implements],
    ("Implementation", "Hypothesis"): [Tests],
    ("Tool", "Methodology"): [Enables],
    ("Methodology", "Capability"): [Requires],
    # Default fallback for flexibility
    ("Entity", "Entity"): [GenericRelation]
}

graphiti = Graphiti(
    entity_types=entity_types,
    edge_type_map=edge_type_map
)
```

### Phase 3: Episode Structuring (Week 2)

**Implement episode metadata system:**
```python
async def ingest_research_session(
    objective_id: str,
    worker_type: str,
    research_content: str,
    hypothesis_ids: list[str],
    priority: str
):
    episode_name = f"{objective_id}_Research_{worker_type}_{date.today()}"
    
    episode_description = f"""
    {worker_type.title()} worker researching {objective_id}. 
    Testing hypotheses {', '.join(hypothesis_ids)}. 
    Priority: {priority}. Session phase: discovery.
    """
    
    await graphiti.add_episode(
        episode_body=research_content,
        episode_name=episode_name,
        episode_description=episode_description,
        reference_time=datetime.now(),
        entity_types=entity_types,
        edge_type_map=edge_type_map
    )
```

### Phase 4: Retrieval Pattern Development (Week 3)

**Implement hybrid retrieval:**
```python
async def retrieve_research_intelligence(query: str, top_k: int = 10):
    # Step 1: Semantic search on episodes
    episodes = await graphiti.search(
        query=query,
        num_results=top_k
    )
    
    # Step 2: Extract entity IDs from retrieved episodes
    entity_ids = extract_entities_from_episodes(episodes)
    
    # Step 3: Graph traversal for strategic context
    strategic_context = await graphiti.query(f"""
        MATCH (obj:ResearchObjective)-[r:INVESTIGATES]->(target)
        WHERE target.id IN {entity_ids}
        MATCH (obj)<-[:TESTS]-(hyp:Hypothesis)
        MATCH (hyp)<-[e:SUPPORTS|TESTS]-(evidence)
        RETURN obj, hyp, evidence, r.properties
    """)
    
    # Step 4: Retrieve execution outcomes
    executions = await graphiti.query(f"""
        MATCH (impl:Implementation)-[r:TESTS]->(hyp:Hypothesis)
        WHERE hyp.id IN {hypothesis_ids}
        RETURN impl, r.validation_outcome, r.evidence_strength
    """)
    
    # Step 5: Synthesize results
    return synthesize_intelligence(episodes, strategic_context, executions)
```

### Phase 5: Iterative Refinement (Ongoing)

**Monitor extraction quality:**
```python
# Check entity type distribution
entity_counts = await graphiti.query("""
    MATCH (n) 
    RETURN labels(n) as type, count(n) as count 
    ORDER BY count DESC
""")

# Validate strategic entity creation
strategic_entities = await graphiti.query("""
    MATCH (n) 
    WHERE n:ResearchObjective OR n:Hypothesis OR n:Finding
    RETURN n.name, n.created_at
    ORDER BY n.created_at DESC
    LIMIT 20
""")
```

**Adapt based on patterns:**
- If ResearchObjective extraction is low → Strengthen verbalization prompts
- If edges missing → Ensure relationship context in text
- If confidence scores absent → Add explicit confidence statements

## Trade-Offs and Limitations

### Constraint 1: Entity Mention Requirement

**Limitation:** Cannot create entities not mentioned in text  
**Impact:** Abstract concepts like "Strategic Intent" must be explicitly verbalized  
**Mitigation:** Engineer agent outputs to mention strategic concepts by name  
**Trade-off:** Slightly verbose research outputs vs. rich strategic graph

### Constraint 2: Relationship Extraction Accuracy

**Limitation:** LLM-based extraction may miss implicit relationships  
**Impact:** Important connections between concepts might not be captured  
**Mitigation:** 
- Use explicit relationship keywords ("supports," "tests," "enables")
- Include relationship statements in episode descriptions
- Validate critical relationships manually in refinement sessions  
**Trade-off:** Explicitness in writing vs. natural language flow

### Constraint 3: Temporal Granularity

**Limitation:** Graphiti's bi-temporal model tracks validity but not fine-grained execution phases  
**Impact:** Difficult to distinguish "exploring," "validating," "implementing" phases for same hypothesis  
**Mitigation:** Use episode metadata (session_phase field) and Implementation entity status fields  
**Trade-off:** Some temporal semantics in metadata vs. graph structure

### Constraint 4: Confidence Propagation

**Limitation:** No built-in confidence propagation across graph relationships  
**Impact:** Cannot automatically compute aggregate confidence for multi-hop reasoning  
**Mitigation:** Store confidence scores on entities and relationships, compute at retrieval time  
**Trade-off:** Additional retrieval-time computation vs. static confidence

### Constraint 5: Meta-Entity Prohibition

**Limitation:** Cannot create "ResearchFinding" as container node with properties  
**Impact:** Findings must be first-class entities, increasing node count  
**Mitigation:** Use Finding entity type with rich properties; use episodes as implicit containers  
**Trade-off:** Larger graph vs. semantic precision

### Constraint 6: Community Detection Overhead

**Limitation:** Hierarchical clustering (Leiden algorithm) requires periodic recomputation  
**Impact:** Community summaries may lag behind latest additions  
**Mitigation:** Schedule community refresh after major research sessions (e.g., daily)  
**Trade-off:** Computation cost vs. global query accuracy

## Alternative Approaches Considered

### Alternative 1: Observation-Based Pattern

**Approach:** Model all findings as Observation entities linking to concrete entities  
**Pattern:** `(:Observation)-[:ABOUT]->(:Company)` instead of direct properties  
**Pros:** Clear separation between facts and interpretations; easier provenance tracking  
**Cons:** Extra hop in queries; more verbose for simple facts  
**Decision:** Hybrid approach—direct properties for stable facts, Finding entities for insights

### Alternative 2: Fully Schema-Free

**Approach:** No custom entity types, rely on LLM to generate all types dynamically  
**Pattern:** Let Graphiti extract whatever it finds  
**Pros:** Maximum flexibility; no upfront ontology design  
**Cons:** Inconsistent entity naming; difficult to structure retrieval; poor for strategic concepts  
**Decision:** Custom types for core entities to enforce structure while allowing "Other" types

### Alternative 3: Episode-Centric Retrieval Only

**Approach:** Store all context in episodes, minimal graph structure  
**Pattern:** Rely on episode semantic search, light graph augmentation  
**Pros:** Simpler implementation; leverages Graphiti's episode indexing  
**Cons:** Loses relationship reasoning; cannot answer "what enables what" queries  
**Decision:** Prioritize graph relationships for strategic reasoning, episodes for context

### Alternative 4: Separate Strategic Knowledge Base

**Approach:** Store strategic context (hypotheses, priorities) outside Graphiti in separate DB  
**Pattern:** Graphiti for entities/facts, PostgreSQL for strategies  
**Pros:** No verbalization constraints; structured strategy management  
**Cons:** Loses unified retrieval; separate sync logic; no temporal consistency  
**Decision:** Keep unified KG for coherent retrieval and temporal reasoning

## Production Knowledge Graph Examples Summary

Based on research, successful production systems demonstrate these patterns:

**Microsoft GraphRAG:** Hierarchical community detection enables both local (entity-specific) and global (dataset-wide) queries—consider implementing community refresh for high-level strategic summaries.

**LightRAG:** Dual-level retrieval (specific entities vs. global themes) via keyword extraction—adapt by distinguishing tactical queries (specific company/tool facts) from strategic queries (market trends, methodology patterns).

**GTM Intelligence (Wyzard, CaliberMind):** Intent signals as first-class entities with temporal tracking—map to your Finding entities with validation_status and confidence scores.

**SciAgents:** Multi-agent collaboration through shared KG where each agent writes explicitly tagged contributions—directly applicable to your 4-worker system with worker_type tagging.

**RNA-KG / ITO:** Formal ontology with strict relationship constraints for regulated domains—your research domain allows more flexibility, use hybrid (core types + flexible relationships).

## Recommended Next Steps

**Week 1: Foundation**
1. Implement 10 custom entity types in Pydantic
2. Define edge type mappings for 11 core relationships
3. Create episode naming and description templates
4. Modify one research agent to verbalize strategic concepts

**Week 2: Integration**
1. Integrate custom types into Graphiti initialization
2. Build episode ingestion pipeline with metadata
3. Test extraction quality on sample research sessions
4. Validate strategic entity creation (ResearchObjective, Hypothesis, Finding)

**Week 3: Retrieval**
1. Implement hybrid retrieval (episode search + graph traversal)
2. Build synthesis function to aggregate entity facts + strategic context + execution outcomes
3. Create query templates for common intelligence needs
4. Test end-to-end: query → retrieval → synthesized intelligence

**Week 4: Refinement**
1. Monitor entity type distribution and relationship coverage
2. Adjust verbalization prompts based on extraction gaps
3. Implement confidence propagation in retrieval layer
4. Schedule community detection refresh strategy

**Ongoing: Evolution**
- Add new entity types as research patterns emerge
- Refine relationship types based on query needs
- Optimize episode descriptions for retrieval accuracy
- Build autonomous agent query interfaces

## Conclusion

This ontology balances Graphiti's NER constraints with research intelligence requirements through **deliberate verbalization of strategic concepts**. By engineering research agent outputs to explicitly mention ResearchObjectives, Hypotheses, Findings, and Methodologies, you create extractable entities while maintaining natural semantic richness.

The three-layer architecture—concrete entities with facts, strategic entities with context, execution entities with outcomes—enables retrieval queries to return **woven intelligence** rather than separated fact buckets. Episode metadata and relationship properties carry semantic weight, while Graphiti's temporal model tracks knowledge evolution across research sessions.

Your closed system advantage means you control what gets written into episodes. Use this to create a **self-optimizing research intelligence loop:** agents write strategically structured outputs → Graphiti extracts rich graph → queries return actionable intelligence → execution outcomes feed back → refined strategies emerge. This creates a living knowledge graph that becomes more valuable with each research session.

The constraint becomes the design: by grounding abstractions in text, you ensure every strategic concept has evidentiary backing, every hypothesis links to specific findings, and every methodology connects to concrete execution outcomes. This produces not just a knowledge graph, but an **execution intelligence system** where facts, strategy, and validation are inseparably woven together.