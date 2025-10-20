---
description: Load complete project context for new session
---

# Onboard: Load Project Context

You are loading context for the Helldiver research project. This ensures you have all necessary information to continue work.

## Step 1: Read Core Context Files

Read these files **in order**:

1. **CLAUDE.md** (if you haven't already - skip if just read)
   - Critical rules (never break these)
   - Design rationale (why we built it this way)
   - File map (where things are)

2. **docs/CURRENT_WORK.md** (MOST IMPORTANT - read completely)
   - Active Focus (what we're working on NOW)
   - What We Just Figured Out (recent decisions)
   - Active Research Sessions (in-flight work)
   - Immediate Next Steps (ordered tasks)
   - Open Questions (prioritized by High/Medium/Future)
   - Key Learnings This Session

## Step 2: Check Git History

Run these commands:

```bash
git log --oneline -10
```

This shows recent commits. Note the most recent commit message.

```bash
git status
```

This shows any uncommitted changes currently in progress.

## Step 3: Determine Context Depth Needed

**Quick onboard** (daily work, continuing from yesterday):
- You've read CLAUDE.md and CURRENT_WORK.md
- You've checked git log
- This is usually sufficient

**Deep onboard** (after break, forgot context, new computer):
- Also read: **docs/GRAPH_ARCHITECTURE.md** (if graph-related work)
- Also read: Latest **docs/archive/sessions/SESSION_SUMMARY_*.md**
  - Find latest: `ls docs/archive/sessions/ | grep SESSION_SUMMARY | sort | tail -1`
  - This gives deep conversation context

## Step 4: Check for Graph-Related Work

If CURRENT_WORK.md mentions:
- Group ID strategy
- Custom entities
- Graph schema
- Graphiti
- Neo4j
- MCP integration

Then also read: **docs/GRAPH_ARCHITECTURE.md**

## Step 5: Output Summary

After reading all necessary files, output EXACTLY this format:

```
✓ Context Loaded

Last Commit: [first line from git log -1]
Active Focus: [from CURRENT_WORK.md "Active Focus" section]
Status: [from CURRENT_WORK.md - current project status]

Next Steps:
1. [First item from CURRENT_WORK.md "Immediate Next Steps"]
2. [Second item if exists]

Open Questions: [count] ([list high-priority ones])

Ready to continue! What would you like to work on?
```

**Keep output concise** - context is loaded, don't repeat entire docs.

## Example Output

```
✓ Context Loaded

Last Commit: fix: Add reference_time to Graphiti API call
Active Focus: Building optimal knowledge graph architecture
Status: Active development on custom entities research, group_id strategy under review

Next Steps:
1. Complete custom entities research (continue refinement)
2. Decide group_id strategy (single global vs hierarchical)

Open Questions: 3 High Priority
- Custom entities: Use them? Which types?
- Group ID strategy: Single global vs hierarchical?
- Schema rigidity: How much flexibility vs structure?

Ready to continue! What would you like to work on?
```

## Notes

- **Do not** read docs/ARCHITECTURE_OVERVIEW.md unless specifically needed (it's reference material)
- **Do not** read all session summaries (only latest if doing deep onboard)
- **Do not** dump entire file contents to user (summarize key points)
- **Time budget**: This should take <30 seconds total
