# Documentation Map

**Purpose**: Quick reference showing what each documentation file contains and when to read it.

## Documentation Structure

```
docs/
├── DOCUMENTATION_MAP.md              # This file - documentation navigation
├── AI_ONBOARDING.md                  # PRIMARY ENTRY POINT for AI assistants
├── ARCHITECTURE_OVERVIEW.md          # System architecture and design patterns
├── Claude Sessions/                  # Session continuation system
│   ├── README.md                    # How session continuation works
│   ├── SESSION_SUMMARY_1.md         # First session (migration, debugging)
│   └── SESSION_SUMMARY_2.md         # Second session (refactor, optimization)
└── decisions/                        # Architecture Decision Records (ADRs)
    ├── 001-episode-naming-strategy.md
    ├── 002-graphiti-chunking-strategy.md
    └── 003-episode-grouping-metadata.md
```

## Quick Reference Guide

### For AI Assistants

| Situation | Read This First | Then Read |
|-----------|----------------|-----------|
| **New to project** | [AI_ONBOARDING.md](AI_ONBOARDING.md) | [README.md](../README.md), [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) |
| **Continuing session** | [Claude Sessions/README.md](Claude%20Sessions/README.md) | Latest `SESSION_SUMMARY_*.md` |
| **Making architectural changes** | Relevant ADR in [decisions/](decisions/) | [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) |
| **Debugging** | [Claude Sessions/](Claude%20Sessions/) (check if seen before) | Code files with issue |
| **Adding features** | [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) | Relevant ADR |

### For Humans

| Goal | Start Here |
|------|-----------|
| **Install and run** | [README.md](../README.md) |
| **Understand architecture** | [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) |
| **Understand decisions** | [decisions/](decisions/) (ADRs) |
| **Continue development** | [Claude Sessions/](Claude%20Sessions/) (latest summary) |

## File Descriptions

### Core Documentation

#### [AI_ONBOARDING.md](AI_ONBOARDING.md)
- **Audience**: AI assistants (Claude Code, ChatGPT, etc.)
- **Purpose**: Navigation guide explaining what to read when
- **When to read**: First file to read when starting new session
- **Key sections**: Scenario-based navigation, quick reference, best practices

#### [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)
- **Audience**: Developers and AI assistants
- **Purpose**: High-level system architecture and design patterns
- **When to read**: When you need to understand how the system works
- **Key sections**: Episode model, state machine, design patterns, key files

#### [DOCUMENTATION_MAP.md](DOCUMENTATION_MAP.md)
- **Audience**: Anyone confused about documentation
- **Purpose**: Meta-documentation explaining the documentation system
- **When to read**: When you're not sure which doc to read
- **Key sections**: This file you're reading now

### Session Continuation

#### [Claude Sessions/README.md](Claude%20Sessions/README.md)
- **Audience**: AI assistants and developers
- **Purpose**: Explains session continuation system
- **When to read**: Before reading session summaries
- **Key sections**: How it works, file naming, usage examples

#### [Claude Sessions/SESSION_SUMMARY_*.md](Claude%20Sessions/)
- **Audience**: AI assistants continuing work
- **Purpose**: Complete context from previous sessions
- **When to read**: When continuing from previous session or new computer
- **Key sections**: All decisions, all code changes, all bugs/fixes, current state

### Architecture Decision Records

#### [decisions/001-episode-naming-strategy.md](decisions/001-episode-naming-strategy.md)
- **Decision**: Use LLM-generated episode names with user approval
- **Context**: Old timestamps and verbose metadata in folder names
- **Impact**: Better folder organization, clean graph titles
- **When to read**: Before changing episode naming system

#### [decisions/002-graphiti-chunking-strategy.md](decisions/002-graphiti-chunking-strategy.md)
- **Decision**: One episode per worker (1,400-2,600 tokens each)
- **Context**: Graphiti research shows optimal chunking for entity extraction
- **Impact**: Richer graph entities, more detailed extraction
- **When to read**: Before changing graph commit strategy

#### [decisions/003-episode-grouping-metadata.md](decisions/003-episode-grouping-metadata.md)
- **Decision**: Hierarchical metadata (name patterns, group_id, source_description)
- **Context**: Need to link episodes from same session in graph
- **Impact**: Queryable graph structure, cross-episode insights
- **When to read**: Before changing episode metadata or graph queries

## Documentation Philosophy

### Principles

1. **AI-First Design**: Documentation optimized for AI consumption with clear navigation
2. **No Duplication**: Each concept documented once, referenced elsewhere
3. **Context-Rich**: File/line references, code examples, before/after comparisons
4. **Living Documents**: Updated as code changes, not one-time artifacts
5. **Rationale Over Description**: Explain WHY decisions were made, not just WHAT

### File Organization Rules

- **README.md**: Project overview, installation, usage (in repo root)
- **AI_ONBOARDING.md**: Navigation guide (entry point for AI)
- **ARCHITECTURE_OVERVIEW.md**: System architecture and patterns
- **decisions/**: ADRs for architectural decisions (numbered sequentially)
- **Claude Sessions/**: Session continuation files (numbered sequentially)

### Cross-Referencing

All documentation uses relative paths with markdown links:

```markdown
[File Name](../path/to/file.md)           # For files
[File:Line](../path/to/file.py#L42)      # For code references
[File:Range](../path/to/file.py#L42-L51) # For code ranges
```

This makes references clickable in IDEs and GitHub.

## Update Guidelines

### When to Update Each File

| File | Update When... |
|------|---------------|
| **README.md** | Installation/usage changes, new features |
| **AI_ONBOARDING.md** | Documentation structure changes |
| **ARCHITECTURE_OVERVIEW.md** | Architecture or design pattern changes |
| **DOCUMENTATION_MAP.md** | New docs added, organization changes |
| **ADRs** | Architectural decisions made or revised |
| **Session Summaries** | Context limit reached or manually requested |

### Who Updates

- **AI Assistants**: Update docs as part of implementing changes
- **Users**: Review and approve updates
- **Both**: Collaborate on ADRs for major decisions

### Quality Standards

All documentation must:
- ✅ Use clear, concise language
- ✅ Include code examples where relevant
- ✅ Reference other docs without duplicating
- ✅ Use clickable file/line references
- ✅ Explain rationale, not just facts

## Common Questions

### "Which file do I start with?"

**AI**: [AI_ONBOARDING.md](AI_ONBOARDING.md)
**Human**: [README.md](../README.md)

### "Where's the code documentation?"

Inline in code files with docstrings. Documentation files explain architecture and decisions, not individual functions.

### "How do I know if a session summary is relevant?"

Check the filename - higher numbers = more recent. Always read the latest.

### "Should I update docs when I make code changes?"

**Yes**, if the change affects:
- Architecture or design patterns → Update ARCHITECTURE_OVERVIEW.md
- Usage or installation → Update README.md
- Architectural decisions → Create/update ADR
- Session continuation → Generate new session summary

**No**, if the change is:
- Bug fix with no architectural impact
- Small refactor following existing patterns
- Adding comments or improving code clarity

### "What if I'm not sure where something should go?"

Ask the user. When in doubt, less documentation is better than duplicated/conflicting documentation.

## Meta: Evolution of This System

### Why This Exists

**Problem**: AI assistants waste time finding information, ask redundant questions, miss prior context.

**Solution**: Comprehensive documentation system with clear navigation, session continuity, and architectural decision records.

**Result**: AI can get full context in minutes and continue work seamlessly across sessions and computers.

### Previous Issues Solved

1. ❌ **Old**: AI asked "What does this project do?" every session
   - ✅ **New**: AI reads AI_ONBOARDING.md → README.md → understands immediately

2. ❌ **Old**: AI repeated mistakes from previous sessions
   - ✅ **New**: AI reads Claude Sessions/ summaries → avoids known issues

3. ❌ **Old**: AI changed code without understanding rationale
   - ✅ **New**: AI reads ADRs → understands WHY decisions were made

4. ❌ **Old**: Docs outdated, conflicting, hard to navigate
   - ✅ **New**: Single source of truth, clear cross-references, living documents

### Future Improvements

Potential enhancements:
- [ ] Automated doc generation on git commits
- [ ] Doc linting (check for broken links, outdated references)
- [ ] Interactive doc navigation (CLI tool)
- [ ] Doc versioning aligned with git tags

## Need Help?

If you're still confused about documentation:
1. Read [AI_ONBOARDING.md](AI_ONBOARDING.md) again more carefully
2. Check if your question is answered in [README.md](../README.md)
3. Ask the user for clarification

---

**Remember**: Good documentation saves hours of confusion. Update docs as you code, not as an afterthought.
