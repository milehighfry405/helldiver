# Helldiver Research Agent

**AI-Optimized Documentation** - This README is designed for Claude Code and other AI assistants to quickly understand the project.

---

## 🤖 For Claude Code: Start Here

**New session? Type**: `/onboard`

This automatically loads:
- CLAUDE.md (critical rules, design rationale)
- docs/CURRENT_WORK.md (active work, next steps)
- Recent git history
- Latest session summary (if needed)

**Time**: <30 seconds

---

## 👤 For Humans: Quick Commands

**New session?** Type: `/onboard` → Claude loads context in <30 seconds

**Ready to commit?** Type: `/commit` → Claude updates docs, writes rich commit message, commits

**Done for the day?** Type: `/session-end` → Claude saves comprehensive session summary

---

## Quick Start for AI Assistants

### What This Project Does

Helldiver is a multi-agent research system with ontology-driven knowledge graph:
1. Takes a user query (e.g., "Arthur.ai downmarket opportunity")
2. Spawns 4 specialist workers (Academic, Industry, Tool, Critical Analyst)
3. Conducts research using Anthropic Batch API (50% cost savings)
4. Two-stage architecture: Natural research → Graph-optimized structuring
5. Allows interactive refinement with prompt caching (90% cost savings)
6. Commits findings to Graphiti knowledge graph with custom ontology (10 entity types, 11 edge types)

### Key Architecture Principles

1. **Episode-based**: Each research is broken into episodes for optimal graph extraction
2. **User-approved naming**: LLM proposes episode names, user approves before folders created
3. **Optimal chunking**: One episode per worker (~1,400-2,600 tokens) for rich entity extraction
4. **Metadata grouping**: Episodes linked via name patterns, group_id hierarchy, and source_description

### File Structure

```
helldiver/
├── README.md                    # Project overview, quick start
├── CLAUDE.md                    # AI context file (read this first!)
│
├── .claude/                     # Plugin system
│   ├── plugin.json              # Plugin manifest
│   └── commands/
│       ├── onboard.md           # /onboard command
│       ├── commit.md            # /commit command
│       └── session-end.md       # /session-end command
│
├── main.py                      # Entry point, research orchestration
├── core/
│   ├── session.py               # Session state management
│   └── research_cycle.py        # Unified research execution
├── workers/
│   ├── research.py              # Batch API + two-stage architecture
│   └── prompts.py               # Elite prompts (Anthropic 2025 best practices)
├── graph/
│   ├── client.py                # Graphiti client with retry logic
│   └── ontology.py              # Entity/edge types for knowledge graph
├── utils/
│   └── files.py                 # File I/O and conversation distillation
│
├── context/                     # Research sessions (gitignored)
│   └── {Session_Name}/         # Session folder
│       ├── {Episode_Name}/     # Research episode folder
│       │   ├── academic_researcher.txt      # Structured research (graph-optimized)
│       │   ├── academic_researcher_raw.txt  # Natural research (original quality)
│       │   ├── industry_intelligence.txt    # Structured research
│       │   ├── industry_intelligence_raw.txt
│       │   ├── tool_analyzer.txt            # Structured research
│       │   ├── tool_analyzer_raw.txt
│       │   ├── critical_analysis.txt        # Synthesized critical analysis
│       │   ├── refinement_context.txt       # Refinement conversation
│       │   └── refinement_distilled.txt     # Distilled strategic context (THE GOLD)
│       └── session.json        # Session metadata
│
├── docs/
│   ├── CURRENT_WORK.md          # **Active work tracker** (updated every commit)
│   ├── GRAPH_ARCHITECTURE.md    # Graph design decisions (active)
│   ├── ARCHITECTURE_OVERVIEW.md # Technical architecture (active)
│   │
│   ├── decisions/               # Architecture Decision Records (ADRs)
│   │   ├── 001-episode-naming-strategy.md
│   │   ├── 002-graphiti-chunking-strategy.md
│   │   ├── 003-episode-grouping-metadata.md
│   │   ├── 004-graphiti-ontology-extraction-findings.md
│   │   ├── 005-elite-prompt-engineering-implementation.md
│   │   └── 006-rate-limiting-and-retry-strategy.md
│   │
│   └── archive/                 # Historical documentation
│       ├── AI_ONBOARDING.md     # Old onboarding (replaced by CLAUDE.md + /onboard)
│       ├── COMMIT_CHECKLIST.md  # Old checklist (embedded in /commit plugin)
│       └── sessions/            # Historical session summaries
│           └── SESSION_SUMMARY_*.md
│
├── .env                         # API keys (gitignored)
├── requirements.txt             # Python dependencies
└── .gitignore

## Installation

```bash
# Clone repo
git clone https://github.com/milehighfry405/helldiver.git
cd helldiver

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env  # Then add your API keys
```

### Neo4j Setup (Required for Graph Storage)

1. **Install Neo4j Desktop** or use Docker:
   ```bash
   docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
   ```

2. **Create required fulltext indexes**:
   - Open Neo4j Browser: http://localhost:7474
   - Run the setup script:
   ```bash
   # In Neo4j Browser, paste and run:
   CREATE FULLTEXT INDEX node_name_and_summary IF NOT EXISTS
   FOR (n:Entity)
   ON EACH [n.name, n.summary];

   CREATE FULLTEXT INDEX edge_name_and_fact IF NOT EXISTS
   FOR ()-[r:RELATES_TO]-()
   ON EACH [r.name, r.fact];
   ```
   - Or run: `cat setup_neo4j.cypher | cypher-shell -u neo4j -p password`

3. **Verify indexes created**:
   ```cypher
   SHOW INDEXES;
   ```
   You should see both `node_name_and_summary` and `edge_name_and_fact` in the list.

### Required API Keys (.env)

```
ANTHROPIC_API_KEY=your_key_here
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
OPENAI_API_KEY=your_openai_key  # For Graphiti entity extraction
MODEL_NAME=gpt-4o-mini          # For Graphiti
```

## Usage

### Start New Research

```bash
python main.py
```

Flow:
1. Tasking conversation (Socratic questioning to refine query)
2. LLM proposes episode name → user approves
3. Research phase (4 workers, 3-5 minutes)
4. Refinement phase (ask questions, request deep research)
5. Commit to graph

### Resume Existing Session

```bash
python main.py --refine "context/Episode_Name"
```

### Test Mode (Fast 30-second research)

```bash
python main.py --test
```

Uses Haiku with 500 tokens, no web search. Perfect for testing workflow without waiting 3-5 minutes.

### Mock Mode (Test without Neo4j)

```bash
# Mock mode (no graphiti_core installed)
python main.py  # Will simulate graph writes

# Real mode (requires graphiti_core + Neo4j)
pip install graphiti_core
# Start Neo4j, then run
python main.py
```

## Key Concepts for AI

### ResearchSession State Machine

```
TASKING → RESEARCH → REFINEMENT → COMMIT → COMPLETE
                         ↑            ↓
                         └─── (loop for deep research)
```

### Episode Structure (NEW as of 2025-10-13)

**Before**: One episode per research session (9,000+ tokens, sparse extraction)
**After**: One episode per worker (1,400-2,600 tokens, rich extraction)

For a full research cycle (initial + 1 deep + refinement):
- 4 episodes: Initial research (Academic, Industry, Tool, Critical)
- 4 episodes: Deep research (same workers)
- 1 episode: Refinement (distilled mental models)
**Total: 9 episodes**

### Episode Naming Pattern

```
{Session Name} - {Worker Role}
```

Examples:
- "Arthur AI product and market analysis - Academic Research"
- "Downmarket ICP signals - Industry Intelligence"

### Episode Metadata (for grouping in graph)

```python
{
    "name": "Arthur AI analysis - Academic Research",
    "group_id": "helldiver_research/arthur_ai_analysis/initial",
    "source_description": "Initial Research | Session: Arthur AI analysis | 2025-10-13T15:30:00"
}
```

## Common Tasks

### Add New Worker Type

1. Edit `create_worker_batch()` in main.py
2. Add worker to batch requests
3. Update `worker_mapping` in `commit_research_episode()`

### Change Graphiti Chunking

See `docs/decisions/002-graphiti-chunking-strategy.md` for rationale.
Chunking happens in `commit_research_episode()` function.

### Modify Distillation Prompt

Edit `distill_refinement_context()` in main.py (lines ~705-853).
Prompt follows Anthropic best practices with XML tags.

### Debug Graph Writes

If `graphiti_core` not installed, system runs in mock mode:
- Check terminal output for "MOCK GRAPH WRITE"
- Episodes show what WOULD be written
- No actual Neo4j connection needed

## Architecture Decision Records (ADRs)

Before making changes, read relevant documentation:

- **[GRAPH_ARCHITECTURE.md](docs/GRAPH_ARCHITECTURE.md)**: Knowledge graph design decisions (group_id strategy, custom entities, schema design)
- **[decisions/001](docs/decisions/001-episode-naming-strategy.md)**: Episode Naming Strategy (why LLM-generated names)
- **[decisions/002](docs/decisions/002-graphiti-chunking-strategy.md)**: Graphiti Chunking Strategy (why one-episode-per-worker)
- **[decisions/003](docs/decisions/003-episode-grouping-metadata.md)**: Episode Grouping Metadata (how episodes link in graph)

## Session Continuation

When Claude Code approaches context limit, it generates session summary files stored in:
```
docs/Claude_Sessions/session-{date}.md
```

These files enable seamless continuation on new computers or after context resets.

## Git Workflow

```bash
# Normal workflow
git add .
git commit -m "description"
git push

# Context folder is gitignored EXCEPT migration sessions
# Check .gitignore for current exceptions
```

## Debugging

### Kill Zombie Processes

```bash
python scripts/kill_agents.py
```

### Check Session State

```bash
cat context/{Session_Name}/session.json
```

### View Research Outputs

```bash
ls context/{Session_Name}/{Episode_Name}/
# academic_researcher.txt
# industry_intelligence.txt
# tool_analyzer.txt
# critical_analysis.txt
```

## Project Status

**Current State**: Fully refactored with episode naming and chunking optimizations (Oct 13, 2025)

**Recent Changes**:
- Decoupled folder creation from session initialization
- LLM-generated episode names with user approval
- One-episode-per-worker for optimal Graphiti extraction
- Hierarchical metadata grouping for graph queries
- **NEW (Oct 14, 2025)**: Narrative.txt files saved per-research-folder (no overwriting)
- **NEW (Oct 14, 2025)**: Tasking conversation now preserved in refinement logs

**Next Steps**:
- Add custom entity types for Graphiti (Company, Tool, Signal, Person)
- Test retroactive commit on existing Arthur AI session
- Build Clay table integration for ICP lead generation

## Plugin Workflows

This project uses Claude Code plugins for automated documentation management.

### `/onboard` - Load Context
**Use when**: Starting new session, returning after break, switching computers

**What it does**:
- Reads CLAUDE.md, CURRENT_WORK.md
- Checks git log and status
- Loads latest session summary if needed
- Outputs concise summary of where we left off

### `/commit` - Update Docs and Commit
**Use when**: Ready to commit changes

**What it does**:
- Asks "why did you make these changes?"
- Determines which docs need updates based on what changed
- Updates CURRENT_WORK.md (always)
- Updates README, CLAUDE.md, ARCHITECTURE_OVERVIEW, GRAPH_ARCHITECTURE (if needed)
- Creates ADR if major architectural decision
- Writes rich commit message with full context
- Commits and pushes

### `/session-end` - Save Session Summary
**Use when**: Done for the day, switching computers, before long break

**What it does**:
- Extracts context from full conversation (not just git log)
- Generates comprehensive summary capturing:
  - Problems solved (with debugging journey)
  - Decisions made (with alternatives considered)
  - User questions (confusion points)
  - Key learnings (lessons from debugging)
- Saves to docs/archive/sessions/
- Commits and pushes automatically

## For Claude Code: Quick Reference

**Files to read** (in order):
1. CLAUDE.md (critical rules, design rationale, file map)
2. docs/CURRENT_WORK.md (active work, next steps, open questions)
3. docs/GRAPH_ARCHITECTURE.md (if graph-related work)
4. docs/ARCHITECTURE_OVERVIEW.md (if need technical architecture reference)
5. docs/archive/sessions/SESSION_SUMMARY_*.md (latest, if need deep context)

**Every file has a purpose**:
- README.md → Project overview for humans and AI
- CLAUDE.md → AI context file (fast reference)
- CURRENT_WORK.md → Active work tracker (updated every commit)
- GRAPH_ARCHITECTURE.md → Graph design decisions (active development)
- ARCHITECTURE_OVERVIEW.md → Technical architecture (reference)
- decisions/ → ADRs (permanent record of major decisions)
- archive/ → Historical docs (not actively updated)

## Contact

Project: https://github.com/milehighfry405/helldiver
Issues: https://github.com/milehighfry405/helldiver/issues
