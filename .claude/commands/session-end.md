---
description: Generate comprehensive session summary from conversation context and commit automatically
---

# Session-End: Save Session Summary

You are generating a comprehensive session summary that captures the FULL CONTEXT of this work session, including the conversation journey, not just code changes.

## Critical: Use Full Conversation Context

**This is NOT just a git log summary.**

Use your **ENTIRE CONTEXT WINDOW** to extract:
- What problems we tried to solve (the journey)
- What we tried (including failures)
- What errors we encountered (exact messages)
- What questions the user asked (their confusion points)
- What decisions we made (and WHY)
- What we learned (insights from debugging)

**The git log only shows the final state. This summary shows HOW we got there.**

## Step 1: Gather Baseline Context

Run these commands:

```bash
git log --oneline -20
```

```bash
git diff --stat HEAD~5..HEAD
```

Read these files:
- `docs/CURRENT_WORK.md` (what we were working on)

Note the time span of commits to estimate session duration.

## Step 2: Find Next Session Number

Run:
```bash
ls docs/archive/sessions/ 2>/dev/null | grep SESSION_SUMMARY | sed 's/SESSION_SUMMARY_//' | sed 's/.md//' | sort -n | tail -1
```

If no sessions exist yet, start with 5 (continuing from SESSION_SUMMARY_4).
Otherwise, increment the number by 1.

## Step 3: Extract from Conversation Memory

**CRITICAL**: Search your FULL CONTEXT WINDOW to answer these questions:

<extraction_questions>
1. **What problem were we trying to solve?**
   - User's goal for this session
   - What motivated the work

2. **What did we try?**
   - First attempt (what happened)
   - Second attempt (what happened)
   - Third attempt (what happened)
   - Include failures, not just successes

3. **What errors did we encounter?**
   - Exact error messages (from conversation)
   - Line numbers where errors occurred
   - Root causes we discovered

4. **What questions did the user ask?**
   - Their confusion points (exact quotes)
   - My explanations
   - Why they were confused (helps future sessions)

5. **What decisions did we make?**
   - What we decided
   - WHY we chose it (from conversation)
   - What alternatives we considered
   - What we explicitly decided NOT to do

6. **What did we learn?**
   - Insights from debugging
   - Discoveries about the system
   - Lessons that should become "Critical Rules"
   - Cost of learning (time spent debugging)

7. **Where did we leave off?**
   - Mental state (not just code state)
   - What's ready to continue
   - What's blocking us
   - What should happen next

8. **What should the next session do?**
   - Next logical steps
   - Open questions to address
   - Tests or validations needed
</extraction_questions>

## Step 4: Generate Comprehensive Summary

Create: `docs/archive/sessions/SESSION_SUMMARY_[N].md`

Use Anthropic prompt engineering best practices:
- XML tags for structure
- Be explicit about sources
- Prioritize conversation context over file context

**Template:**

```markdown
# SESSION_SUMMARY_[N].md

**Date**: [Today's date: YYYY-MM-DD]
**Duration**: [Estimate from git log timestamps or conversation flow]
**Status**: [From CURRENT_WORK.md - current project status]

---

## Executive Summary

[2-3 sentences: What we accomplished this session]

**Key Achievement**: [Main thing we completed]
**Key Decision**: [Most important decision made]
**Status**: [Ready to continue / Blocked by X / Completed milestone]

---

## What We Worked On

[Synthesize from conversation - tell the STORY, not just list commits]

**Context**: [Why we were working on this - user's goal]

**Journey**: [Narrative of what happened]
- Started with [goal]
- First tried [approach], which [result]
- Then tried [approach], which [result]
- Finally [outcome]

[This should read like a story that future you can follow]

---

## Problems Solved

[Extract from conversation - include the debugging journey]

### Problem 1: [Error/Issue Name]

**Symptom**: [What we observed]
**Error Message**: [Exact error from conversation]
```
[Full error if available]
```
**Root Cause**: [Why it happened - from our investigation]
**Investigation**: [How we found it - the debugging journey]
- [Step 1 of debugging]
- [Step 2 of debugging]
- [Breakthrough moment]

**Solution**: [What we changed]
- File: [file:line]
- Change: [Specific change]
- Why it works: [Explanation]

**Time Spent**: [Estimate from conversation]
**Key Insight**: [What we learned that's worth remembering]

[Repeat for each problem - extract from conversation]

---

## Decisions Made

[Extract from conversation - what did we DECIDE and WHY]

### Decision 1: [What We Decided]

**Context**: [Why we needed to decide]
**Options Considered**:
1. **[Option A]**: [Why we considered it] → [Why we didn't choose it]
2. **[Option B]**: [Why we considered it] → [Why we didn't choose it]
3. **[Option C]**: [Why we chose this] → **CHOSEN**

**Rationale**: [From conversation - why we chose this]
**Consequences**: [What this means going forward]
**Documented**: [Link to ADR if created, or commit hash]

[Repeat for each major decision]

---

## User Questions & Clarifications

[GOLD - extract from conversation]

**This section captures confusion points that might come up again.**

### Question 1: [User's question]

**User asked**: "[Exact quote from conversation]"

**Context**: [What prompted this question]

**I explained**: [My answer - summary]

**Why this matters**: [Why user was confused - prevents repeat confusion]

[Repeat for each significant question]

---

## Code Changes

[Annotate git log with WHY from conversation]

### Commits This Session

[List commits from git log, but add context from conversation]

1. **[Commit hash]**: [Commit message first line]
   - Why: [From conversation, not just commit message]
   - Impact: [What this enabled or fixed]

### Files Changed

[From git diff --stat, annotated with purpose]

- `[file:line-range]` - [What changed] ([WHY from conversation])

**Example**:
- `main.py:916-918` - Group ID format changed to underscores (Graphiti validation rejects slashes, discovered after 20 min debugging)

---

## Key Learnings

[Extract from conversation - what did we LEARN that's worth capturing]

Format: **[Learning]** - [Why it matters] - [Cost/Impact] - [Reference]

1. **[Lesson from debugging]** - [Why this is important to remember] - [Time/cost this lesson took] - See: [commit/doc reference]

**Example**:
1. **Graphiti requires timezone-aware datetimes** - Naive datetimes set valid_at to NULL, breaking MCP search - Cost: 2 hours debugging - See: CLAUDE.md Critical Rule #2

[These should become Critical Rules in CLAUDE.md if not already there]

---

## Conversation Highlights

[Extract "aha" moments and key exchanges from conversation]

**These are the moments that led to breakthroughs:**

[Quote or paraphrase key conversation moments that won't be obvious from commits]

**Example**:
```
User: "so each episode is going to have a different group id?"

Me: "No - all workers in the same research phase share one group_id.
This enables querying by research phase. Per ADR-003, this is the correct design."

User: "ah thank you for the reminder"
```

**Why this matters**: User was previously confused about this, might need reminder again.

---

## Next Session Should

[Based on conversation context and CURRENT_WORK.md]

1. **Immediate**: [What's ready to do right now]
2. **Soon**: [What should happen after that]
3. **Eventually**: [Future consideration]

**Ready to**: [What state we're in - can continue or blocked?]

**Blockers**: [Any blockers from conversation - external APIs, missing info, etc.]

**Recommended next command**: [Exact command to run, if applicable]

---

## Technical Context for AI

**Current State**: [1 sentence from CURRENT_WORK.md Active Focus]
**Last Commit**: [From git log -1]
**Mental State**: [Where we left off - from conversation]
**Context Loaded**: [Is everything ready for next session? Any setup needed?]

---

## Session Statistics

**Commits**: [Count from git log]
**Files Changed**: [Count from git diff --stat]
**Problems Solved**: [Count from Problems Solved section]
**Decisions Made**: [Count from Decisions Made section]
**Key Learnings**: [Count from Key Learnings section]
**Time Span**: [From first to last commit, or conversation estimate]

---

## Quality Checklist

This summary should answer:
- ✅ "What happened this session?" (the story, not just commits)
- ✅ "Why did we make change X?" (from conversation, not just code)
- ✅ "What did user struggle with?" (their questions and confusion)
- ✅ "What would I forget in 2 weeks?" (key insights and lessons)
- ✅ "Where do I pick up next time?" (mental state and next steps)

If this summary doesn't answer all of these, it's incomplete.

---

**End of SESSION_SUMMARY_[N].md**
```

## Step 5: Commit the Summary Automatically

Run:
```bash
git add docs/archive/sessions/SESSION_SUMMARY_[N].md
git commit -m "docs: Add SESSION_SUMMARY_[N] - [brief description from session]"
git push
```

## Step 6: Output to User

Say:
```
✓ Session summary saved: SESSION_SUMMARY_[N].md
✓ Committed and synced to remote

Summary captured:
- [X] problems solved
- [Y] decisions made
- [Z] key learnings documented
- [W] conversation highlights preserved

Next session should: [first item from "Next Session Should"]

You can switch computers now. Run /onboard on the new machine to continue exactly where we left off.
```

## Notes

- **Use conversation context heavily** - This is the unique value of this summary
- **Don't just summarize git log** - That's lazy and misses the journey
- **Capture user's questions** - These reveal confusion points that might recur
- **Extract debugging journeys** - "Tried A, got error X, tried B, realized Y" is gold
- **Note time costs** - "2 hours debugging this" helps prioritize future work
- **Quality over speed** - Take time to extract rich context from conversation
- **This replaces manual copy/paste** - User no longer copies Claude Code's auto-generated summaries

## Example: What Good Extraction Looks Like

**Bad** (just git log):
```
Problem: Missing reference_time
Solution: Added reference_time parameter
```

**Good** (from conversation):
```
Problem: Missing reference_time parameter

Symptom: Graphiti.add_episode() call crashed with "missing 1 required positional argument"
Error appeared on second attempt (first attempt was different error - group_id validation)

Investigation:
- Checked Graphiti docs, found reference_time is required positional argument
- Checked our code: graphiti_client.py:87 was missing it
- User asked: "should we add debug flag?" but error was obvious enough

Solution: Added reference_time=datetime.now(timezone.utc)
- Must be timezone-aware (naive datetime → NULL valid_at → MCP fails)
- This was discovered earlier in session during MCP debugging

Time: ~30 minutes
Insight: Always check Graphiti API signature before calling
```

**The second one captures the journey.** That's what we want.
