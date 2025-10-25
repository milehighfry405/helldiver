# Current Work Tracker

> **New to this project?** Read `CLAUDE.md` first, then come back here.

**Last Updated**: 2025-01-24
**Active Sessions**: Schema redesign needed after Graphiti architecture investigation

---

## 🎯 Active Focus

**Paused: Redesigning entity schema to align with Graphiti's NER architecture**

**What happened**: Attempted to implement custom entity types (ResearchFinding, StrategicIntent, ExecutionOutcome) but discovered Graphiti is designed for Named Entity Recognition (concrete nouns mentioned in text), not conceptual entity extraction (structure of content itself).

**Current blocker**: Meta-entities fail to extract properly - they create generic `Entity` nodes instead of typed nodes with attributes.

**Next step**: Redesign schema to use only concrete entity types that represent things mentioned in text, not abstract concepts.

---

## 📋 What We Just Figured Out

### Graphiti Extraction Architecture Investigation (2025-01-24)
- **Problem**: Custom entity types (ResearchFinding, StrategicIntent, ExecutionOutcome) don't extract - they create generic Entity nodes
- **Root Cause Discovered**: Graphiti uses Named Entity Recognition (NER) designed for concrete nouns mentioned in text ("Arthur.ai", "Clay"), not conceptual entities that ARE the text structure itself
- **Deep Investigation**: 8-point analysis of Graphiti's extraction pipeline revealed:
  - Two-stage extraction: (1) Extract entity names, (2) Extract attributes for named entities
  - ResearchFinding has no "name" mentioned in text - it's the paragraph structure itself
  - Graphiti makes 17+ LLM calls per episode (1 extraction + 1 reflexion + 15 attribute calls)
  - `custom_prompt` parameter exists but is NOT accessible via `add_episode()` - only used internally for reflexion retries
  - Entity type filtering IS supported and recommended (saves 65% token overhead)
- **Fixes Applied This Session**:
  - ✅ Fixed protected field conflicts: `name` → `company_name`, `tool_name`, `methodology_name`
  - ✅ Changed group_id to single global `"helldiver_research"` (enables cross-session synthesis)
  - ✅ Added `entity_types` parameter to all `add_episode()` calls
  - ✅ Enhanced worker prompts with execution formatting hints (5th guideline for workflow/config/prompt extraction)
  - ✅ Added `--commit-to-graph` CLI flag for retroactive commits when graph commits fail
  - ✅ Fixed async close() warning in graph client
- **Solutions Explored**:
  1. Fork Graphiti and modify extraction prompts (complex, high risk - deduplication issues)
  2. Hybrid JSON approach (append extracted findings as JSON to episode body)
  3. Dual storage (Graphiti for concrete entities, separate system for findings)
  4. Custom extractor hooks (not supported by Graphiti)
- **Decision**: Pause implementation, redesign schema to work WITH Graphiti's NER paradigm (use only concrete entity types)
- **Impact**: Need to rethink how we capture research intelligence - can't use meta-entities as nodes
- **Files Created**: `graph/entity_types.py` (ready but won't work as designed)
- **Files Modified**: `graph/client.py`, `core/research_cycle.py`, `workers/research.py`, `main.py`

### Codebase Refactoring (2025-01-20)
- **Problem**: Bloated 2,228-line main.py with duplicate code for initial vs deep research, bugs from code drift
- **Solution**: Systematic migration to modular architecture with unified research cycle
- **Results**:
  - 56% line reduction (2,228 → 440 lines in main.py)
  - Unified research cycle works for all research types (initial, deep, future)
  - Fixed conversation history capture bugs (tasking and refinement conversations now complete)
  - Episode name generation uses LLM to clean conversational queries
  - Batch API with 30-second progress polling preserved
  - All prompts identical to old code (no behavior changes)
- **Architecture**:
  - `core/session.py` - Session state management
  - `core/research_cycle.py` - Unified research execution
  - `workers/research.py` - Batch API for 3 workers + critical analyst
  - `graph/client.py` - Graph commits with connection handling
  - `utils/files.py` - File I/O and conversation distillation
- **Fixes Applied**:
  - Subfolder names use clean episode names (not raw queries)
  - Tasking conversation captures final user message before "go"
  - Refinement conversation captures deep research request (excludes confirmation)
  - Initial research uses episode_name for graph group_id
- **Files Archived**: `docs/archive/refactoring-2025-01-20/` contains complete old codebase:
  - `main_old.py` - Original 2,228-line monolithic version
  - `graphiti_client.py` - Old graph client (now graph/client.py)
  - `helldiver_agent.py` - Very old version (pre-main.py era)
  - `setup_neo4j.cypher` - Manual index setup (now automatic)
  - `test_refactor.py` - Validation test (no longer needed)
  - `README.md` - Explains what each file was and why archived
  - **Use case**: If questions arise about how something worked before refactoring, search these archived files
- **Impact**: Codebase is maintainable, bugs fixed, ready for production use

### Plugin-Based Documentation System (2025-01-19)
- **Problem**: Manual documentation updates, context lost between sessions, copy/paste session summaries
- **Solution**: Claude Code plugins for automated workflows
- **Implemented**:
  - `/onboard` - Loads context in <30 seconds (CLAUDE.md + CURRENT_WORK + git log + latest session)
  - `/commit` - Asks "why?", updates appropriate docs automatically, writes rich commit messages
  - `/session-end` - Extracts conversation context, generates comprehensive summary, commits automatically
- **Impact**:
  - Context loading: 3 minutes → <30 seconds
  - Documentation updates: manual → automatic
  - Session summaries: copy/paste → auto-committed
  - Multi-computer workflow: seamless (git pull + /onboard)
- **Files**:
  - Created: CLAUDE.md, .claude/plugin.json, .claude/commands/[onboard|commit|session-end].md
  - Archived: docs/AI_ONBOARDING.md, docs/COMMIT_CHECKLIST.md, docs/Claude Sessions/
  - Updated: README.md (plugin workflows), CURRENT_WORK.md (this file)

### Group ID Strategy (Under Review)
- **Issue Discovered**: Hierarchical group_ids (per-session) break cross-session querying via MCP
- **Root Cause**: Graphiti MCP requires explicit group_id filtering (no wildcards)
- **Options Identified**:
  - Option 1: Single global `helldiver_research` (enables omega context, recommended)
  - Option 2: Keep hierarchical, manually pass all group_ids in searches
- **Decision Status**: ⏸️ DEFERRED - Completing custom entities research first
- **Documented In**: [GRAPH_ARCHITECTURE.md](GRAPH_ARCHITECTURE.md) - Group ID Strategy section

### Critical Bugs Fixed (2025-01-19)
- ✅ Timezone-aware datetime (episodes now have valid_at timestamps for MCP search)
- ✅ Deep research episode naming (correct topic names instead of initial session name)
- ✅ OpenAI rate limit retry logic (progressive backoff: 2s, 4s, 6s)
- ✅ Retroactive commit metadata saving (session.json now updates after commits)
- ✅ MCP compatibility validated (Claude Desktop can find and search episodes)

---

## 🔬 Active Research Sessions

### 1. Custom Entities for Graphiti Knowledge Graphs
- **Status**: In Progress - Refinement phase
- **Episodes Committed**: 4 initial research episodes (✅ in Neo4j with correct valid_at)
- **Next Step**: Continue refinement conversation to determine custom entity schema
- **Key Question**: Should we use custom entities? If so, which types and attributes?
- **Location**: `context/Custom_entities_for_Graphiti_knowledge_graphs/`

### 2. Knowledge Graph Schema Design Principles
- **Status**: Deep research attempted (partial commit due to rate limits)
- **Episodes Committed**: 2 of 4 (Academic, Industry committed; Tool, Critical failed)
- **Next Step**: Retry commit with new rate limit logic to get remaining 2 episodes
- **Key Question**: Information-driven vs query-driven schema design?
- **Location**: Deep research within Custom Entities session

### 3. General Graph Architecture Research
- **Status**: Ongoing (synthesis of above sessions)
- **Purpose**: Inform final decisions on group_id, schema, custom entities
- **Output**: Will update [GRAPH_ARCHITECTURE.md](GRAPH_ARCHITECTURE.md) with final decisions

---

## 📍 Immediate Next Steps (In Order)

1. **Complete Custom Entities Research**
   - Continue refinement conversation in Helldiver agent
   - Land on: Do we use custom entities? Which types? What attributes?
   - Update [GRAPH_ARCHITECTURE.md](GRAPH_ARCHITECTURE.md) with decision

2. **Decide Group ID Strategy**
   - Based on custom entities decision
   - Choose: Single global "helldiver_research" vs hierarchical
   - Update [GRAPH_ARCHITECTURE.md](GRAPH_ARCHITECTURE.md) with decision
   - Update code if changing from current hierarchical approach

3. **Finalize Graph Schema**
   - Document final schema in [GRAPH_ARCHITECTURE.md](GRAPH_ARCHITECTURE.md)
   - Create ADR-004 if schema is complex enough to warrant detailed rationale

4. **Wipe and Re-commit All Research** (if group_id strategy changes)
   - Delete all existing episodes from Neo4j
   - Re-commit with new group_id strategy
   - Validate MCP search works as expected

5. **Plan Claude Skills Integration**
   - Design how skills will query the graph
   - Document in [GRAPH_ARCHITECTURE.md](GRAPH_ARCHITECTURE.md) - Integration Points section

---

## ❓ Open Questions

### High Priority
- [ ] **Custom entities**: Use them? Which types? (ResearchFinding, Critique, Hypothesis?)
- [ ] **Custom entity attributes**: confidence_level? source_quality? strategic_relevance?
- [ ] **Group ID strategy**: Single global vs hierarchical?
- [ ] **Schema rigidity**: How much flexibility vs structure?

### Medium Priority
- [ ] **Claude Skills integration pattern**: How should skills query the graph?
- [ ] **Performance targets**: What's acceptable query latency for execution agents?
- [ ] **Schema evolution**: How to handle changes as research evolves?

### Future Considerations
- [ ] **Multi-agent coordination**: How will other agents use this graph?
- [ ] **Execution result ingestion**: How to write skill execution results back to graph?
- [ ] **Cross-session synthesis**: How to surface insights across research topics?

---

## 🚫 What We're NOT Working On Right Now

- Building features for the Helldiver agent (architecture is stable)
- Optimizing batch API usage (working fine)
- Refactoring existing code (no tech debt issues)
- Documentation cleanup beyond this session's changes

**Focus**: Graph architecture research and decisions only

---

## 🎓 Key Learnings This Session

1. **Plugins > instructions for repetitive workflows** - Explicit triggers (/onboard, /commit) more reliable than hoping AI reads instructions
2. **Session summaries capture journey, not just outcome** - Git log shows final state; summaries show the debugging odyssey
3. **Every file needs explicit purpose** - No stale docs; each file actively updated or archived
4. **"Why" question in /commit is gold** - User's explanation captures context git diff can't show
5. **Graphiti's group_id is optional** - Default behavior searches entire graph (supports omega context vision)
6. **Enterprise use ≠ our use** - Zep uses per-user isolation; we want cross-session synthesis
7. **Episode size matters** - 1,000-2,000 tokens optimal for entity extraction (our chunking is correct)
8. **Timezone-aware datetimes are critical** - Naive datetimes → NULL valid_at → MCP can't find episodes
9. **MCP compatibility requires planning** - Can't assume other AI agents will "just work" without correct metadata
10. **Graphiti is NER, not conceptual extraction** - Designed for concrete nouns ("Arthur.ai"), not abstract concepts (ResearchFinding)
11. **Two-stage extraction has implications** - Entity names extracted first, attributes second - conceptual entities have no "name" to extract
12. **Protected fields exist** - Graphiti reserves `name`, `uuid`, `group_id`, etc. - use `company_name`, `tool_name` instead
13. **Entity type filtering reduces overhead** - Passing only relevant types per episode saves 65% of entity type token overhead
14. **Test assumptions about tools** - We assumed Graphiti could extract any entity type; investigation revealed NER-specific design

---

## 🔄 Session Handoff Instructions

**For next AI assistant picking up this work:**

1. Read this file (CURRENT_WORK.md) first
2. Read [GRAPH_ARCHITECTURE.md](GRAPH_ARCHITECTURE.md) for current design state
3. Check `context/Custom_entities_for_Graphiti_knowledge_graphs/` - this is the active research
4. Continue refinement conversation to answer open questions
5. Update [GRAPH_ARCHITECTURE.md](GRAPH_ARCHITECTURE.md) when decisions are made
6. Update this file (CURRENT_WORK.md) with new progress/decisions

**Current priority**: Land on custom entities decision, then group_id strategy.

---

## 📅 Timeline

- **2025-01-15**: Discovered group_id filtering issue with MCP
- **2025-01-19**: Fixed critical bugs (valid_at timestamps, episode naming, rate limits)
- **2025-01-19**: Created GRAPH_ARCHITECTURE.md to track design decisions
- **2025-01-19**: Currently in refinement phase for custom entities research
- **Next**: TBD - Land custom entities decision, then group_id strategy

---

**Remember**: This is foundational work. Take time to get it right. The graph will be the brain for everything we build.
