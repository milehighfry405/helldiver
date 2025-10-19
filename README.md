# Helldiver Research Agent

**AI-Optimized Documentation** - This README is designed for Claude Code and other AI assistants to quickly understand the project.

---

## 🤖 For Claude Code: Start Here

**When user says "read the README"**, do this:

1. **Read this entire file** (you're doing that now ✓)
2. **Read [docs/CURRENT_WORK.md](docs/CURRENT_WORK.md)** - **START HERE** - What we're working on RIGHT NOW
3. **Read [docs/AI_ONBOARDING.md](docs/AI_ONBOARDING.md)** - Navigation guide and workflows
4. **Read [docs/GRAPH_ARCHITECTURE.md](docs/GRAPH_ARCHITECTURE.md)** - Knowledge graph design decisions and strategy
5. **Check [docs/Claude Sessions/](docs/Claude%20Sessions/)** - Read latest `SESSION_SUMMARY_*.md` for previous context
6. **Read [docs/COMMIT_CHECKLIST.md](docs/COMMIT_CHECKLIST.md)** - Pre-commit checklist (follow before EVERY commit)

**Then say**: "Context loaded. Current focus: [summary from CURRENT_WORK.md]. Ready to continue!"

**CRITICAL RULES**:
- **Before ANY git commit**: Re-read [docs/COMMIT_CHECKLIST.md](docs/COMMIT_CHECKLIST.md) and follow it
- **When user says "commit"**: Automatically check [docs/COMMIT_CHECKLIST.md](docs/COMMIT_CHECKLIST.md), update docs, propose commit message
- **Session summaries**: Remind user to save them in `docs/Claude Sessions/` if context limit approaching

---

## 👤 For Humans: Quick Commands

**New session?** Say: `"Read the README"` → Claude loads all context

**Ready to commit?** Say: `"commit"` → Claude checks docs, updates as needed, proposes commit

---

## Quick Start for AI Assistants

### What This Project Does

Helldiver is a multi-agent research system that:
1. Takes a user query (e.g., "arthur ai based on out nyc")
2. Spawns 4 specialist workers (Academic, Industry, Tool, Critical Analyst)
3. Conducts research using Anthropic Batch API (50% cost savings)
4. Allows interactive refinement with prompt caching (90% cost savings)
5. Commits findings to Graphiti knowledge graph for future querying

### Key Architecture Principles

1. **Episode-based**: Each research is broken into episodes for optimal graph extraction
2. **User-approved naming**: LLM proposes episode names, user approves before folders created
3. **Optimal chunking**: One episode per worker (~1,400-2,600 tokens) for rich entity extraction
4. **Metadata grouping**: Episodes linked via name patterns, group_id hierarchy, and source_description

### File Structure

```
helldiver/
├── main.py                     # Core orchestrator (ResearchSession, state machine)
├── graphiti_client.py          # Graphiti/Neo4j interface
├── helldiver_agent.py          # (Legacy - functionality merged into main.py)
├── context/                    # Research sessions (gitignored except migration session)
│   └── {Episode_Name}/        # Session folder = initial episode name
│       ├── {Episode_Name}/    # Initial research (worker outputs)
│       │   └── narrative.txt  # Synthesized findings for initial research
│       ├── {Deep_Topic}/      # Deep research folders (clean names)
│       │   └── narrative.txt  # Synthesized findings for deep research
│       ├── session.json       # Session metadata (includes tasking context)
│       └── refinement_*.txt/json  # Refinement logs (includes tasking + refinement)
├── docs/
│   ├── CURRENT_WORK.md        # **START HERE** - Active tasks, next steps, open questions
│   ├── AI_ONBOARDING.md       # Primary entry point for AI assistants
│   ├── GRAPH_ARCHITECTURE.md  # Knowledge graph design decisions (group_id, schema, custom entities)
│   ├── ARCHITECTURE_OVERVIEW.md
│   ├── COMMIT_CHECKLIST.md    # Pre-commit checklist for AI (auto-updates docs)
│   ├── decisions/             # Architecture Decision Records (ADRs)
│   │   ├── 001-episode-naming-strategy.md
│   │   ├── 002-graphiti-chunking-strategy.md
│   │   └── 003-episode-grouping-metadata.md
│   └── Claude Sessions/       # Session continuation files (when Claude Code runs out of context)
│       ├── README.md          # Explains session continuation system
│       └── SESSION_SUMMARY_1-4.md
├── scripts/
│   └── kill_agents.py         # Utility to kill zombie processes
├── .env                       # API keys (gitignored)
├── requirements.txt
└── README.md                  # This file

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

### Required API Keys (.env)

```
ANTHROPIC_API_KEY=your_key_here
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
OPENAI_API_KEY=your_openai_key  # For Graphiti
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

### Test Graph Integration

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

## For Claude Code Specifically

**Starting a new session?** Read [docs/AI_ONBOARDING.md](docs/AI_ONBOARDING.md) first - it explains:
- Where to find information (navigation guide)
- When to read what (based on user's request)
- How session continuation works
- Best practices for AI assistants

**Quick checklist when continuing this project:**
1. Read [docs/AI_ONBOARDING.md](docs/AI_ONBOARDING.md) for navigation
2. Read [docs/GRAPH_ARCHITECTURE.md](docs/GRAPH_ARCHITECTURE.md) for knowledge graph design decisions
3. Check [docs/Claude Sessions/](docs/Claude%20Sessions/) for previous session context
4. Read [docs/ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md) for high-level architecture
5. Check [docs/decisions/](docs/decisions/) for rationale behind design choices
6. Run code as-is first to understand flow
7. Make changes incrementally, test after each change

## Contact

Project: https://github.com/milehighfry405/helldiver
Issues: https://github.com/milehighfry405/helldiver/issues
