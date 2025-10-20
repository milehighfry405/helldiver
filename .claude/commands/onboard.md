---
description: Load complete project context for new session
allowed-tools: [Read, Bash, Glob]
---

# Onboard: Load Project Context

You are an **expert context loader** for the Helldiver research project. Your mission: Get future Claude up to speed in <30 seconds with complete, relevant context.

**Your expertise**:
- Deep understanding of Helldiver's documentation structure
- Intelligent context prioritization (what's needed NOW vs nice-to-have)
- Semantic analysis of what type of work is active
- Concise context summarization

**Your standards**: SEAL Team 6. Load exactly what's needed. No more, no less. Fast and complete.

---

## Step 1: Read Core Context Files (ALWAYS)

<step_1_instructions>
Read these files **in order** (use Read tool):

1. **CLAUDE.md**
   - Critical rules (never break these)
   - Design rationale (why we built it this way)
   - File map (where things are)
   - Last session recap

2. **docs/CURRENT_WORK.md** (MOST IMPORTANT)
   - Active Focus (what we're working on NOW)
   - What We Just Figured Out (recent wins)
   - Active Research Sessions (in-flight work)
   - Immediate Next Steps (ordered tasks)
   - Open Questions (prioritized)
   - Key Learnings This Session

**Why these matter**:
- CLAUDE.md: Prevents repeating painful mistakes (timezone bugs, group_id validation, etc.)
- CURRENT_WORK.md: Tells you the mental state and priorities RIGHT NOW
</step_1_instructions>

---

## Step 2: Load Latest Session Summary (ALWAYS)

<step_2_instructions>
**Find and read the latest session summary**:

```bash
ls docs/archive/sessions/ | grep SESSION_SUMMARY | sort | tail -1
```

Then read that file using Read tool.

**Why this is ALWAYS needed**:
- User switches computers frequently
- Session summaries capture conversation context (not just code changes)
- Contains debugging journeys, user questions, decisions that won't be in git log
- This is how continuity works across computers

**What to extract**:
- What We Worked On (the journey)
- Problems Solved (debugging context)
- Decisions Made (WHY we chose things)
- User Questions & Clarifications (confusion points to avoid repeating)
- Next Session Should (what's ready to continue)

This gives you the **mental state** from last session, not just code state.
</step_2_instructions>

---

## Step 3: Check Git History

<step_3_instructions>
Run these commands:

```bash
git log --oneline -10
```

This shows recent commits. Note:
- Most recent commit (what was just completed)
- Pattern of work (are we iterating on one thing or jumping topics?)
- Frequency (how long since last work?)

```bash
git status
```

This shows:
- Uncommitted changes (work in progress)
- Current branch
- Sync status with remote

**Combine git context with session summary**:
- Git log shows WHAT changed
- Session summary shows WHY and HOW (the journey)
- Together: Complete picture
</step_3_instructions>

---

## Step 4: Load Graph Architecture Context (IF Needed)

<step_4_instructions>
**Determine if graph-related work is active**:

Check if CURRENT_WORK.md Active Focus mentions:
- Group ID strategy
- Custom entities
- Graph schema
- Graphiti
- Neo4j
- MCP integration
- Episode structure

**If YES, also read**: `docs/GRAPH_ARCHITECTURE.md`

**Why conditional**:
- Not all work touches graph (could be docs, plugins, refactoring)
- Only load if semantically relevant to current work
- Saves time when not needed

**What to extract from GRAPH_ARCHITECTURE.md**:
- Current group_id strategy
- Custom entity design status
- Open questions about graph structure
- Key insights/learnings

**If NO**: Skip this file (not needed for current work)
</step_4_instructions>

---

## Step 5: Synthesize and Output Context Summary

<step_5_instructions>
After reading all necessary files, synthesize into concise output:

```
✓ Context Loaded

Last Commit: [first line from git log -1]
Last Session: [topic from SESSION_SUMMARY filename]
Active Focus: [from CURRENT_WORK.md "Active Focus" section]

Next Steps:
1. [First item from CURRENT_WORK.md "Immediate Next Steps"]
2. [Second item if exists]
3. [Third item if exists]

Open Questions: [count] ([list HIGH priority ones only])

[If graph work is active]
Graph Status: [1 sentence from GRAPH_ARCHITECTURE.md or CURRENT_WORK.md]

Ready to continue! What would you like to work on?
```

**Quality standards**:
- ✅ Concise (not dumping entire file contents)
- ✅ Actionable (user knows what to do next)
- ✅ Complete (nothing important missing)
- ✅ Fast (<30 seconds total time)
</step_5_instructions>

---

## Example Output

```
✓ Context Loaded

Last Commit: refactor: Rebuild plugins with AI-native logic
Last Session: Plugin system migration (SESSION_SUMMARY_6)
Active Focus: Rebuilding documentation plugins with best-in-class prompt engineering

Next Steps:
1. Rebuild /onboard plugin to ALWAYS load session summary
2. Enhance /session-end with XML tags and few-shot examples
3. Test all rebuilt plugins end-to-end

Open Questions: 2 High Priority
- Should /commit use semantic ADR matching or keep keyword search? (RESOLVED: semantic)
- How to handle evolving ADRs vs creating new ones? (RESOLVED: update existing)

Ready to continue! What would you like to work on?
```

---

## Quality Standards (Never Compromise)

<quality_checklist>
Before outputting to user, verify:

- ✅ Read CLAUDE.md (critical rules loaded)
- ✅ Read CURRENT_WORK.md (current state understood)
- ✅ Read latest SESSION_SUMMARY (conversation context loaded)
- ✅ Checked git log (recent commits understood)
- ✅ Checked git status (current changes noted)
- ✅ Read GRAPH_ARCHITECTURE.md if relevant (graph context loaded if needed)
- ✅ Output is concise (not dumping files)
- ✅ Next steps are clear (user knows what to do)
- ✅ Took <30 seconds

**If ANY of these are false, go back and fix.**

This is SEAL Team 6 level onboarding. Fast, complete, actionable.
</quality_checklist>

---

## Notes for Excellence

- **ALWAYS read session summary** - This is the continuity mechanism, not optional
- **Use semantic analysis** - Determine if graph docs are needed based on current work
- **Synthesize, don't dump** - User doesn't need entire file contents, just key points
- **Be actionable** - User should know exactly what to do next
- **Trust the system** - Session summaries + CURRENT_WORK.md capture everything needed
- **Time budget** - This should take <30 seconds total (fast reads, concise output)
