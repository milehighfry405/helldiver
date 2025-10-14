# AI Assistant Onboarding Guide

**Purpose**: This document is the **primary entry point** for AI assistants (Claude Code, ChatGPT, etc.) picking up this project. It explains where to find information and how to get context quickly.

## Quick Start (30 seconds)

If the user says "read the docs and get up to speed", do this:

1. **Read this file first** (you're already here ✓)
2. **Read [README.md](../README.md)** - Project overview, installation, usage
3. **Read [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)** - High-level architecture
4. **Check [Claude Sessions/](Claude%20Sessions/)** - Previous session context (if continuing)
5. **Browse [decisions/](decisions/)** - ADRs for architectural decisions

**Total reading time: 5-10 minutes**

## Documentation Structure

```
helldiver/
├── README.md                           # START HERE - Project overview for humans and AI
├── docs/
│   ├── AI_ONBOARDING.md               # THIS FILE - Navigation guide for AI
│   ├── ARCHITECTURE_OVERVIEW.md        # System architecture, design patterns
│   ├── Claude Sessions/               # Session continuation files
│   │   ├── README.md                  # Explains session continuation system
│   │   ├── SESSION_SUMMARY_1.md       # First session (migration, retroactive commit)
│   │   └── SESSION_SUMMARY_2.md       # Second session (episode naming, chunking)
│   └── decisions/                     # Architecture Decision Records (ADRs)
│       ├── 001-episode-naming-strategy.md
│       ├── 002-graphiti-chunking-strategy.md
│       └── 003-episode-grouping-metadata.md
```

## When to Read What

### Scenario 1: New to the Project

**User says**: "Help me understand this codebase" or "What does this project do?"

**You should**:
1. Read [README.md](../README.md) - Get project overview
2. Read [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) - Understand architecture
3. Ask user what they want to work on

### Scenario 2: Continuing from Previous Session

**User says**: "I'm continuing from a previous session" or "Read the session summary"

**You should**:
1. Read [Claude Sessions/README.md](Claude%20Sessions/README.md) - Understand continuation system
2. Find latest `SESSION_SUMMARY_*.md` in [Claude Sessions/](Claude%20Sessions/)
3. Read that summary completely
4. Continue work without asking questions already answered

### Scenario 3: Making Architectural Changes

**User says**: "Let's change how episode naming works" or "Refactor the chunking strategy"

**You should**:
1. Read [README.md](../README.md) - Current architecture
2. Read relevant ADR in [decisions/](decisions/) - Understand existing rationale
3. Read [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) - See how it fits overall
4. Propose changes, discuss tradeoffs
5. **After implementing**: Create new ADR or update existing one

### Scenario 4: Debugging Issues

**User says**: "X isn't working" or "Why does Y happen?"

**You should**:
1. Check [Claude Sessions/](Claude%20Sessions/) - See if issue was encountered before
2. Read relevant code in [main.py](../main.py) or [graphiti_client.py](../graphiti_client.py)
3. Check [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) - Understand expected behavior
4. Debug and fix

### Scenario 5: Adding Features

**User says**: "Add feature X" or "Implement Y"

**You should**:
1. Read [README.md](../README.md) - Understand current feature set
2. Read [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) - Understand patterns to follow
3. Check [decisions/](decisions/) - See if related decisions exist
4. Implement feature following existing patterns
5. **After implementing**: Update docs, consider creating ADR if architectural

### Scenario 6: Committing Changes

**User says**: "Commit" or "Ready to commit" or "Let's commit this" or "commit"

**🚨 CRITICAL WORKFLOW - NEVER SKIP THIS**:

1. **Re-read [COMMIT_CHECKLIST.md](COMMIT_CHECKLIST.md)** - Even if you read it earlier, read it again NOW
   - Why? Context window may be filled with other work
   - The checklist ensures docs stay current
   - Takes 30 seconds, saves hours of future confusion

2. **Run through checklist automatically** (don't ask user about each item)
   - Check if ADR needed
   - Check if README needs update
   - Check if Architecture Overview needs update
   - Check if code comments sufficient

3. **Make doc updates** (ADR, README, Architecture Overview as needed)

4. **Generate commit message** with context and doc references

5. **Show user** what docs were updated and proposed commit message

6. **Ask for approval** to commit

**IMPORTANT**:
- This is **automatic**. User doesn't want to be asked about each checklist item.
- You check the list, update docs, then show results.
- **ALWAYS re-read COMMIT_CHECKLIST.md** when user says "commit", even if context is full.

## Key Concepts (Quick Reference)

### ResearchSession State Machine
```
TASKING → RESEARCH → REFINEMENT → COMMIT → COMPLETE
             ↑           ↓
             └───────────┘ (loop for deep research)
```

### Episode-Based Architecture
- **Episode**: A discrete unit of research committed to knowledge graph
- **Why**: Optimal chunking (1,400-2,600 tokens) for Graphiti entity extraction
- **How**: One episode per worker (4 per research session)

### Episode Naming
- **Generated by**: LLM (Claude)
- **Approved by**: User
- **When**: Before folders are created
- **Format**: "{Session Name} - {Worker Role}"

### Folder Structure
```
context/
└── {Episode_Name}/              # Session folder = initial episode name
    ├── {Episode_Name}/          # Initial research folder
    ├── {Deep_Topic_1}/          # Deep research folders (clean names)
    ├── {Deep_Topic_2}/
    ├── session.json             # Session metadata
    ├── narrative.txt            # Synthesized findings
    └── refinement_context.json  # Refinement conversations
```

## Common Tasks (Quick Links)

### Understanding a Function
1. Search for function name in [main.py](../main.py)
2. Read function docstring
3. Check if it's referenced in [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)
4. Look for related ADR in [decisions/](decisions/)

### Changing Episode Naming
1. Read [001-episode-naming-strategy.md](decisions/001-episode-naming-strategy.md)
2. Modify `generate_episode_name()` in [main.py](../main.py)
3. Test with `python main.py`
4. Update ADR with changes

### Changing Graph Chunking
1. Read [002-graphiti-chunking-strategy.md](decisions/002-graphiti-chunking-strategy.md)
2. Modify `commit_research_episode()` in [main.py](../main.py)
3. Test in mock mode
4. Update ADR with changes

### Changing Episode Grouping
1. Read [003-episode-grouping-metadata.md](decisions/003-episode-grouping-metadata.md)
2. Modify metadata in `commit_research_episode()` in [main.py](../main.py)
3. Test graph queries
4. Update ADR with changes

## Documentation Philosophy

### For Humans
- **README.md**: Quick start, installation, usage
- **ARCHITECTURE_OVERVIEW.md**: How the system works

### For AI
- **AI_ONBOARDING.md**: Navigation and quick reference (this file)
- **Claude Sessions/**: Detailed context from previous work
- **ADRs**: Rationale behind decisions

### For Both
- All docs use clear, concise language
- Code examples throughout
- File/line references for easy navigation
- Updated as project evolves

## File/Line Reference Format

When referencing code, use this format:

```
[filename.ts:42](../filename.ts#L42)              # Single line
[filename.ts:42-51](../filename.ts#L42-L51)       # Range
[directory/](../directory/)                        # Folder
```

This makes references **clickable** in IDEs and GitHub.

## Update Guidelines

### When to Update Docs

**README.md**: When project setup, usage, or key concepts change
**ARCHITECTURE_OVERVIEW.md**: When architecture, patterns, or design changes
**AI_ONBOARDING.md**: When doc structure or navigation changes
**ADRs**: When architectural decisions are made or revised
**Claude Sessions/**: Automatically on context limit or manual request

### Who Updates

- **AI assistants**: Update docs as part of implementing changes
- **Users**: Review and approve doc updates
- **Both**: Collaborate on ADRs for major decisions

## Best Practices for AI

### DO
✅ Read docs before asking questions
✅ Reference docs when explaining decisions
✅ Update docs when making changes
✅ Create ADRs for architectural changes
✅ Use file/line references in explanations
✅ Check session summaries for prior context

### DON'T
❌ Make changes without understanding rationale
❌ Skip updating docs after refactors
❌ Ignore existing patterns and conventions
❌ Ask questions answered in docs
❌ Create new doc files without good reason
❌ Duplicate information across docs

## Project Status (As of October 2025)

**Current Phase**: Episode-based architecture complete, ready for graph commit testing

**Recent Work**:
- ✅ Episode naming system with LLM + user approval
- ✅ Optimal chunking (one episode per worker)
- ✅ Metadata grouping for graph queries
- ✅ Comprehensive documentation system

**Next Steps**:
- Test retroactive commit on Arthur AI session
- Add custom entity types for Graphiti
- Build Clay table integration

**Known Issues**:
- None (all previous issues resolved)

See [Claude Sessions/SESSION_SUMMARY_2.md](Claude%20Sessions/SESSION_SUMMARY_2.md) for detailed context.

## Communication Style

When working with this user:
- **Be concise**: User values clarity over verbosity
- **Reference docs**: Point to files/lines instead of repeating
- **Ask when unclear**: Don't guess architectural decisions
- **Show tradeoffs**: Explain pros/cons of approaches
- **Think like CTO**: User wants best engineering practices

## Getting Help

If you're stuck:
1. **Check session summaries** - Was this solved before?
2. **Read relevant ADR** - Is there documented rationale?
3. **Ask user** - Explain what's unclear and why

## Meta: About This File

This file was created to solve a problem:

**Problem**: AI assistants waste time navigating docs, asking redundant questions, and missing prior context.

**Solution**: Single entry point (this file) that explains where everything is and when to read it.

**Result**: AI assistants get context in minutes, not hours. Users don't repeat themselves.

If this file isn't serving that purpose, update it or tell the user it needs improvement.

---

**Ready to start?** Read [README.md](../README.md) next, then come back here if you need navigation help.
