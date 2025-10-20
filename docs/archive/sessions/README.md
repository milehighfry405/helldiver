# Claude Sessions - Session Continuation System

## What This Is

This folder contains **session summary files** that enable seamless continuation of Claude Code conversations when:
- Context window approaches the limit (~200k tokens)
- Moving to a new computer
- Starting a new Claude Code session

These files are **automatically generated** by Claude Code when it runs out of context, or **manually requested** by the user during critical development milestones.

## How It Works

### Automatic Generation

When Claude Code approaches its context limit, it automatically generates a massive, comprehensive summary file that captures:
1. **All user requests** (chronologically ordered)
2. **All code changes** (with file paths, line numbers, and explanations)
3. **All errors and fixes** (what went wrong, how it was fixed)
4. **Current work state** (what was just completed, what's blocked, what's next)
5. **Technical context** (architecture decisions, design patterns, key concepts)
6. **User mental models** (goals, workflow, background context)

### Manual Generation

The user can request a session summary at any time by saying:
> "Generate a session summary like you do when you run out of context"

This is useful before:
- Git commits (to document the journey)
- Computer migrations (to ensure no context loss)
- Major architectural changes (to capture the "why")

## File Naming Convention

```
SESSION_SUMMARY_{number}.md
```

- `SESSION_SUMMARY_1.md` - First session (migration from another computer)
- `SESSION_SUMMARY_2.md` - Second session (current session)
- etc.

Files are numbered sequentially as sessions continue.

## How to Use These Files

### Starting a New Claude Code Session

When you start a new Claude Code session (new chat, new computer, context reset), say:

```
I'm continuing from a previous session. Please read docs/Claude Sessions/SESSION_SUMMARY_{latest}.md
and continue where we left off.
```

Claude will:
1. Read the entire summary
2. Understand all previous work
3. Know exactly what's pending
4. Continue seamlessly without asking questions

### After Reading a Summary

Claude Code will have full context of:
- ✅ What you're building and why
- ✅ All architectural decisions and rationale
- ✅ All code changes made (with file/line references)
- ✅ All bugs encountered and how they were fixed
- ✅ Current blockers and next steps
- ✅ Your goals, workflow, and mental models

## Security and Privacy

### What's Safe to Commit

Session summaries **DO NOT contain**:
- ❌ API keys or credentials
- ❌ Passwords
- ❌ Email addresses or phone numbers
- ❌ Personal identifiable information (PII)
- ❌ Contents of .env files

Session summaries **DO contain**:
- ✅ File paths and line numbers
- ✅ Code snippets and function names
- ✅ Architecture patterns and decisions
- ✅ Git commands and workflow
- ✅ Research queries (business topics like "Arthur AI market analysis")
- ✅ User's technical goals and context

### If Sensitive Data Appears

If a session summary accidentally captures sensitive data:
1. **Don't commit it to git** - Delete the file first
2. **Regenerate** - Ask Claude to regenerate excluding sensitive data
3. **Edit manually** - Remove sensitive lines before committing

**General rule**: Session summaries are **context about code**, not code with secrets. They document the journey, not the keys.

---

## What Gets Captured

### 1. Primary Request and Intent
- What the user asked for (exact quotes)
- What problem we're solving
- Why this work matters

### 2. Key Technical Concepts
- Architecture patterns used
- Design decisions made
- Technologies and frameworks involved

### 3. Files and Code Sections
- Every file changed
- Specific functions modified (with line numbers)
- Code snippets showing before/after
- Why each change was made

### 4. Errors and Fixes
- What went wrong
- User feedback about the error
- How it was fixed
- Status (fixed/pending/blocked)

### 5. Problem Solving
- Problems encountered
- Solutions implemented
- Validation and testing
- Ongoing considerations

### 6. All User Messages
- Chronological log of key user inputs
- Exact quotes for critical decisions

### 7. Pending Tasks
- What's completed (✅)
- What's in progress
- What's blocked (⚠️)
- What's next

### 8. Current Work
- What was just completed
- What's being worked on
- System state snapshot

### 9. Optional Next Step
- Recommended next action
- What user should be asked
- Context for next session

## Best Practices

### For Users

1. **Request summaries before major milestones**
   - Before git commits
   - Before computer migrations
   - After major refactors
   - When conversation gets complex

2. **Keep summaries organized**
   - Number them sequentially
   - Store in this folder only
   - Don't edit them (they're AI-generated)

3. **Reference in git commits**
   - Link to relevant summary in commit messages
   - Helps future you understand the journey

### For Claude Code

1. **Read summaries completely**
   - Don't skim, read every section
   - Understand the full context
   - Note the user's mental models

2. **Continue seamlessly**
   - Don't ask questions already answered in summary
   - Pick up exactly where previous session left off
   - Reference prior decisions when relevant

3. **Update documentation if needed**
   - If summary reveals gaps in docs, fix them
   - Ensure README, ADRs, and ARCHITECTURE_OVERVIEW stay current

## Example Usage

### Scenario 1: Context Window Full

```
User: "Continue working on the episode naming system"

Claude: "I'm approaching my context limit. Let me generate a session summary..."
[Generates SESSION_SUMMARY_2.md]

Claude: "Summary generated at docs/Claude Sessions/SESSION_SUMMARY_2.md.
When you start a new session, ask me to read this file to continue."
```

### Scenario 2: Computer Migration

```
[On old computer]
User: "I'm moving to a new computer. Generate a session summary."
Claude: [Generates SESSION_SUMMARY_3.md]
User: [Commits to git, pushes to GitHub]

[On new computer]
User: "I'm continuing from my old computer. Read docs/Claude Sessions/SESSION_SUMMARY_3.md"
Claude: [Reads summary] "Got it! I can see we were working on the graph commit feature.
The last session had an issue with deep research topic prompts not showing. Ready to continue?"
```

### Scenario 3: Documenting a Complex Journey

```
User: "We just finished a major refactor across 10 context windows.
Generate a summary so future me understands what we built and why."

Claude: [Generates comprehensive summary capturing entire journey]

User: "Perfect. I'm going to commit this to git."
[Commits with message: "Major refactor: Episode-based architecture. See docs/Claude Sessions/SESSION_SUMMARY_4.md for full context."]
```

## Integration with Other Docs

### Relationship to README.md
- **README**: High-level overview, quick start, common tasks
- **Session Summaries**: Detailed journey, decisions, and context

### Relationship to ARCHITECTURE_OVERVIEW.md
- **Architecture Overview**: Current state of system architecture
- **Session Summaries**: How we got here, evolution over time

### Relationship to ADRs (Architecture Decision Records)
- **ADRs**: Formal documentation of architectural decisions with rationale
- **Session Summaries**: Conversational context of why decisions were made

### Workflow

```
Session Summary (captures journey)
       ↓
   Updates to:
   - README.md (quick start changes)
   - ARCHITECTURE_OVERVIEW.md (architecture changes)
   - ADRs (new decisions documented)
       ↓
Next session reads updated docs + latest summary
```

## Files in This Folder

- `README.md` - This file (explains the system)
- `SESSION_SUMMARY_1.md` - Migration from old computer, retroactive commit debugging
- `SESSION_SUMMARY_2.md` - Episode naming refactor, chunking optimization, metadata grouping

## Git Workflow

Session summaries **SHOULD be committed to git** because:
1. They document the development journey
2. They help future contributors understand decisions
3. They enable computer migration
4. They serve as historical record

```bash
git add "docs/Claude Sessions/"
git commit -m "Add session summary for [feature/bugfix]"
git push
```

## Future Enhancements

Potential improvements to this system:
- [ ] Automated summary generation on git commit hooks
- [ ] Summary indexing for quick search across sessions
- [ ] Summary compression (focus on decisions, prune noise)
- [ ] Integration with project management tools

## Contact

If you have questions about this system:
- Read this README first
- Check latest SESSION_SUMMARY_*.md for recent context
- Consult README.md and ARCHITECTURE_OVERVIEW.md for current state

Project: https://github.com/milehighfry405/helldiver
