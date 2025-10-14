# Helldiver Research Agent - Architecture Overview

**Last Updated:** 2025-10-13
**Status:** Production-ready with recent refactors for episode naming and Graph chunking optimization

> **Documentation Guide**: New to this project? Start with [AI_ONBOARDING.md](AI_ONBOARDING.md) for navigation. Continuing from previous session? Check [Claude Sessions/](Claude%20Sessions/) for context.

## What This Project Does

The Helldiver Research Agent is a multi-agent research system designed for deep, context-engineered knowledge discovery with human-in-the-loop refinement. The system conducts comprehensive research using specialized AI workers (Academic Researcher, Industry Intelligence, Tool Analyzer, and Critical Analyst) that operate in parallel via Anthropic's Batch API, then synthesizes findings into dense narrative summaries.

The key innovation is the interactive refinement phase, where users engage in conversational "wave function collapse"—asking clarifying questions, reframing priorities, and providing mental models that get weighted higher than the original research when committing to a knowledge graph. This implements Anthropic's context engineering principles: the agent doesn't just gather facts, it learns how the user wants to interpret those facts, creating a personalized lens for understanding the research.

All findings persist to a Graphiti knowledge graph as **optimally-chunked episodes** (one per worker, ~1,400-2,600 tokens each) for rich entity extraction and long-term episodic memory across research sessions.

## System Architecture (Updated Oct 2025)

### Episode-Based Research Model

The architecture follows a **session-based, episodic research model** where each session is broken into optimally-sized episodes for Graphiti knowledge graph extraction:

#### Folder Structure

```
context/
└── {Episode_Name}/                          # Session folder = initial episode name
    ├── {Episode_Name}/                      # Initial research (worker outputs)
    │   ├── academic_researcher.txt          # ~1,900 tokens
    │   ├── industry_intelligence.txt        # ~2,500 tokens
    │   ├── tool_analyzer.txt                # ~2,200 tokens
    │   ├── critical_analysis.txt            # ~1,400 tokens
    │   └── narrative.txt                    # Synthesized findings for this research
    ├── {Deep_Research_Topic}/               # Deep research (same structure)
    │   ├── (same 4 worker files)
    │   └── narrative.txt                    # Synthesized findings for this deep research
    ├── session.json                         # Session metadata (includes tasking context)
    ├── refinement_context.json              # Full conversation log (tasking + refinement)
    ├── refinement_context.txt               # Human-readable transcript (tasking + refinement)
    └── refinement_distilled.txt             # Graph-optimized mental models (~1,500 tokens)
```

**Key Change (Oct 2025)**: Session folders are now named after clean episode names (e.g., "Arthur_AI_product_and_market_analysis") instead of timestamps (e.g., "session_research_20251012_170404"). This makes folders human-readable and aligns with knowledge graph titles.

### Episode Creation Flow

#### 1. Initial Research

```
User Query → Tasking Conversation → LLM Generates Episode Name → User Approves
    ↓
Filesystem Created with Clean Name → 4 Workers Research (Batch API)
    ↓
4 Episodes Written to Graph (one per worker)
```

#### 2. Deep Research

```
User Requests Deep Research → Topic Extracted → LLM Generates Episode Name → User Approves
    ↓
Folder Created with Clean Name → 4 Workers Research
    ↓
4 Episodes Written to Graph (linked to initial research)
```

#### 3. Refinement & Commit

```
User Refines Understanding → Distillation Extracts Mental Models
    ↓
1 Episode Written to Graph (links to all research episodes)
```

**Total Episodes for Full Cycle**: 9 episodes (4 initial + 4 deep + 1 refinement)

### State Machine

```
TASKING → RESEARCH → REFINEMENT → COMMIT → COMPLETE
                         ↑            ↓
                         └─────────────┘
                         (loop for deep research)
```

## Technical Implementation

### Core Components

#### 1. ResearchSession Class (Stateful Orchestrator)

**Architecture Principle**: Decoupled instantiation from filesystem creation

```python
class ResearchSession:
    def __init__(self):
        # Initialize state (NO filesystem I/O)
        self.state = "TASKING"
        self.query = None
        self.episode_name = None
        self.session_dir = None  # Set later by initialize_filesystem()

    def initialize_filesystem(self, episode_name: str):
        # Called AFTER user approves episode name
        self.session_dir = os.path.join("context", safe_name(episode_name))
        self.initial_research_dir = os.path.join(self.session_dir, safe_name(episode_name))
        os.makedirs(self.initial_research_dir)
```

**Why**: Allows episode naming to happen BEFORE folder creation, enabling user control and clean folder structures.

#### 2. Episode Naming System

```python
def generate_episode_name(query: str) -> str:
    # LLM proposes clean episode name (3-8 words)
    suggested_name = llm_generate(query)

    # User approval required
    print(f"I suggest naming this episode: '{suggested_name}'")
    user_input = input("Press Enter to approve, or type different name: ")

    return user_input if user_input else suggested_name
```

**Characteristics of Good Episode Names**:
- Concise (3-8 words)
- Descriptive of what was researched
- Keyword-focused (easy to find later)
- Professional (no verbose metadata)

**Examples**:
- ✅ "Arthur AI product and market analysis"
- ✅ "Downmarket ICP signals for Arthur AI"
- ❌ "Based on the conversation, they want deep research on..."

See [ADR-001](decisions/001-episode-naming-strategy.md) for full rationale.

#### 3. Graphiti Chunking Strategy

**Architecture Principle**: One episode per worker for optimal entity extraction

**Before (❌)**:
```python
# One big episode per research session
episode_body = combine_all_workers()  # 9,000+ tokens
commit_episode(episode_body)  # Sparse extraction
```

**After (✅)**:
```python
# One episode per worker
for worker in workers:
    episode_body = worker.findings  # 1,400-2,600 tokens
    commit_episode(
        name=f"{session_name} - {worker.role}",
        body=episode_body,
        group_id=f"helldiver_research/{session}/{type}"
    )
```

**Why**: Graphiti research shows 1,000-2,000 token episodes produce rich, detailed entity extraction vs sparse extraction from large episodes.

See [ADR-002](decisions/002-graphiti-chunking-strategy.md) for measured token counts and benchmarks.

#### 4. Episode Grouping Metadata

Episodes from the same session are linked via three metadata fields:

```python
{
    "name": "Arthur AI analysis - Academic Research",
    "group_id": "helldiver_research/arthur_ai_analysis/initial",
    "source_description": "Initial Research | Session: Arthur AI analysis | 2025-10-13T15:30:00"
}
```

**Querying**:
- By name prefix: All episodes with "Arthur AI analysis"
- By group_id: `helldiver_research/arthur_ai_analysis/*`
- By source_description: Session metadata for programmatic linking

See [ADR-003](decisions/003-episode-grouping-metadata.md) for full query patterns.

### Cost Optimization

1. **Batch API** (50% cost savings): 3 workers submitted as batch jobs, avoiding rate limits
2. **Prompt Caching** (90% cost savings): Research context cached during refinement conversations
3. **Opus 4 for Synthesis Only**: Using Sonnet 4.5 for workers, Opus 4 only for final narrative synthesis

### Context Engineering Pattern

**Weighted Context Hierarchy**:
```
User Mental Models (refinement_distilled.txt) > Original Research
```

When committing to graph:
1. Research episodes provide facts
2. Refinement episode provides interpretive lens
3. Graph queries combine both with user's framing weighted higher

### Session Persistence

**State Files**:
- `session.json`: Session metadata (state, query, episode IDs)
- `refinement_context.json`: Full conversation log (audit trail)
- `refinement_distilled.txt`: Graph-optimized mental models (created at commit time)

**Crash Recovery**: All state persisted to disk, enabling session resumption with `--refine` flag.

## Design Patterns

### 1. Separation of Concerns

- **ResearchSession**: Pure state object (no I/O in __init__)
- **Episode Generation**: LLM + user approval (no filesystem assumptions)
- **Graph Commits**: Isolated in `graphiti_client.py`

### 2. LLM-Based Intent Detection

**No keyword matching**. All user inputs parsed via LLM:

```python
intent = llm_detect_intent(user_input, context)
# Returns: "PROCEED", "DEEP_RESEARCH", "COMMIT", "QUESTION", "UNCLEAR"
```

**Why**: More robust than regex, handles conversational inputs naturally.

### 3. Wave Function Collapse

Users can explore tangents during refinement:
- Agent maintains original research question in state
- Answers follow-up questions naturally
- Conversations eventually converge back to commit

### 4. Prompt Caching Strategy

```python
messages = [
    {"role": "user", "content": [
        {"type": "text", "text": research_context, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": current_question}  # Not cached
    ]}
]
```

Large contexts cached, dynamic queries fresh.

## Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `main.py` | Core orchestrator, state machine, all logic | ~1,800 |
| `graphiti_client.py` | Graphiti/Neo4j interface | ~150 |
| `helldiver_agent.py` | Legacy (merged into main.py) | Deprecated |
| `docs/AI_ONBOARDING.md` | Navigation guide for AI assistants | Entry point |
| `docs/ARCHITECTURE_OVERVIEW.md` | This file - system architecture | Overview |
| `docs/decisions/` | Architecture Decision Records (ADRs) | Design rationale |
| `docs/Claude Sessions/` | Session continuation files | Context handoff |

## Future Enhancements

### Planned

1. **Custom Graphiti Entity Types**:
   ```python
   class Company(BaseModel):
       name: str
       funding_stage: str
       employee_count: int
   ```

2. **Clay Table Integration**: Query graph → build ICP tables for lead generation

3. **Multi-Session Graph Queries**: Cross-session insights and pattern detection

### Under Consideration

- Async worker execution (replace Batch API with async tasks)
- Streaming synthesis (show narrative as it's generated)
- Graph-based session resumption (load context from graph instead of files)

## For Developers

### Making Changes

1. **Read ADRs first**: `docs/decisions/` explains rationale for design choices
2. **Test incrementally**: System has many moving parts, test after each change
3. **Update docs**: Keep ADRs and this overview in sync with code

### Common Modifications

- **Add worker type**: Edit `create_worker_batch()` and `commit_research_episode()`
- **Change chunking**: See ADR-002, modify `commit_research_episode()`
- **Modify distillation**: Edit `distill_refinement_context()` prompt

### Debugging

```bash
# Mock mode (no graphiti_core needed)
python main.py  # Simulates graph writes

# Kill zombie processes
python scripts/kill_agents.py

# Check session state
cat context/{Session_Name}/session.json
```

## Architecture Evolution

### Oct 2025 Refactor

**Changes**:
1. Decoupled folder creation from session initialization
2. LLM-generated episode names with user approval
3. One-episode-per-worker for optimal Graphiti extraction
4. Hierarchical metadata grouping for graph queries
5. **NEW (Oct 14, 2025)**: Narrative.txt files now saved per-research-folder instead of session root
6. **NEW (Oct 14, 2025)**: Tasking context (initial conversation) now saved in refinement logs

**Impact**:
- Better folder organization (human-readable names)
- Richer graph extraction (optimal token counts)
- More queryable graph structure (hierarchical group_id)
- Complete conversation history preserved (tasking + refinement)
- Each research has its own narrative (no overwriting)

### Previous State

- Timestamps in folder names
- Verbose LLM extraction metadata in folder names
- One episode per research session (suboptimal for Graphiti)

## Questions for Future Reviews

1. **Async Architecture**: Should we replace Batch API with async worker tasks for real-time progress?
2. **Graph-First Design**: Should sessions load from graph instead of files?
3. **Streaming Synthesis**: Can we stream narrative generation for better UX?
4. **Custom Entity Schema**: What entity types are most valuable for our use cases?
5. **Multi-Agent Coordination**: Can workers collaborate during research instead of parallel isolation?

## References

- [Anthropic Prompt Engineering](https://docs.anthropic.com/claude/docs/prompt-engineering)
- [Graphiti Documentation](https://help.getzep.com/graphiti)
- [ADR-001: Episode Naming Strategy](decisions/001-episode-naming-strategy.md)
- [ADR-002: Graphiti Chunking Strategy](decisions/002-graphiti-chunking-strategy.md)
- [ADR-003: Episode Grouping Metadata](decisions/003-episode-grouping-metadata.md)
