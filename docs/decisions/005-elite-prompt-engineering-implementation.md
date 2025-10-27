# ADR 005: Elite Prompt Engineering Implementation

**Date**: 2025-01-26
**Status**: Implemented
**Context**: Two-stage research architecture with Anthropic best practices

---

## Summary

Implemented two-stage research architecture with elite prompt engineering following Anthropic's 2025 best practices. This separates research quality from extraction precision, using specialized LLMs for each stage.

---

## Architecture

### Stage 1: Research LLMs (Natural Prose)
**Purpose**: Maximize insight quality without extraction constraints

**Workers**:
- Academic Researcher (deep literature, theoretical frameworks)
- Industry Analyst (real-world implementations, competitive intelligence)
- Tool Analyzer (technical evaluation, trade-off analysis)
- Critical Analyst (reviews all workers, filters noise)

**Model**: Claude Sonnet 4.5 (best quality for research)
**Output**: Natural prose saved as `{worker}_raw.txt`

### Stage 2: Structuring LLM (Graph-Optimized Format)
**Purpose**: Transform natural research into graph-ready format

**Process**: Reads raw research → adds entity markers → adds relationship declarations
**Model**: Claude Haiku 4.5 (cost-effective for structured tasks)
**Output**: Verbalized format saved as `{worker}.txt` → fed to Graphiti

---

## Prompt Engineering Techniques Applied

### From Anthropic Best Practices (2025)

**1. XML Tags for Structure**
```xml
<role>You are a world-class academic researcher...</role>
<task>Conduct deep research...</task>
<methodology>1. Cast a wide net... 2. Seek contradictory evidence...</methodology>
<examples><example><good>...</good><bad>...</bad></example></examples>
```

**Why**: Claude was trained to pay special attention to XML structure. Tags act as signposts that separate instructions, examples, and context.

**2. Role-Based Prompting**
```
You are a world-class academic researcher with expertise in discovering
cutting-edge insights from peer-reviewed literature.

Your specialty: Finding signal in academic noise—identifying the 10%
of research that matters for strategic decisions.
```

**Why**: Precise personas guide tone and depth, helping Claude focus on relevant expertise.

**3. Few-Shot Examples**
```xml
<examples>
<example>
<good>
**Key finding:** Cross-domain analysis of 47 SaaS companies...
</good>
<bad>
Some research suggests PLG might help reduce costs...
</bad>
</example>
</examples>
```

**Why**: Showing Claude a clear example makes a significant difference, especially for nuanced or stylistic tasks.

**4. Chain-of-Thought Reasoning**
```xml
<methodology>
Think step by step:
1. Read all three worker outputs carefully
2. For each major claim, ask: "What's the evidence? Is it rigorous?"
3. Look for contradictions between workers...
</methodology>
```

**Why**: Telling Claude to think step-by-step produces more accurate responses for complex reasoning tasks.

**5. Explicit Task Decomposition**
```
Your goals:
1. Score relevance (1-10): Does this actually answer the research query?
2. Filter noise: Cut fluff, marketing speak, and low-signal observations
3. Challenge evidence: Flag weak citations, unsupported claims
4. Identify gaps: What's missing?
5. Synthesize patterns: Where do findings converge?
```

**Why**: Breaking down complex tasks into clear subtasks improves execution quality.

**6. Output Format Specification**
```xml
<output_format>
Structure naturally with clear headers. Use these sections:

## Relevance Scores
- Academic Research: [1-10]/10 - [one sentence why]
...

## Signal Extraction (Top Insights)
[The 10% that truly matters]
</output_format>
```

**Why**: Clear output structure ensures consistency and makes results easier to parse.

**7. Context Engineering (High Signal-to-Noise)**
- Every sentence in the prompt serves a purpose
- No fluff or redundant instructions
- Examples show patterns rather than describe them abstractly
- Critical rules highlighted explicitly

**Why**: LLMs have finite attention budget—maximize signal, minimize noise.

---

## Prompt Architecture

### Research Prompts (Stage 1)

**Structure**:
1. `<role>` - Define expertise and specialty
2. `<task>` - Explain why this research matters (strategic context)
3. `<methodology>` - Step-by-step research approach
4. `<output_format>` - Natural prose with helpful markers (not constraints)
5. `<examples>` - Show good vs. bad research output
6. `<tone>` - Set writing style and rigor level
7. `<critical_rule>` - One key principle (DEPTH > BREADTH)

**Key Design Choices**:
- Emphasis on **natural prose** - no extraction constraints
- Strategic context provided (why research matters → motivates quality)
- Examples show **what** quality looks like (concrete > abstract)
- Critical rule anchors the entire prompt (depth over breadth)

### Structuring Prompt (Stage 2)

**Structure**:
1. `<role>` - Ontology specialist expertise
2. `<task>` - Transform research without losing insights
3. `<context>` - Explain NER limitations and why structuring is needed
4. `<entity_naming_rules>` - Explicit format for each entity type
5. `<relationship_rules>` - Explicit format for each relationship type
6. `<domain_entities>` - What already extracts well (no changes needed)
7. `<critical_rules>` - PRESERVE ALL INSIGHTS (non-negotiable)
8. `<examples>` - Show before/after transformation

**Key Design Choices**:
- Explain **why** transformation is needed (NER limitations)
- Show **exact format** for each entity type (reduces ambiguity)
- Multiple examples of input → output (pattern demonstration)
- Critical rule: **preservation** > compression (never lose insights)

---

## Cost Analysis

### Per Research Session (3 workers + critical analyst)

**Stage 1: Research (Natural Prose)**
- 3 workers × 3,000 tokens avg × $15/1M tokens = $0.135
- Critical analyst × 1,500 tokens × $15/1M tokens = $0.0225
- **Stage 1 total: $0.1575**

**Stage 2: Structuring (Graph-Optimized)**
- 3 workers × 3,500 tokens avg × $1/1M tokens = $0.0105
- **Stage 2 total: $0.0105**

**Total per research: ~$0.17** (was $0.15 single-stage)

**Cost increase: 13% for massive quality gain**

---

## Quality Improvements

### What We Gain

**Research Quality**:
- ✅ No cognitive load from formatting constraints
- ✅ Research LLMs focus purely on insight quality
- ✅ Natural prose enables better web search queries
- ✅ Critical analyst sees natural research (better review quality)

**Extraction Precision**:
- ✅ Structuring LLM specialized for entity extraction
- ✅ Can validate structuring separately from research
- ✅ Can re-run structuring without re-doing expensive research
- ✅ Explicit examples reduce ambiguity in entity formatting

**Debugging**:
- ✅ Have both raw and structured versions
- ✅ Can compare to see if structuring lost information
- ✅ Can iterate on structuring prompt without burning research credits
- ✅ Can A/B test different structuring strategies

---

## File Structure

```
workers/
├── research.py         # Two-stage execution logic
└── prompts.py          # Elite optimized prompts (600+ lines)
    ├── ACADEMIC_RESEARCHER_PROMPT
    ├── INDUSTRY_ANALYST_PROMPT
    ├── TOOL_ANALYZER_PROMPT
    ├── STRUCTURING_PROMPT_TEMPLATE
    └── CRITICAL_ANALYST_PROMPT

context/
└── {Session_Name}/
    ├── academic_researcher_raw.txt      # Stage 1 output (natural prose)
    ├── academic_researcher.txt          # Stage 2 output (graph-ready)
    ├── industry_intelligence_raw.txt
    ├── industry_intelligence.txt
    ├── tool_analyzer_raw.txt
    ├── tool_analyzer.txt
    └── critical_analysis.txt
```

---

## Usage

### Normal Research Flow
```python
# Automatically runs both stages
worker_results, critical_analysis = execute_research(
    query="Arthur.ai downmarket GTM strategy",
    tasking_summary=tasking_context,
    research_dir="context/Session_Name"
)
# Returns structured results ready for Graphiti ingestion
```

### Outputs
- **Raw research**: `{worker}_raw.txt` (natural prose)
- **Structured research**: `{worker}.txt` (graph-ready)
- **What gets ingested**: Structured version (graph-optimized)

---

## Validation

### How to Test Quality

**Research Quality (Stage 1)**:
- Read `academic_researcher_raw.txt`
- Check: Depth of insights, citation quality, evidence rigor
- Compare to previous research outputs (should be noticeably better)

**Structuring Quality (Stage 2)**:
- Read `academic_researcher.txt`
- Check: All insights preserved? Entity markers correct? Relationships explicit?
- Compare raw vs. structured (should have MORE content, not less)

**Extraction Quality (Graph)**:
- Run Graphiti ingestion on structured output
- Query Neo4j for extracted entities
- Check: Do strategic entities (Finding, Hypothesis, Implementation) extract?

---

## Best Practices for Prompt Maintenance

### When to Update Prompts

**Research Prompts**:
- When research quality drops (users report low-signal findings)
- When adding new research methodologies
- When strategic context changes (new goals, different use cases)

**Structuring Prompt**:
- When entity extraction fails (entities not extracting correctly)
- When adding new entity types to ontology
- When relationship patterns change

### How to Update

1. **Test in isolation**: Create test file, run single worker
2. **Compare outputs**: Check before/after quality
3. **Validate extraction**: Run through Graphiti, check Neo4j
4. **Document changes**: Update this ADR with rationale

### Prompt Version Control

All prompts live in `workers/prompts.py`:
- ✅ Version controlled via git
- ✅ Easy to see prompt history (git log)
- ✅ Can revert if quality drops
- ✅ Can A/B test by creating branches

---

## References

- **Anthropic Best Practices (2025)**: XML tags, role prompting, few-shot examples, chain-of-thought
- **Context Engineering**: High signal-to-noise ratio, finite attention budget
- **ADR 004**: Graphiti extraction findings (why verbalization is needed)
- **Prompt Engineering Research**: Task decomposition, explicit output formats

---

## Refinement Distillation (THE GOLD)

### Why This Matters More Than Research

Refinement context is **weighted higher** than research findings because:
- Research findings = data (what exists)
- Refinement context = interpretation (how to use it)
- Without refinement context, research is information
- With refinement context, research becomes actionable intelligence

### Elite Prompt Design

The refinement distillation prompt (`REFINEMENT_DISTILLATION_PROMPT`) uses all Anthropic best practices:

**1. Strategic Framing**
- Role: "Strategic context archaeologist" (not generic distiller)
- Task: Extract the 20% with 80% of value (Pareto principle explicit)
- Context: THIS IS THE GOLD (makes importance explicit)

**2. Extraction Framework**
Five explicit categories with examples:
- Mental Models (how user frames problems)
- Reframings (corrections and redirections)
- Constraints (hard boundaries)
- Priorities (hierarchy of what matters)
- Synthesis Instructions (how to interpret research)

**3. Few-Shot Examples**
Three detailed examples showing:
- Mental model extraction (pipeline framing)
- Reframing extraction (NER constraint design)
- Constraint extraction (100% insight preservation)

Each example shows: conversation snippet → distilled output (pattern demonstration)

**4. Graph Optimization Rules**
Explicit instructions for NER extraction:
- Use entity names (not "it"/"they")
- Complete sentences with subject-verb-object
- Relational language ("connects to", "enables", "requires")
- Specific references (name tools, companies explicitly)

**5. Output Format Specification**
Structured sections with clear requirements:
- Mental Models
- Reframings
- Constraints
- Priorities
- Synthesis Instructions

### Implementation

**File**: [utils/files.py](utils/files.py) - `distill_conversation()` function
**Prompt**: [workers/prompts.py](workers/prompts.py) - `REFINEMENT_DISTILLATION_PROMPT`
**Model**: Claude Sonnet 4.5 (excellent at structured extraction)
**Tokens**: 3,000 max (increased from 2,000 for detail)
**Temperature**: 0.3 (factual extraction, not creative)

### Cost

**Per refinement distillation**: ~$0.005-0.015
- Input: 1,000-2,000 tokens (conversation)
- Output: 500-1,500 tokens (distilled gold)
- Model: Sonnet 4.5 ($3/1M input, $15/1M output)

Negligible cost for extracting THE GOLD.

---

**Status**: Ready for production use
**Next**: Test with real research query, validate extraction quality
