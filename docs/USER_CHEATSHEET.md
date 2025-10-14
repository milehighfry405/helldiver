# User Cheat Sheet

**Quick reference for how to use this project with Claude Code**

---

## Starting a New Session

**What you say**:
```
"Read the README"
```

**What happens**:
1. Claude reads README.md
2. Claude reads docs/AI_ONBOARDING.md
3. Claude reads latest docs/Claude Sessions/SESSION_SUMMARY_*.md
4. Claude reads docs/COMMIT_CHECKLIST.md
5. Claude says: "Context loaded. Ready to continue!"

**That's it. One command, full context.**

---

## During Work

Just work normally. Claude knows the codebase and patterns.

---

## When Ready to Commit

**What you say**:
```
"commit"
```
or
```
"ready to commit"
```

**What happens**:
1. Claude re-reads docs/COMMIT_CHECKLIST.md (even if context is full)
2. Claude checks if docs need updates:
   - ADR needed? (architectural decision)
   - README update? (usage changed)
   - Architecture overview update? (design changed)
3. Claude updates docs automatically
4. Claude generates commit message with context
5. Claude shows you:
   ```
   Documentation updates made:
   - Created/Updated X
   - Updated Y

   Commit message:
   [proposed message]

   Ready to commit?
   ```
6. You say "yes" or request changes

**You don't need to remember what docs to update. Claude handles it automatically.**

---

## Session Summaries

**When it happens**: Claude Code hits context limit (~200k tokens)

**What Claude does**: Automatically generates massive summary file

**What you do**:
1. Copy the summary Claude generated
2. Paste into new file: `docs/Claude Sessions/SESSION_SUMMARY_X.md` (increment number)
3. That's it!

**Why**: Next session, Claude reads this and has full context of all previous work.

---

## Common Commands

| You Say | Claude Does |
|---------|-------------|
| "Read the README" | Loads all context (README, onboarding, session summary, checklist) |
| "commit" | Checks docs, updates as needed, proposes commit |
| "Add feature X" | Implements following existing patterns |
| "Debug issue Y" | Checks session history, debugs, fixes |
| "Refactor Z" | Refactors, updates docs if architectural |

---

## What You Maintain

### Manual (you do this):
- ✅ Session summaries (copy/paste when Claude hits context limit)

### Automatic (Claude does this):
- ✅ Code changes
- ✅ Documentation updates (README, Architecture Overview)
- ✅ ADRs (Architecture Decision Records)
- ✅ Commit messages with context
- ✅ Code comments

**Total manual effort: Copy/paste session summaries when needed. Everything else automated.**

---

## File Structure (Quick Reference)

```
helldiver/
├── README.md                      # Start here (say "read the README")
├── main.py                        # Core code
├── docs/
│   ├── AI_ONBOARDING.md          # Navigation for Claude
│   ├── COMMIT_CHECKLIST.md       # Pre-commit checklist (Claude reads before commits)
│   ├── ARCHITECTURE_OVERVIEW.md  # System architecture
│   ├── USER_CHEATSHEET.md        # This file
│   ├── Claude Sessions/          # Session summaries (you maintain)
│   │   ├── README.md
│   │   ├── SESSION_SUMMARY_1.md
│   │   └── SESSION_SUMMARY_2.md
│   └── decisions/                # ADRs (Claude maintains)
│       ├── 001-episode-naming-strategy.md
│       ├── 002-graphiti-chunking-strategy.md
│       └── 003-episode-grouping-metadata.md
```

---

## Troubleshooting

### "Claude forgot to update docs when committing"
**Fix**: Say "re-read docs/COMMIT_CHECKLIST.md and update docs"

### "Claude doesn't have context from previous session"
**Fix**: Say "read the README" (it will load latest session summary)

### "I forgot to save session summary before context limit"
**Fix**: Ask Claude to generate one: "Generate a session summary like you do when running out of context"

### "I don't remember what was done in previous session"
**Fix**: Read `docs/Claude Sessions/SESSION_SUMMARY_X.md` yourself (human-readable)

---

## Key Principles

1. **Single entry point**: "Read the README" = full context loaded
2. **Commit-triggered docs**: Say "commit" = docs auto-updated
3. **Session continuity**: Session summaries = no context loss
4. **Zero mental overhead**: You focus on work, Claude handles docs

---

## Example Session Flow

```
[New Claude Code session]

You: "Read the README"

Claude: "Context loaded. I've read the README, AI_ONBOARDING,
         SESSION_SUMMARY_2, and COMMIT_CHECKLIST. Ready to continue!"

You: "Let's add custom entity types for Graphiti"

Claude: [implements feature]

You: "commit"

Claude: [Re-reads COMMIT_CHECKLIST.md]
        [Checks: Architectural decision? YES]
        [Creates docs/decisions/004-custom-entity-types.md]
        [Updates docs/ARCHITECTURE_OVERVIEW.md]

        "Documentation updates made:
         - Created docs/decisions/004-custom-entity-types.md
         - Updated docs/ARCHITECTURE_OVERVIEW.md

         Commit message:
         feat: Add custom entity types for Graphiti
         ...

         Ready to commit?"

You: "yes"

Claude: [Commits everything]

[Later...]

Claude: "Approaching context limit. Generating session summary..."
        [Generates summary]

You: [Copy/paste into docs/Claude Sessions/SESSION_SUMMARY_3.md]

[Next session, new computer]

You: "Read the README"

Claude: [Loads all context including SESSION_SUMMARY_3]
        "Context loaded. Ready to continue!"
```

**Seamless, zero friction.**

---

## That's It!

Remember:
- **Start session**: "Read the README"
- **Commit**: "commit" (Claude auto-handles docs)
- **Save summaries**: Copy/paste when Claude hits context limit

Everything else is automated.
