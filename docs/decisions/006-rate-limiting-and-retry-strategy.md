# ADR 006: Rate Limiting and Retry Strategy for Graphiti LLM Calls

**Status**: Accepted
**Date**: 2025-10-26
**Last Updated**: 2025-10-26

## Context

During implementation of the ontology system (ADR-004), we encountered persistent rate limit errors from OpenAI when committing research episodes to Graphiti. Initial attempts to solve this by adjusting `max_coroutines` parameter in the Graphiti constructor failed - the system continued hitting rate limits even with `max_coroutines=1`.

The problem manifested as:
- Consistent 429 errors: "Rate limit exceeded. Please try again later."
- Errors occurred even with sequential processing (max_coroutines=1)
- Large research episodes (~15-25KB each) would fail during entity extraction
- Cost: 3+ hours debugging with wrong parameter

Investigation revealed that `max_coroutines` controls Neo4j/Graphiti's internal async operations, but does NOT control the rate of LLM API calls for entity extraction. Graphiti uses an internal semaphore controlled by the `SEMAPHORE_LIMIT` environment variable (default: 10 concurrent operations).

## Decision

**Primary Solution: Use SEMAPHORE_LIMIT environment variable**
- Set `SEMAPHORE_LIMIT=1` in `.env` file
- This controls Graphiti's internal LLM call concurrency (the actual source of rate limits)
- Default value of 10 causes rapid bursts of API calls that exceed OpenAI's 200K TPM limit

**Secondary Solution: Implement automatic retry with exponential backoff**
- Wrap all `graphiti.add_episode()` calls in `retry_with_backoff()` function
- On rate limit error (429 or "rate limit" in message):
  - Wait 60 seconds, retry
  - If fails again, wait 120 seconds, retry
  - If fails again, wait 240 seconds, retry
  - After 3 retries, raise exception
- Non-rate-limit errors fail immediately (no retry)

**Implementation location**: `graph/client.py`

## Alternatives Considered

### 1. Use max_coroutines Parameter
- **Description**: Adjust `max_coroutines` in `Graphiti()` constructor
- **Pros**:
  - Simple, single parameter
  - Documented in Graphiti API
- **Cons**:
  - Controls wrong thing (async operations, not LLM calls)
  - Does NOT prevent rate limits
  - Misleading parameter name suggests it controls concurrency
- **Why not chosen**: Doesn't solve the problem - tested extensively with values 1-10, all failed

### 2. Add Manual Delays Between Episodes
- **Description**: `await asyncio.sleep(30)` between each episode commit
- **Pros**:
  - Simple to implement
  - Guaranteed to respect rate limits
- **Cons**:
  - Slow (adds 2+ minutes to each research commit)
  - Wastes time even when not hitting limits
  - Brittle (hardcoded delay may not be enough for large episodes)
- **Why not chosen**: SEMAPHORE_LIMIT solves root cause; manual delays are workaround

### 3. Switch to Anthropic Claude for Entity Extraction
- **Description**: Use `graphiti-core[anthropic]` to use Claude instead of OpenAI
- **Pros**:
  - Different rate limit pool
  - Higher quality entity extraction (potentially)
- **Cons**:
  - Anthropic Tier 1 has STRICTER limits (30K TPM vs OpenAI's 200K TPM)
  - Concurrent connection limits even more restrictive
  - Hit same rate limit issues in testing
- **Why not chosen**: OpenAI has better rate limits for this use case

## Consequences

**Positive:**
- Eliminates rate limit errors completely (validated in production)
- Processing is slower (sequential) but reliable
- Automatic retry handles transient rate limits gracefully
- Solution scales - can increase SEMAPHORE_LIMIT as API tier increases

**Negative (tradeoffs):**
- Slower processing: ~3-5 minutes for 5 episodes vs ~1-2 minutes with higher concurrency
- Must remember to set SEMAPHORE_LIMIT in .env (not obvious from Graphiti docs)
- Retry logic adds complexity to error handling

**Neutral (implications):**
- OpenAI remains the LLM provider for entity extraction
- Rate limits reset per minute, so batch processing works well
- Future: Can tune SEMAPHORE_LIMIT=2 or 3 if API tier increases

## References

- Commit: [this commit]
- Session: SESSION_SUMMARY_8 (graphiti extraction investigation)
- Code: `graph/client.py` - `retry_with_backoff()` function
- Graphiti docs: https://github.com/getzep/graphiti (SEMAPHORE_LIMIT environment variable)
- Related: ADR-004 (ontology system that triggered this discovery)

## Change Log

- 2025-10-26: Initial decision after discovering SEMAPHORE_LIMIT controls rate limiting
