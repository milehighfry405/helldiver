# Commit Checklist for Claude Code

**Purpose**: This checklist ensures documentation stays current with code changes. Claude Code should follow this checklist **before every git commit**.

---

## 🚨 CRITICAL: Always Read This Before Committing

**If you don't remember this file, READ IT NOW before proceeding with any commit.**

Location: `docs/COMMIT_CHECKLIST.md`

**Why this matters**: Even if context window is full of other work, you MUST re-read this file when user says "commit" to ensure docs stay current.

---

## When User Says "Commit" or "Ready to commit"

**STEP 0**: If you haven't read this file recently, **READ IT NOW** before proceeding.

Claude Code must **automatically** run through this checklist without being asked:

### 1. Check if ADR Needed (Architecture Decision Record)

**Question**: Did this work involve an architectural decision?

**Architectural decisions include**:
- ✅ Changing how data flows through the system
- ✅ Adding/removing major components or modules
- ✅ Changing API contracts or interfaces
- ✅ Performance optimization strategies
- ✅ Security/privacy design decisions
- ✅ Database schema or storage decisions
- ✅ Third-party integration patterns

**NOT architectural decisions**:
- ❌ Bug fixes with no design impact
- ❌ Adding comments or improving readability
- ❌ Small refactors following existing patterns
- ❌ Dependency version updates

**If YES** → Create or update ADR in `docs/decisions/XXX-decision-name.md`

### 2. Check if README Needs Update

**Question**: Did this work change how users interact with the system?

**README changes needed if**:
- ✅ Installation steps changed
- ✅ Usage commands changed
- ✅ New features added (user-facing)
- ✅ Configuration options changed
- ✅ Dependencies added/removed

**If YES** → Update `README.md` with changes

### 3. Check if ARCHITECTURE_OVERVIEW Needs Update

**Question**: Did this work change system architecture or design patterns?

**Architecture overview changes needed if**:
- ✅ State machine transitions changed
- ✅ Data flow changed
- ✅ New design patterns introduced
- ✅ File structure changed
- ✅ Key concepts changed

**If YES** → Update `docs/ARCHITECTURE_OVERVIEW.md`

### 3.5. Check if GRAPH_ARCHITECTURE Needs Update

**Question**: Did this work involve graph design decisions?

**Graph architecture changes needed if**:
- ✅ Group ID strategy changed or decided
- ✅ Custom entities added/removed/modified
- ✅ Schema design changed
- ✅ Integration patterns changed (Claude Skills, MCP, etc.)
- ✅ New graph-related open questions identified

**If YES** → Update `docs/GRAPH_ARCHITECTURE.md`

### 3.6. Check if CURRENT_WORK Needs Update

**Question**: Did this work complete a task, answer a question, or create new next steps?

**Current work changes needed if**:
- ✅ Completed an item from "Immediate Next Steps"
- ✅ Answered an "Open Question"
- ✅ Made progress on "Active Research Sessions"
- ✅ Discovered new work that needs to be done
- ✅ Changed priorities or focus

**If YES** → Update `docs/CURRENT_WORK.md` with:
- Move completed items from "Next Steps" to "What We Just Figured Out"
- Update "Active Research Sessions" status
- Mark answered questions as resolved
- Add new next steps or open questions
- Update "Last Updated" timestamp

### 4. Check if Code Comments Sufficient

**Question**: Will future AI assistants understand WHY this code exists?

**Add comments if**:
- ✅ Non-obvious design decisions in code
- ✅ Workarounds for edge cases
- ✅ Performance-critical sections
- ✅ Complex algorithms

**Format**:
```python
# ARCHITECTURE NOTE: Reason for this design choice
# IMPORTANT: Critical behavior to maintain
# PERFORMANCE: Why this optimization matters
```

### 5. Generate Commit Message with Context

**Format**:
```
<type>: <short summary>

<detailed explanation>
- What changed (bullet points)
- Why it changed
- Impact on system

Documentation:
- [Updated/Created] <doc files changed>

See: docs/Claude Sessions/SESSION_SUMMARY_X.md for full context
```

**Types**: `feat`, `fix`, `refactor`, `docs`, `perf`, `test`, `chore`

---

## Commit Checklist (Quick Reference)

Before every commit, Claude Code checks:

```
□ ADR needed? (architectural decision?)
  └─→ If YES: Create/update docs/decisions/XXX-*.md

□ README updated? (user-facing changes?)
  └─→ If YES: Update README.md

□ Architecture overview updated? (design changes?)
  └─→ If YES: Update docs/ARCHITECTURE_OVERVIEW.md

□ Graph architecture updated? (graph design decisions?)
  └─→ If YES: Update docs/GRAPH_ARCHITECTURE.md

□ Current work updated? (completed tasks, new next steps?)
  └─→ If YES: Update docs/CURRENT_WORK.md

□ Code comments sufficient? (complex logic documented?)
  └─→ If YES: Add inline comments

□ Commit message includes:
  - What changed
  - Why it changed
  - Reference to session summary (if applicable)
  - List of docs updated
```

---

## Examples

### Example 1: Bug Fix (No ADR)

**Change**: Fixed episode name truncation bug

**Checklist**:
- ❌ ADR needed? NO - bug fix, no architectural change
- ❌ README update? NO - usage unchanged
- ❌ Architecture overview? NO - design unchanged
- ✅ Code comments? Added comment explaining edge case
- ✅ Commit message:
```
fix: Handle long episode names in filesystem creation

Fixed bug where episode names >255 chars would crash.
Now truncates to 200 chars with ellipsis.

Documentation:
- No doc changes (bug fix only)
```

### Example 2: New Feature (ADR Required)

**Change**: Added multi-language support for research workers

**Checklist**:
- ✅ ADR needed? YES - architectural decision about language handling
  → Created `docs/decisions/004-multilingual-research-strategy.md`
- ✅ README update? YES - new config option for language
  → Updated README.md with `RESEARCH_LANGUAGE` env var
- ✅ Architecture overview? YES - new worker initialization flow
  → Updated docs/ARCHITECTURE_OVERVIEW.md with language flow diagram
- ✅ Code comments? Added comments in worker prompt templates
- ✅ Commit message:
```
feat: Add multi-language support for research workers

Added ability to conduct research in multiple languages (English, Spanish, French, German, Japanese).

Changes:
- New RESEARCH_LANGUAGE env var (defaults to "english")
- Worker prompts now include language instructions
- LLM responses validated for target language

Documentation:
- Created docs/decisions/004-multilingual-research-strategy.md
- Updated README.md with configuration
- Updated docs/ARCHITECTURE_OVERVIEW.md with flow diagram

See: docs/Claude Sessions/SESSION_SUMMARY_3.md for implementation context
```

### Example 3: Refactor (ADR May Be Needed)

**Change**: Refactored episode naming to use strategy pattern

**Checklist**:
- ✅ ADR needed? YES - design pattern change
  → Updated `docs/decisions/001-episode-naming-strategy.md` with new approach
- ❌ README update? NO - user-facing behavior unchanged
- ✅ Architecture overview? YES - design pattern changed
  → Updated docs/ARCHITECTURE_OVERVIEW.md with strategy pattern explanation
- ✅ Code comments? Added comments explaining strategy interface
- ✅ Commit message:
```
refactor: Use strategy pattern for episode naming

Refactored episode naming to use strategy pattern for better extensibility.
Allows custom naming strategies without modifying core code.

Changes:
- Created EpisodeNamingStrategy interface
- Implemented LLMNamingStrategy (existing behavior)
- Added TemplateNamingStrategy (new option)

Documentation:
- Updated docs/decisions/001-episode-naming-strategy.md
- Updated docs/ARCHITECTURE_OVERVIEW.md with pattern explanation

See: docs/Claude Sessions/SESSION_SUMMARY_3.md for full context
```

---

## For Claude Code: How to Use This

### When user says: "commit" / "ready to commit" / "let's commit"

**Your workflow**:

1. **Read this file** (`docs/COMMIT_CHECKLIST.md`)
2. **Run through checklist automatically** (don't ask user about each item)
3. **Make doc updates** (ADR, README, Architecture Overview as needed)
4. **Show user** what docs you updated
5. **Generate commit message** following format above
6. **Ask user**: "Ready to commit with this message?"

### Example interaction

```
User: "Okay, commit this work"

Claude: "Running pre-commit checklist..."

[Claude checks checklist internally]

Claude: "Documentation updates made:
- Created docs/decisions/004-multilingual-research-strategy.md (new architectural decision)
- Updated README.md (new RESEARCH_LANGUAGE config)
- Updated docs/ARCHITECTURE_OVERVIEW.md (new language flow)

Proposed commit message:

feat: Add multi-language support for research workers
...

Ready to commit?"

User: "Yes, commit it"

[Claude runs git commit]
```

---

## For User: Your Role

**You only need to**:
1. Say "commit" when ready
2. Review Claude's doc updates and commit message
3. Approve or request changes

**You don't need to**:
- Remember checklist items
- Decide which docs to update
- Write ADRs yourself
- Format commit messages

**Claude handles all that automatically** by following this checklist.

---

## Integration with Session Summaries

When commit message references session summary, use this format:

```
See: docs/Claude Sessions/SESSION_SUMMARY_X.md for full context
```

This creates a **trail** from git history → session summary → complete context.

Future AI assistants can:
1. Read git log
2. See session summary reference
3. Read that summary for full context
4. Understand the journey, not just the destination

---

## Updating This Checklist

If user wants to add/remove checklist items, edit this file.

Claude Code will follow whatever this checklist says before commits.

---

## Benefits

✅ **No mental overhead** - User just says "commit", Claude handles docs
✅ **Consistent docs** - Checklist ensures nothing forgotten
✅ **Git-integrated** - Ties into workflow user already knows
✅ **Auditable** - Commit messages reference docs and summaries
✅ **Future-proof** - Future AI reads commit → summary → full context

---

## TL;DR

**User**: "Commit"
**Claude**: Checks this file → Updates docs → Proposes commit message → Asks approval
**User**: "Yes" (approves)
**Claude**: Commits with full context

That's it. Documentation stays current with zero user effort.
