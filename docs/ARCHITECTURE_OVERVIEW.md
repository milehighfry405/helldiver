# Helldiver Research Agent - Architecture Overview

## What This Project Does

The Helldiver Research Agent is a multi-agent research system designed for deep, context-engineered knowledge discovery with human-in-the-loop refinement. The system conducts comprehensive research using specialized AI workers (Academic Researcher, Industry Intelligence, Tool Analyzer, and Critical Analyst) that operate in parallel via Anthropic's Batch API, then synthesizes findings into dense narrative summaries. The key innovation is the interactive refinement phase, where users engage in conversational "wave function collapse"—asking clarifying questions, reframing priorities, and providing mental models that get weighted higher than the original research when committing to a knowledge graph. This implements Anthropic's context engineering principles: the agent doesn't just gather facts, it learns how the user wants to interpret those facts, creating a personalized lens for understanding the research. All findings persist to a Graphiti knowledge graph for long-term episodic memory across research sessions.

## System Architecture

The architecture follows a session-based, hierarchical research model. Each research mission creates an isolated session directory (`context/session_{name}_{timestamp}/`) containing: (1) an `initial_research/` subdirectory with findings from the 4 specialist workers, (2) a `refinement_context.txt` file capturing the user's mental models and synthesis instructions (weighted higher than original research), and (3) optional `deep_research_{topic}/` subdirectories spawned during refinement when users request deeper investigation into specific areas. The refinement mode acts as a mini-orchestrator within each session—users can trigger lightweight research (single web searches) or deep research (full 4-worker agent swarm) on follow-up questions, with all accumulated context eventually collapsing into a single knowledge graph episode. The system uses prompt caching extensively (90% cost savings on repeated context reads), Batch API for parallel worker execution (50% cheaper, avoids rate limits), and maintains conversation state through file-based persistence for crash recovery. State files (`session.json`, `refinement_context.json`, `batch_state.json`) enable resumption of interrupted research and provide audit trails.

## Technical Implementation and Design Patterns

Built on Anthropic's Claude API with Sonnet 4.5 for workers and Opus 4 for synthesis, the system implements several production-grade patterns: (1) **Context Engineering** - follows Anthropic's just-in-time context loading with lightweight file identifiers, caching large research contexts while keeping dynamic queries fresh; (2) **Batch API Integration** - submits 3 workers as batch jobs with custom_ids for tracking, polls for completion, then extracts results—avoiding real-time API rate limits while cutting costs in half; (3) **Weighted Context Synthesis** - when committing to the knowledge graph, refinement context (user mental models/framing) is explicitly marked as higher priority than original research findings, implementing true context engineering where users teach the AI how to think about facts rather than just accumulating facts; (4) **Session Isolation** - each research mission lives in its own directory tree, preventing context pollution across different research topics and enabling parallel exploration of multiple subjects; (5) **Wave Function Collapse Pattern** - users can go off on tangents, ask unrelated questions, or explore rabbit holes during refinement, with the agent maintaining the original research question in state until conversations naturally converge back to synthesis and graph commit. The codebase uses argparse for CLI flags (`--refine`, `--test-graphiti`, `--skip-research`), asyncio for Graphiti's async operations, and prompt caching with explicit `cache_control` blocks to optimize repeated context reads during multi-turn refinement conversations.

## Questions for SWE Best Practices Review

1. **Project Structure**: Is the current flat file structure appropriate, or should we reorganize into packages (e.g., `helldiver/agents/`, `helldiver/context/`, `helldiver/graphiti/`) with proper `__init__.py` files?

2. **State Management**: We're using global `CURRENT_SESSION_DIR` and file-based state. Should we implement a proper Session class with context managers or a state machine pattern?

3. **Error Handling**: Currently using basic try/except blocks. Should we implement custom exception types, retry logic with exponential backoff, or structured logging?

4. **Configuration**: Using hardcoded values and environment variables. Should we implement a proper config management system (e.g., `pydantic` settings, YAML configs)?

5. **Testing**: No tests currently exist. What testing strategy makes sense for a system with external API dependencies (Anthropic, Graphiti, Neo4j)? Unit tests with mocks, integration tests, or E2E tests?

6. **Type Hints**: Some functions have type hints, some don't. Should we add comprehensive typing and run `mypy` for type checking?

7. **Concurrency**: Currently using Batch API for parallelism. Is the async/await usage correct for Graphiti operations? Should we use asyncio more extensively?

8. **Observability**: Basic print statements for logging. Should we implement structured logging (e.g., `structlog`), metrics, or tracing?

9. **API Client Management**: Creating Anthropic client at module level. Should we use dependency injection, client pools, or request session management?

10. **Session Architecture**: The current session-based file structure allows hierarchical research (parent research → refinement → deep research). Is this directory-based approach scalable, or should we use a database for session management?
