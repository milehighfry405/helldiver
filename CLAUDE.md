# Helldiver Project - AI Context File

**Last Updated**: 2025-01-19

---

## What This Project Is

Multi-agent research system for solo developer working with Claude Code.

**Flow**: User query → 4 specialist workers (Academic, Industry, Tool, Critical Analyst) → Research → Graphiti knowledge graph
**Goal**: Build permanent memory substrate for research intelligence and execution layer
**Status**: Active development on graph architecture (custom entities, group_id strategy)

---

## Quick Start (New Session)

**Type**: `/onboard`

This will:
- Read all necessary context files
- Check recent git history
- Load active work status
- Tell you where we left off

**Time**: <30 seconds

---

## Critical Rules (Never Break These)

These are lessons from painful debugging sessions. **Read every session.**

### 1. Group IDs: Underscores Only, No Slashes
**Format**: `helldiver_research_SessionName_initial`
**Why**: Graphiti validation requires `^[a-zA-Z0-9_-]+$` (rejects slashes)
**Cost**: 2 hours debugging validation errors
**See**: docs/archive/sessions/SESSION_SUMMARY_4.md

### 2. Datetimes: Always Timezone-Aware
**Use**: `datetime.now(timezone.utc)`
**Why**: Naive datetimes → `NULL valid_at` → MCP can't find episodes
**Cost**: 2 hours debugging MCP integration
**See**: docs/CURRENT_WORK.md "Key Learnings"

### 3. Episode Naming: "{Session} - {Worker}" Format
**Example**: "Custom entities for Graphiti - Academic Research"
**Why**: Enables querying by session name OR worker type
**See**: docs/decisions/001-episode-naming-strategy.md

### 4. Episode Size: 1,400-2,600 Tokens (One Per Worker)
**Why**: Graphiti extracts richer entities from smaller chunks
**Tested**: 9,000+ token episodes had sparse extraction
**See**: docs/decisions/002-graphiti-chunking-strategy.md

### 5. Mock Mode First: Always Test with --mock
**Command**: `python main.py --refine "context/Session" --mock`
**Why**: Validates structure before consuming API credits, catches API signature errors
**See**: docs/archive/sessions/SESSION_SUMMARY_4.md "Mock Mode Validation"

### 6. OpenAI Rate Limits: Expect 500 Errors
**Why**: Graphiti uses OpenAI `gpt-4o-mini` for entity extraction
**Solution**: Progressive backoff (2s, 4s, 6s) - implemented in code
**See**: docs/CURRENT_WORK.md "Critical Bugs Fixed"

### 7. Neo4j First-Write Warnings: Expected Behavior
**What**: "Property does not exist", "Label does not exist" warnings
**Why**: Empty database creates schema on first write
**Action**: Ignore warnings, check for actual errors
**See**: docs/archive/sessions/SESSION_SUMMARY_4.md "Test 2"

### 8. Retroactive Commits: Load All Worker Files Separately
**Why**: Preserves one-episode-per-worker chunking (optimal for Graphiti)
**Files**: academic_researcher.txt, industry_intelligence.txt, tool_analyzer.txt, critical_analysis.txt
**See**: docs/decisions/002-graphiti-chunking-strategy.md

---

## Design Rationale (Why We Built It This Way)

### Episode-Based Architecture
**What**: Break research into discrete episodes (4 workers + 1 refinement per research)
**Why**: Graphiti extracts richer entities from 1,400-2,600 token chunks
**Alternative**: Single 9,000+ token episode (tested, extraction was sparse)
**Decision**: One episode per worker + one for user's refinement context
**Refinement Episode**: User's Socratic conversation (THE GOLD) - why research matters, mental models, priorities
**See**: docs/decisions/002-graphiti-chunking-strategy.md

### Group ID Format: `helldiver_research_{session}_{type}`
**Why**: Enables filtering by session (CONTAINS) or type (ENDS WITH)
**Constraint**: Underscores required (Graphiti validation rejects slashes)
**Use Case**: Query all "initial" research across sessions: `WHERE group_id ENDS WITH "_initial"`
**See**: docs/decisions/003-episode-grouping-metadata.md, docs/GRAPH_ARCHITECTURE.md

### Timezone-Aware Datetimes
**What**: Always use `datetime.now(timezone.utc)`
**Why**: Naive datetimes → `NULL valid_at` field → MCP temporal search fails
**Cost**: 2 hours debugging "episodes exist but MCP can't find them"
**See**: docs/archive/sessions/SESSION_SUMMARY_4.md

### Mock Mode Testing
**What**: `--mock` flag simulates graph writes without Neo4j connection
**Why**: Validates episode structure, metadata, API signatures before real commits
**When**: Use before every first real commit to catch errors early
**See**: docs/archive/sessions/SESSION_SUMMARY_4.md "Mock Mode Validation"

---

## File Map

```
helldiver/
├── README.md            # Project overview, installation, quick start
├── CLAUDE.md            # THIS FILE - AI context (read first)
│
├── .claude/             # Plugin system
│   ├── plugin.json      # Plugin manifest
│   └── commands/
│       ├── onboard.md   # /onboard - Load full context
│       ├── commit.md    # /commit - Update docs, commit changes
│       └── session-end.md # /session-end - Save session summary
│
├── main.py              # Core orchestrator (~1,813 lines)
│                        # Key: ResearchSession class, commit_research_episode()
├── graphiti_client.py   # Graph interface (~173 lines)
│                        # Key: GraphitiClient.add_research_episode()
│
├── docs/
│   ├── CURRENT_WORK.md          # **START HERE** - Active work tracker
│   ├── GRAPH_ARCHITECTURE.md    # Graph design decisions (group_id, schema, entities)
│   ├── ARCHITECTURE_OVERVIEW.md # Technical architecture, state machine
│   │
│   ├── decisions/       # Architecture Decision Records (ADRs)
│   │   ├── 001-episode-naming-strategy.md
│   │   ├── 002-graphiti-chunking-strategy.md
│   │   └── 003-episode-grouping-metadata.md
│   │
│   └── archive/         # Historical documentation
│       ├── AI_ONBOARDING.md     # Old onboarding (replaced by CLAUDE.md)
│       ├── COMMIT_CHECKLIST.md  # Old checklist (embedded in /commit plugin)
│       └── sessions/    # Historical session summaries
│
└── context/             # Research sessions (gitignored except migration)
    └── {Session_Name}/  # Episode folders with worker outputs
```

---

## Architecture Quick Facts

- **State Machine**: TASKING → RESEARCH → REFINEMENT → COMMIT → COMPLETE
- **Workers**: Academic Research, Industry Intelligence, Tool Analyzer, Critical Analyst
- **Episode Structure**: 5 episodes per research (4 workers + 1 refinement context)
- **Episode Size**: 1,400-2,600 tokens (optimal for Graphiti entity extraction)
- **Refinement Flow**: Continuous conversation (tasking + post-research) → distill → commit → clear
- **Group ID**: `helldiver_research_{session}_{type}` (underscores only!)
- **Cost Optimization**: Batch API (50% savings) + Prompt Caching (90% savings)
- **Graph**: Graphiti (temporal knowledge graph) + Neo4j + OpenAI (entity extraction)

**For detailed architecture**: See docs/ARCHITECTURE_OVERVIEW.md

---

## Common Commands

### Start New Research
```bash
python main.py
```

### Resume Existing Session
```bash
python main.py --refine "context/Session_Name"
```

### Test in Mock Mode (Always Test First)
```bash
python main.py --refine "context/Session_Name" --mock
```

### Check Neo4j Browser
```bash
# Navigate to: http://localhost:7474
# Query: MATCH (e:Episodic) RETURN e.name, e.group_id, e.created_at
```

---

## Plugin Workflows

### `/onboard` - Load Context
Use when:
- Starting new session
- Coming back after break
- Switching computers (after git pull)

What it does:
- Reads CURRENT_WORK.md
- Checks git log
- Loads latest session summary if needed
- Tells you where we left off

### `/commit` - Update Docs and Commit
Use when:
- Ready to commit changes
- Want docs automatically updated

What it does:
- Asks "why did you make these changes?"
- Updates appropriate docs (CURRENT_WORK.md, etc.)
- Writes rich commit message
- Shows you for approval
- Commits and pushes

### `/session-end` - Save Session Summary
Use when:
- **After EVERY /commit** (captures context while fresh)
- Or after 1-2 commits if commits are small

**Why after every commit**: Your commits are meaty (2-3 hours of discussion, multiple attempts, design decisions). Context fades from Claude's window after 2-3 commits. Capture the journey while it's still fresh.

**Typical flow**:
1. Work on feature (2-3 hours of discussion)
2. `/commit` (commit the code)
3. `/session-end` (capture the journey immediately)
4. Repeat

What it does:
- Extracts FULL conversation context from current window
- Generates comprehensive summary focused on THIS commit (800-1,200 lines)
- Saves as `SESSION_SUMMARY_[N]_[topic_slug].md` (searchable by topic)
- Commits and pushes automatically

---

## Key Learnings (Growing List)

- **Graphiti's group_id is optional** - Default searches entire graph (supports "omega context")
- **Enterprise patterns ≠ our patterns** - Zep uses per-user isolation; we want cross-session synthesis
- **Episode size matters** - 1,000-2,000 tokens optimal (validated via testing)
- **Timezone-aware datetimes are critical** - Naive datetimes break MCP search
- **MCP compatibility requires planning** - Can't assume tools "just work" without correct metadata
- **Mock mode is invaluable** - Catches errors before consuming API credits
- **OpenAI 500 errors are transient** - Retry logic with backoff handles them

**For session-specific learnings**: See docs/CURRENT_WORK.md → "Key Learnings This Session"

---

## Last Session Recap

**Date**: 2025-01-19
**What we did**: Designed and built plugin-based documentation system
**What we decided**: Use plugins (not Skills) for explicit workflow triggers
**Where we left off**: Building the plugin system (.claude/ directory)
**Next session should**: Test /onboard, /commit, /session-end workflows

---

## If Confused, Read

1. **What am I working on?** → docs/CURRENT_WORK.md (Active Focus section)
2. **What are the graph design decisions?** → docs/GRAPH_ARCHITECTURE.md
3. **What's the technical architecture?** → docs/ARCHITECTURE_OVERVIEW.md
4. **Why did we make decision X?** → docs/decisions/ (ADRs) or git log
5. **What happened last session?** → docs/archive/sessions/SESSION_SUMMARY_*.md (latest)
6. **Still confused?** → Ask user for clarification

---

**File size**: ~195 lines (target: ≤200 ✓)
