# ADR-001: Episode Naming Strategy

**Status:** Accepted
**Date:** 2025-10-13
**Context:** Session continuation from previous development

## Context

Previously, episode names were auto-generated with timestamps and verbose metadata (e.g., `session_research_20251012_170404`, `deep_research_1_Based_on_the_conversation_they_want_deep_research`). This produced:

1. **Poor folder organization** - Timestamps made folders unsearchable and non-human-readable
2. **Verbose metadata pollution** - LLM extraction metadata leaked into episode names
3. **Bad knowledge graph titles** - Episode names are used as graph node titles for querying
4. **No user control** - Users couldn't verify or correct auto-generated names

The research session involved on another computer and migrated via GitHub had these issues manifest in the folder structure, making it clear we needed a systematic fix.

## Decision

### 1. LLM-Generated Episode Names with User Approval

**Before folder creation**, use LLM to generate clean episode names:

```python
def generate_episode_name(query: str) -> str:
    # LLM proposes name based on query
    suggested_name = llm_generate(query)

    # Show to user for approval
    print(f"I suggest naming this episode: '{suggested_name}'")
    user_input = input("Press Enter to approve, or type different name: ")

    return user_input if user_input else suggested_name
```

### 2. Naming Pattern

**Session folder name** = Initial episode name
**Research folder names** = Episode names (no prefixes)

```
context/
└── Arthur_AI_product_and_market_analysis/  ← Session = initial episode name
    ├── Arthur_AI_product_and_market_analysis/  ← Initial research folder
    ├── Downmarket_ICP_signals_for_Arthur_AI/   ← Deep research folder
    └── session.json
```

### 3. Characteristics of Good Episode Names

- **Concise**: 3-8 words
- **Descriptive**: Captures what was researched
- **Keyword-focused**: Easy to search/find later
- **Professional**: No verbose extraction metadata
- **Examples**:
  - ✅ "Arthur AI product and market analysis"
  - ✅ "Downmarket ICP signals for Arthur AI"
  - ❌ "Based on the conversation, they want deep research on..."

### 4. Timing of Name Generation

- **Initial research**: After tasking, before research starts
- **Deep research**: After topic extraction, before workers spawn
- **User always approves**: Can accept suggestion or provide alternative

## Consequences

### Positive

1. **Clean folder structure** - Human-readable, searchable folder names
2. **Better graph queries** - Episode titles in Graphiti are meaningful
3. **User control** - Users validate names before committing to structure
4. **Consistent naming** - LLM ensures professional naming across all sessions
5. **Easy migration** - Old sessions with bad names are one-time issue

### Negative

1. **Extra LLM call** - Adds one API call per research session (negligible cost)
2. **User interaction required** - Adds approval step (prevents bad names, worth it)
3. **Slightly slower start** - ~2 seconds for name generation + user approval

### Neutral

1. **Backward compatibility needed** - Code must handle both old and new folder structures
2. **Migration for existing sessions** - One-time manual rename required

## Implementation Notes

### Code Changes

1. **ResearchSession.__init__()** - No longer creates folders (pure state object)
2. **ResearchSession.initialize_filesystem(episode_name)** - New method to create folders AFTER name approval
3. **generate_episode_name(query)** - LLM generation + user approval flow
4. **load_existing_session()** - Detects both old and new folder structures

### Migration Path

For old sessions (like `Arthur_AI_product_and_market_analysis`):
1. Manually rename folders to clean names
2. Update `session.json` with `episode_name` field
3. System detects structure automatically going forward

## Related

- ADR-002: Graphiti Chunking Strategy (episode size optimization)
- ADR-003: Episode Grouping Metadata (how episodes link in graph)
