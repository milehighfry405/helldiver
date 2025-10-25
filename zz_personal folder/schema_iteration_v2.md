# Schema Iteration v2: Execution Research Support

**Date**: 2025-10-21  
**Purpose**: Expand ResearchFinding entity to support execution knowledge and update worker prompts accordingly  
**Type**: ITERATION (not a rewrite - we're modifying the existing implementation)

---

## What's Changing

### 1. ResearchFinding Entity - Expand `finding_type` Enum

**Current implementation:**
```python
class ResearchFinding(BaseModel):
    """Insight discovered through research."""
    topic: str
    finding_type: str  # technical_spec | limitation | best_practice | strategic_insight | competitive_analysis
    content_summary: str
    source_type: str
    confidence: str
    session_name: str
```

**Updated implementation:**
```python
class ResearchFinding(BaseModel):
    """Insight discovered through research."""
    topic: str
    finding_type: str  # EXPANDED - see below
    content_summary: str
    source_type: str
    confidence: str
    session_name: str
```

**New `finding_type` values:**

**Strategic Research (keep existing):**
- `strategic_insight` - Market trends, competitive positioning
- `competitive_analysis` - How competitors operate
- `best_practice` - General principles and proven approaches
- `limitation` - Constraints, blockers, what doesn't work

**Execution Research (NEW):**
- `workflow_guide` - Step-by-step processes and procedures
- `technical_spec` - API capabilities, tool features, what's possible (keep this one)
- `configuration_spec` - Specific settings, parameters, values to use
- `prompt_template` - Prompts that work for specific use cases
- `integration_pattern` - How to connect multiple tools together
- `troubleshooting_guide` - Common issues, errors, and solutions
- `data_schema` - Data structures, field mappings, table designs

---

### 2. Worker Prompt Updates

**What stays the same:**
- All 4 structural hints from v1 (headers, consistent terminology, full names, etc.)
- Focus on depth and quality

**What's being added:**
- Type-specific formatting guidelines to help Graphiti extraction identify finding types
- Breadcrumbs for execution knowledge

---

## Updated Worker Prompts

### System Prompt Addition for All 4 Workers

**Location**: Add to the system prompt for Academic, Industry, Tool, and Critical workers

**Content:**
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

   **For step-by-step processes (workflow guides):**
   - Use numbered steps: "Step 1:", "Step 2:", etc.
   - Or use explicit workflow language: "First, then, next, finally"
   - Example: "Workflow: Setting up Clay enrichment"

   **For configuration settings:**
   - Use consistent format: "Setting: value" or "Parameter: value"
   - Group related settings together
   - Example: "Configuration: Rate limit: 100/hour, Timeout: 30s"

   **For prompt templates:**
   - Clearly label as prompts
   - Show the exact prompt text
   - Include context about when to use it
   - Example: "Prompt for Clay personalization: 'Based on {{company_info}}, write...'"

   **For integrations between tools:**
   - Describe the data flow
   - Show what connects to what
   - Example: "Integration: Clay → Webhook → Slack"

   **For troubleshooting:**
   - State the problem clearly
   - Provide the solution
   - Example: "Error: Rate limit exceeded. Solution: Implement exponential backoff"

   **For data structures:**
   - Show field names and types
   - Describe relationships
   - Example: "Table schema: company_name (text), employee_count (integer)"

Focus on DEPTH and QUALITY of research. These are structural hints, not constraints.
```

---

## Implementation Instructions for Claude Code

### Step 1: Update ResearchFinding Pydantic Model

**File**: Wherever the ResearchFinding model is defined (likely in your schema definitions)

**Action**: Update the docstring/comment for `finding_type` field to reflect the expanded enum

**Before:**
```python
finding_type: str  # technical_spec | limitation | best_practice | strategic_insight | competitive_analysis
```

**After:**
```python
finding_type: str  # strategic_insight | competitive_analysis | best_practice | limitation | workflow_guide | technical_spec | configuration_spec | prompt_template | integration_pattern | troubleshooting_guide | data_schema
```

**Note**: You don't need to enforce these as actual enum constraints in Pydantic. Graphiti's LLM will extract the appropriate type based on the content and these hints. The comment is for documentation.

---

### Step 2: Update Worker System Prompts

**Files**: Wherever the 4 worker system prompts are defined (Academic, Industry, Tool, Critical)

**Action**: Replace the existing "Worker Prompt Improvements" section with the expanded version above (Section 5 is new)

**What to look for:**
- Existing prompts should have 4 numbered items about formatting
- You're adding a 5th item with sub-bullets for execution knowledge formatting

**What NOT to change:**
- Don't modify the core worker personas/instructions
- Don't change the research quality guidelines
- Only update the "structural hints" section

---

### Step 3: Update Documentation

**File**: `schema.md`

**Action**: Update two sections:

1. **ResearchFinding entity definition** - Update the `finding_type` comment
2. **Worker Prompt Improvements section** - Replace with the expanded version from this document

---

### Step 4: No Other Changes Needed

**What stays exactly the same:**
- All other entity definitions (StrategicIntent, ExecutionOutcome, Company, Tool, Methodology)
- The entity_types dictionary structure
- How add_episode() is called
- The entity type matrix (which types for which episodes)
- All protected field names
- Usage examples
- Implementation checklist

---

## Why These Changes Matter

**Problem without execution types:**
- "How to set up Clay tables" produces findings all labeled as "technical_spec"
- Execution agents must read ALL findings to determine which are workflows vs. configs vs. prompts
- Inefficient and token-heavy

**Solution with execution types:**
- Agents can filter: "Give me workflow_guide findings for Clay tables"
- Then: "Give me configuration_spec findings for Clay enrichment"
- Then: "Give me prompt_template findings for Clay personalization"
- Precise retrieval = better execution

**The worker prompt updates:**
- Help Graphiti's extraction LLM correctly identify finding types
- Without these breadcrumbs, all execution knowledge might get lumped into "technical_spec"
- With breadcrumbs, extraction is more accurate and findings are properly categorized

---

## Testing After Implementation

1. Run a research session focused on execution (e.g., "How to use Clay for enrichment")
2. Commit to Graphiti
3. Query Neo4j to verify finding types:
   ```cypher
   MATCH (e:Entity:ResearchFinding)
   RETURN e.finding_type, count(*) as count
   ORDER BY count DESC
   ```
4. You should see distribution across the new types (workflow_guide, configuration_spec, etc.)
5. Test filtering in search:
   ```python
   results = await graphiti.search(
       query="Clay table setup",
       filters=SearchFilters(
           labels=["ResearchFinding"],
           # Note: May need to verify exact filter syntax for custom attributes
       )
   )
   ```

---

## Summary of Changes

| Component | Change Type | Description |
|-----------|-------------|-------------|
| ResearchFinding.finding_type | EXPAND | Add 6 new execution-focused values |
| Worker prompts (all 4) | ADD | New section 5 for execution formatting hints |
| schema.md | UPDATE | Reflect expanded finding_type and new prompts |
| Everything else | NO CHANGE | All other entities, structure, implementation stays the same |

---

**Ready for implementation. This is a targeted iteration, not a rewrite.**
