---
description: Run commit checklist, update documentation, write rich commit message
---

# Commit: Automated Documentation and Git Workflow

You are running the commit workflow for Helldiver project. This ensures all documentation stays current and commit messages capture the full context.

## Step 1: Show What Changed

Run:
```bash
git diff
```

Display to user:
- First 100 lines of diff
- If more: "... [X more lines, Y more files]"

## Step 2: Ask Why (CRITICAL - ALWAYS ASK)

Ask user:
```
Why did you make these changes? (1-2 sentences explaining the reason/problem you solved)
```

**Wait for user's answer. Do not proceed without it.**

This answer is GOLD - it captures the "why" that git diff doesn't show.

## Step 3: Analyze What Changed

Based on git diff and user's "why" answer, determine:

1. **Change type**: feat, fix, refactor, docs, perf, test, chore
2. **Scope**: What part of system (graphiti integration, episode naming, etc.)
3. **Impact**: Does this change architecture, user workflow, or implementation only?

## Step 4: Decide Which Files to Update

### ALWAYS UPDATE:
- ✅ **docs/CURRENT_WORK.md** (every commit updates this)

### UPDATE IF:

| If you changed... | Then update... | How... |
|-------------------|----------------|--------|
| Installation steps, dependencies | **README.md** | Update "Installation" section |
| User-facing commands, flags | **README.md** | Update "Usage" section |
| High-level architecture | **README.md** | Update "Key Architecture Principles" |
| Discovered new critical rule from debugging | **CLAUDE.md** | Add to "Critical Rules" with WHY and cost |
| Where we left off mentally | **CLAUDE.md** | Update "Last Session Recap" |
| Design rationale changed | **CLAUDE.md** | Update "Design Rationale" |
| System architecture (new component, state machine change) | **docs/ARCHITECTURE_OVERVIEW.md** | Update relevant section |
| Data flow changed | **docs/ARCHITECTURE_OVERVIEW.md** | Update data flow description |
| Key function signature changed | **docs/ARCHITECTURE_OVERVIEW.md** | Document new signature |
| Group ID strategy decided/changed | **docs/GRAPH_ARCHITECTURE.md** | Update "Group ID Strategy" section |
| Custom entity schema designed/modified | **docs/GRAPH_ARCHITECTURE.md** | Update "Custom Entity Types" |
| Discovered insight about Graphiti | **docs/GRAPH_ARCHITECTURE.md** | Add to "Key Insights" |
| Open question answered | **docs/GRAPH_ARCHITECTURE.md** | Move from "Open Questions" to relevant section |
| **Major architectural decision** | **docs/decisions/** | Create new ADR (see below) |

### When to Create New ADR:

Create `docs/decisions/00X-decision-name.md` if:
- ✅ Major architectural decision made (changes system design fundamentally)
- ✅ Chose between multiple approaches (need to document alternatives)
- ✅ Decision has long-term consequences (affects future development)

**ADR Template:**
```markdown
# ADR [number]: [Title]

**Status**: Accepted

## Context
[What problem are we solving? What constraints exist?]

## Decision
[What did we decide to do?]

## Alternatives Considered
1. **[Alternative 1]**: [Why we didn't choose this]
2. **[Alternative 2]**: [Why we didn't choose this]

## Consequences
[What are the implications of this decision?]
- Positive: [Benefits]
- Negative: [Tradeoffs/costs]

## References
[Links to related docs, commits, discussions]
```

Find next ADR number: `ls docs/decisions/ | grep -oP '\d+' | sort -n | tail -1` then add 1.

## Step 5: Update docs/CURRENT_WORK.md

**Read the file first**, then update relevant sections:

### Always Update:
- **"Last Updated"**: Set to today's date (2025-01-19 format)

### Update Based on What Was Accomplished:

**If task was completed:**
- Move from "Immediate Next Steps" to "What We Just Figured Out"
- Add brief description of what was completed and result

**If open question was answered:**
- Mark question as resolved (move from "Open Questions" to "What We Just Figured Out")
- Include the answer

**If active research progressed:**
- Update "Active Research Sessions" status
- Update "Next Step" for that session

**If new task discovered:**
- Add to "Immediate Next Steps" (ordered by priority)

**If new question discovered:**
- Add to "Open Questions" (categorize as High/Medium/Future priority)

**If we learned something from debugging:**
- Add to "Key Learnings This Session"
- Format: **[Learning]** - [Why it matters] - [Reference]

**If active focus changed:**
- Update "Active Focus" section

### Keep Structure:
- Don't add new sections (follow existing format)
- Maintain priority levels for Open Questions
- Keep "Immediate Next Steps" ordered

## Step 6: Update Other Files (If Needed)

Based on decision tree in Step 4, update:
- README.md (if installation/usage changed)
- CLAUDE.md (if critical rule or session recap changed)
- ARCHITECTURE_OVERVIEW.md (if architecture changed)
- GRAPH_ARCHITECTURE.md (if graph design changed)
- Create new ADR (if major architectural decision)

## Step 7: Generate Commit Message

Use this format:

```
<type>(<scope>): <short summary>

Why: [User's explanation from Step 2]

[Optional: Additional context about the problem]

Changes:
- [Specific change 1 with file:line if relevant]
- [Specific change 2 with why it matters]
- [Specific change 3]

[If architectural decision]
Alternatives Considered:
- [Alternative 1]: [Why not chosen]
- [Alternative 2]: [Why not chosen]

[If created/updated docs]
Documentation:
- Updated: [list of docs updated]
- Created: [list of docs created]

[If relevant]
See: [Reference to ADR, session summary, or other doc]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Type**: feat, fix, refactor, docs, perf, test, chore
**Scope**: graphiti, episodes, graph-schema, docs, etc. (optional)

### Commit Message Examples:

**Example 1: Bug fix**
```
fix(graphiti): Add timezone-aware datetime to reference_time

Why: Graphiti API requires timezone-aware datetime for temporal indexing.
Missing timezone caused NULL valid_at field, breaking MCP temporal search.

Discovered during first real commit attempt. Spent 2 hours debugging
"episodes exist but MCP can't find them" before realizing naive datetimes
were the issue.

Changes:
- graphiti_client.py:87 - Changed datetime.now() to datetime.now(timezone.utc)
- Ensures valid_at field populated correctly for MCP search
- Added import for timezone from datetime module

Documentation:
- Updated: docs/CURRENT_WORK.md (added to Key Learnings)
- Updated: CLAUDE.md (added to Critical Rules)

See: docs/archive/sessions/SESSION_SUMMARY_4.md for debugging journey

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Example 2: Feature with architecture decision**
```
feat(graph-schema): Implement custom entity types for Graphiti

Why: Standard entity extraction was missing domain-specific relationships.
Custom entities (ResearchFinding, Critique, Hypothesis) capture research
structure better than generic entities.

Changes:
- graphiti_client.py:120-180 - Added custom entity schemas
- main.py:850-900 - Modified commit_research_episode to use custom entities
- Added confidence_level and source_quality attributes

Alternatives Considered:
- Default Graphiti entities: Too generic, lost research-specific structure
- Single "Research" entity type: Didn't differentiate findings vs critiques
- Custom entities (chosen): Preserves research semantics, enables targeted queries

Documentation:
- Created: docs/decisions/004-custom-entity-schema.md
- Updated: docs/GRAPH_ARCHITECTURE.md (Custom Entity Types section)
- Updated: docs/CURRENT_WORK.md (completed task, answered open question)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Step 8: Show Summary and Ask Approval

Display to user:

```
📝 Commit Summary

Files changed:
[List from git diff --stat]

Documentation updated:
[List of docs you updated]

Proposed commit message:
───────────────────────────────────────
[Full commit message from Step 7]
───────────────────────────────────────

Ready to commit with this message? (yes/no)
```

## Step 9: Commit and Push

If user says "yes":

```bash
git add .
git commit -m "[commit message]"
git push
```

Say:
```
✓ Committed and pushed

Commit: [first line of commit message]
Docs updated: [count] files
Synced to remote: ✓

You can switch computers now. Run /onboard on the new machine to continue.
```

If user says "no":
```
Okay, commit cancelled. Let me know if you want to adjust the message or make more changes.
```

## Notes

- **Always ask "why"** - Don't skip Step 2, this is the most important part
- **Always update CURRENT_WORK.md** - This is the heartbeat of the project
- **Use conversation context** - The user's explanation might reveal impact you didn't see in git diff
- **Be thorough but fast** - Aim for 1-2 minute workflow (not including user response time)
- **Rich commit messages** - Capture WHY, not just WHAT. Future you will thank you.
