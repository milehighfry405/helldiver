"""
Helldiver Research Agent - Using Anthropic Batch API
Multi-agent research system that dispatches workers via batch processing.

Key benefits:
- 50% cheaper than real-time API
- No rate limit issues (batches process in background)
- True async multi-agent pattern

Usage:
  python helldiver_agent.py                    # Normal research mode
  python helldiver_agent.py --test-graphiti    # Test Graphiti/MCP integration
  python helldiver_agent.py --skip-research    # Skip research, just test graph write
"""

import argparse
import asyncio
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic

from graphiti_client import GraphitiClient

# Load environment
load_dotenv()

# Initialize clients
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
graphiti_client = GraphitiClient()

# Base context directory - each research session gets its own subdirectory
BASE_CONTEXT_DIR = "context"
os.makedirs(BASE_CONTEXT_DIR, exist_ok=True)

# Session management
def create_session_dir(session_name: str = None) -> str:
    """
    Create a unique session directory for this research.

    Session structure:
    context/
    └── session_{name}_{timestamp}/
        ├── initial_research/
        │   ├── academic_researcher.txt
        │   ├── industry_intelligence.txt
        │   ├── tool_analyzer.txt
        │   └── critical_analysis.txt
        ├── refinement_context.txt
        └── deep_research_{topic}/
            └── (same structure as initial_research)
    """
    if not session_name:
        session_name = "research"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(BASE_CONTEXT_DIR, f"session_{session_name}_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)

    # Create initial research subdirectory
    initial_dir = os.path.join(session_dir, "initial_research")
    os.makedirs(initial_dir, exist_ok=True)

    return session_dir


def get_latest_session() -> str:
    """Get the most recent session directory"""
    sessions = [d for d in os.listdir(BASE_CONTEXT_DIR) if d.startswith("session_")]
    if not sessions:
        return None
    sessions.sort(reverse=True)
    return os.path.join(BASE_CONTEXT_DIR, sessions[0])


# Global session context (set at runtime)
CURRENT_SESSION_DIR = None


def write_status(status: str, message: str = ""):
    """Write current status to file"""
    with open(STATUS_FILE, 'w') as f:
        json.dump({
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    print(f"[STATUS] {status}: {message}")


def write_findings(findings: str, query: str):
    """Write findings to file"""
    with open(FINDINGS_FILE, 'w', encoding='utf-8') as f:
        f.write(f"Research Query: {query}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write("="*80 + "\n\n")
        f.write(findings)
    print(f"[FINDINGS] Written to {FINDINGS_FILE}")


def create_worker_batch(research_query: str, tasking_context: str):
    """
    Create batch jobs for 3 specialist workers.

    Returns:
        Batch object with 3 research requests
    """
    write_status("creating_batch", "Creating batch jobs for 3 specialist workers...")

    # Define specialist system prompts
    academic_prompt = """You are an academic researcher specializing in deep technical literature.

Your task is to search for papers, technical documentation, and theoretical frameworks related to the user's query.

Extract key approaches, methodologies, and academic consensus. Focus on:
- Research papers and academic publications
- Technical documentation and specifications
- Theoretical frameworks and models
- Scientific consensus and debates

Use the web_search tool extensively. Return findings as structured information with:
- Key sources (with citations/URLs)
- Main concepts and approaches
- Methodologies discovered
- Relevant technical details

Keep findings dense and signal-rich. Every sentence should carry useful information."""

    industry_prompt = """You are an industry analyst who tracks how companies implement technologies.

Your task is to find real case studies, implementations, and production use cases.

Focus on:
- Real company case studies
- Engineering blog posts from tech teams
- Conference talks and presentations
- Production implementations and lessons learned
- What actually worked in practice

Use the web_search tool extensively. Return findings as structured information with:
- Company names and specific implementations
- Scale/metrics when available
- Technical approaches used
- Lessons learned and gotchas

Prioritize proven, real-world usage over theoretical discussions."""

    tool_prompt = """You are a tools researcher who understands frameworks and implementations.

Your task is to search GitHub repositories, framework documentation, and tool comparisons.

Focus on:
- Open source projects and repositories
- Framework documentation and guides
- Tool comparisons and trade-offs
- Implementation patterns
- Technical architecture

Use the web_search tool extensively. Return findings as structured information with:
- Tool/framework names with GitHub links
- Key features and capabilities
- Technical trade-offs
- Usage patterns and examples
- Community adoption/maturity

Understand what makes tools different and which trade-offs matter."""

    user_message_template = f"""Research Query: {research_query}

Tasking Context: {tasking_context}

Please conduct deep research on this topic using your specialized expertise.
Use web search extensively to gather current, comprehensive information.
Return structured findings with sources and key insights."""

    # Create batch with 3 worker requests
    batch = anthropic_client.messages.batches.create(
        requests=[
            {
                "custom_id": "academic_researcher",
                "params": {
                    "model": "claude-sonnet-4-5",
                    "max_tokens": 4000,
                    "temperature": 0.3,
                    "system": academic_prompt,
                    "tools": [{
                        "type": "web_search_20250305",
                        "name": "web_search"
                    }],
                    "messages": [{"role": "user", "content": user_message_template}]
                }
            },
            {
                "custom_id": "industry_intelligence",
                "params": {
                    "model": "claude-sonnet-4-5",
                    "max_tokens": 4000,
                    "temperature": 0.3,
                    "system": industry_prompt,
                    "tools": [{
                        "type": "web_search_20250305",
                        "name": "web_search"
                    }],
                    "messages": [{"role": "user", "content": user_message_template}]
                }
            },
            {
                "custom_id": "tool_analyzer",
                "params": {
                    "model": "claude-sonnet-4-5",
                    "max_tokens": 4000,
                    "temperature": 0.3,
                    "system": tool_prompt,
                    "tools": [{
                        "type": "web_search_20250305",
                        "name": "web_search"
                    }],
                    "messages": [{"role": "user", "content": user_message_template}]
                }
            }
        ]
    )

    # Save batch ID to state
    with open(BATCH_STATE_FILE, 'w') as f:
        json.dump({
            "batch_id": batch.id,
            "created_at": datetime.now().isoformat(),
            "query": research_query,
            "status": "submitted"
        }, f, indent=2)

    print(f"[BATCH] Created batch {batch.id}")
    print(f"[BATCH] Processing status: {batch.processing_status}")
    print(f"[BATCH] This will process in the background (usually < 5 minutes)")

    return batch


def poll_batch_completion(batch_id: str, poll_interval: int = 10):
    """
    Poll batch until it completes.

    Args:
        batch_id: Batch ID to poll
        poll_interval: Seconds between polls

    Returns:
        Completed batch object
    """
    print(f"\n[BATCH] Polling batch {batch_id} every {poll_interval}s...")
    write_status("polling", f"Waiting for batch {batch_id} to complete...")

    while True:
        batch = anthropic_client.messages.batches.retrieve(batch_id)

        # Update state file
        with open(BATCH_STATE_FILE, 'r') as f:
            state = json.load(f)
        state["status"] = batch.processing_status
        state["last_checked"] = datetime.now().isoformat()
        with open(BATCH_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)

        if batch.processing_status == "ended":
            print(f"[BATCH] Complete! Processed {batch.request_counts.succeeded} requests")
            write_status("batch_complete", f"Batch {batch_id} processing complete")
            return batch

        if batch.processing_status == "canceling" or batch.processing_status == "canceled":
            raise Exception(f"Batch was canceled: {batch}")

        print(f"[BATCH] Status: {batch.processing_status}, Requests: {batch.request_counts}")
        time.sleep(poll_interval)


def extract_batch_results(batch_id: str, research_dir: str = None) -> dict:
    """
    Extract results from completed batch and save as context files.

    Uses Anthropic's context engineering pattern: save research as
    lightweight files for just-in-time loading during refinement.

    Returns:
        Dictionary with worker findings
    """
    print(f"\n[BATCH] Extracting results from batch {batch_id}...")
    write_status("extracting", "Extracting worker findings from batch...")

    results = {}

    # Iterate through results
    for result in anthropic_client.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            custom_id = result.custom_id
            message = result.result.message

            # Extract text content
            findings = ""
            for block in message.content:
                if block.type == "text":
                    findings += block.text

            results[custom_id] = findings
            print(f"[WORKER] {custom_id}: {len(findings)} characters")

            # Save to session's research directory
            if research_dir is None:
                research_dir = os.path.join(CURRENT_SESSION_DIR, "initial_research")

            context_file = os.path.join(research_dir, f"{custom_id}.txt")
            with open(context_file, 'w', encoding='utf-8') as f:
                f.write(f"Worker: {custom_id}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Batch ID: {batch_id}\n")
                f.write("="*80 + "\n\n")
                f.write(findings)
            print(f"[CONTEXT] Saved to {context_file}")

        else:
            print(f"[WORKER] {result.custom_id} failed: {result.result}")
            results[result.custom_id] = f"Error: {result.result}"

    return results


def run_critical_analyst(worker_results: dict, research_query: str, tasking_context: str, research_dir: str = None) -> str:
    """
    Run critical analyst to review worker findings (synchronous, no web search).
    """
    print(f"\n[WORKER] Launching Critical Analyst...")
    write_status("critical_analysis", "Critical Analyst reviewing worker findings...")

    critical_prompt = """You are a skeptical senior researcher who reviews findings from other workers.

Your task is to:
1. Score each finding's relevance to the original query (1-10 scale)
2. Filter out tangentially related or low-quality information
3. Identify gaps in the research
4. Highlight the most valuable insights

Be ruthless about cutting noise. The user's time is valuable.

Return:
- Relevance scores (1-10) with brief justifications
- Filtered findings (keep only high-signal information)
- Gaps or missing areas that should have been covered
- Overall assessment of research quality"""

    critical_message = f"""Original Research Query: {research_query}

Tasking Context: {tasking_context}

ACADEMIC RESEARCHER FINDINGS:
{worker_results.get('academic_researcher', 'No findings')}

INDUSTRY INTELLIGENCE FINDINGS:
{worker_results.get('industry_intelligence', 'No findings')}

TOOL ANALYZER FINDINGS:
{worker_results.get('tool_analyzer', 'No findings')}

Please review these findings critically. Score relevance, filter noise, and identify gaps."""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        temperature=0.3,
        system=critical_prompt,
        messages=[{"role": "user", "content": critical_message}]
    )

    findings = ""
    for block in response.content:
        if block.type == "text":
            findings += block.text

    # Save to session's research directory
    if research_dir is None:
        research_dir = os.path.join(CURRENT_SESSION_DIR, "initial_research")

    context_file = os.path.join(research_dir, "critical_analysis.txt")
    with open(context_file, 'w', encoding='utf-8') as f:
        f.write(f"Worker: Critical Analyst\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write("="*80 + "\n\n")
        f.write(findings)
    print(f"[WORKER] Critical Analyst complete")
    print(f"[CONTEXT] Saved to {context_file}")

    return findings


def synthesize_narrative(worker_results: dict, critical_analysis: str, research_query: str, tasking_context: str) -> str:
    """
    Synthesize worker findings into dense narrative using Opus 4 with prompt caching.

    Uses prompt caching on worker research for 90% cost savings on repeated reads.
    """
    print(f"\n[SYNTHESIS] Using Opus 4 to synthesize findings...")
    write_status("synthesizing", "Synthesizing findings into narrative with Opus 4...")

    # Build cached context blocks - these will be cached for 5 min (or 1 hour with extended cache)
    cached_research = f"""ACADEMIC RESEARCHER FINDINGS:
{worker_results.get('academic_researcher', 'No findings')}

INDUSTRY INTELLIGENCE FINDINGS:
{worker_results.get('industry_intelligence', 'No findings')}

TOOL ANALYZER FINDINGS:
{worker_results.get('tool_analyzer', 'No findings')}

CRITICAL ANALYST ASSESSMENT:
{critical_analysis}"""

    synthesis_instruction = f"""Original query: {research_query}
Tasking context: {tasking_context}

Synthesize these findings into a dense narrative (20-30 seconds of reading) that:
1. Opens with why this matters to the user's query
2. Shows how findings connect and build on each other
3. Explains causality and relationships
4. Ends with confidence/gaps from Critical Analyst

Write as flowing prose, not bullets. Every sentence should carry signal.
Show the thought process that led from broad search to specific insights."""

    # Use prompt caching: system prompt + cached research + synthesis instruction
    response = anthropic_client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=2000,
        temperature=0.4,
        system=[
            {
                "type": "text",
                "text": "You are a brilliant research synthesizer who creates dense, narrative summaries. Create flowing prose that shows connections and builds understanding.",
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": cached_research,
                        "cache_control": {"type": "ephemeral"}
                    },
                    {
                        "type": "text",
                        "text": synthesis_instruction
                    }
                ]
            }
        ]
    )

    print(f"[CACHE] Usage - Created: {response.usage.cache_creation_input_tokens}, Read: {response.usage.cache_read_input_tokens}")

    narrative = ""
    for block in response.content:
        if block.type == "text":
            narrative += block.text

    return narrative


def interactive_refinement():
    """
    Interactive refinement loop - chat with the research like Claude Desktop.

    Uses cached context for 90% cost savings on repeated questions.
    """
    print("\n" + "="*80)
    print("HELLDIVER RESEARCH AGENT - INTERACTIVE REFINEMENT")
    print("="*80)

    # Load initial research from session directory
    initial_research_dir = os.path.join(CURRENT_SESSION_DIR, "initial_research")

    # Check if context files exist
    context_files = {
        'academic': os.path.join(initial_research_dir, "academic_researcher.txt"),
        'industry': os.path.join(initial_research_dir, "industry_intelligence.txt"),
        'tool': os.path.join(initial_research_dir, "tool_analyzer.txt"),
        'critical': os.path.join(initial_research_dir, "critical_analysis.txt")
    }

    missing = [name for name, path in context_files.items() if not os.path.exists(path)]
    if missing:
        print(f"\n[ERROR] Missing context files: {', '.join(missing)}")
        print("Run research first: python helldiver_agent.py")
        return

    # Load all context (the gold mine!)
    print("\n[CONTEXT] Loading research context...")
    full_context = ""
    for name, path in context_files.items():
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            full_context += f"\n\n{'='*80}\n{name.upper()} RESEARCH:\n{'='*80}\n{content}"
            print(f"  [{name}] {len(content)} characters loaded")

    # Load narrative summary
    narrative = ""
    if os.path.exists(FINDINGS_FILE):
        with open(FINDINGS_FILE, 'r', encoding='utf-8') as f:
            narrative = f.read()
        print(f"\n[NARRATIVE] Loaded summary from {FINDINGS_FILE}")

    # Show the narrative to user
    print("\n" + "="*80)
    print("RESEARCH SUMMARY:")
    print("="*80)
    if narrative:
        # Extract just the narrative content (skip metadata)
        lines = narrative.split('\n')
        narrative_only = '\n'.join([l for l in lines if not l.startswith('Research Query:') and not l.startswith('Timestamp:')])
        print(narrative_only.strip())
    else:
        print("[No narrative found - run research first]")

    print("\n" + "="*80)
    print("INTERACTIVE MODE - Ask me anything about this research!")
    print("="*80)
    print("\nCommands:")
    print("  - Type your question naturally")
    print("  - 'commit' - Write refined findings to knowledge graph")
    print("  - 'exit' or 'quit' - Exit refinement mode")
    print("  - 'show context' - See what context is loaded")
    print()

    # Conversation history for multi-turn chat
    conversation_history = []
    refinement_log = []  # Track what user asked about

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit']:
                print("\n[EXIT] Exiting refinement mode.")
                break

            if user_input.lower() == 'show context':
                print(f"\n[CONTEXT] Loaded {len(full_context)} characters of research:")
                for name in context_files.keys():
                    print(f"  - {name}_researcher")
                continue

            if user_input.lower() == 'commit':
                print("\n[COMMIT] Preparing to write to knowledge graph...")
                # Run async commit
                asyncio.run(commit_to_graph(narrative, full_context, refinement_log))
                break

            # Regular question - use cached context to answer
            print("\n[THINKING] Reading cached context...")

            # Build cached message with prompt caching
            system_prompt = """You are a research assistant in interactive refinement mode - CONTEXT ENGINEERING phase.

CONTEXT: Deep research was conducted. You have detailed findings from 4 specialist workers.

YOUR CRITICAL ROLE:
1. EXTRACT USER'S MENTAL MODEL - When user says things like:
   - "I'm more interested in X than Y"
   - "Think about this as [framing]"
   - "The real story here is..."
   - "Focus on/emphasize..."
   → These are INSTRUCTIONS for how to interpret the research. Surface them clearly.

2. IDENTIFY REFRAMING - When user shifts perspective:
   - "It's not about the tech, it's about GTM"
   - "This is really a pricing strategy play"
   → Make these reframings explicit in your response

3. CAPTURE SYNTHESIS INSTRUCTIONS - When user says:
   - "When you write to graph, emphasize X"
   - "De-emphasize technical details"
   - "The key insight is..."
   → These are WEIGHTED HIGHER than original research

4. SUPPORT WAVE FUNCTION COLLAPSE:
   - User may explore tangents, rabbit holes
   - Answer naturally, trust they'll connect back
   - When they do, help them see connections

5. LIGHT RESEARCH vs DEEP RESEARCH:
   - For simple questions, use research + your knowledge
   - If user says "do deep research on X", note that triggers full agent swarm
   - Flag when deep research might be valuable

Your responses shape how the research will be written to the knowledge graph. User's framing > original research.

Be conversational but ACTIVELY LISTEN for mental models, reframings, and synthesis instructions."""

            user_message_parts = [
                {
                    "type": "text",
                    "text": f"RESEARCH CONTEXT:\n{full_context}",
                    "cache_control": {"type": "ephemeral"}  # Cache this!
                }
            ]

            # Add conversation history
            if conversation_history:
                history_text = "\n\nPREVIOUS CONVERSATION:\n"
                for turn in conversation_history[-4:]:  # Last 4 turns for context
                    history_text += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n\n"
                user_message_parts.append({
                    "type": "text",
                    "text": history_text
                })

            # Add current question
            user_message_parts.append({
                "type": "text",
                "text": f"\nCURRENT QUESTION: {user_input}"
            })

            # Call Claude with caching
            response = anthropic_client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=2000,
                temperature=0.3,
                system=[{
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }],
                messages=[{
                    "role": "user",
                    "content": user_message_parts
                }]
            )

            # Extract response
            assistant_response = ""
            for block in response.content:
                if block.type == "text":
                    assistant_response += block.text

            # Show cache stats
            cache_created = getattr(response.usage, 'cache_creation_input_tokens', 0)
            cache_read = getattr(response.usage, 'cache_read_input_tokens', 0)
            if cache_read > 0:
                print(f"[CACHE] Read {cache_read} cached tokens (90% savings!)")
            elif cache_created > 0:
                print(f"[CACHE] Created cache of {cache_created} tokens")

            print(f"\nAssistant: {assistant_response}\n")

            # Update conversation history (for multi-turn context)
            conversation_history.append({
                "user": user_input,
                "assistant": assistant_response
            })

            # Extract refinement context (user's mental models, framing, instructions)
            # This is what gets WEIGHTED HIGHER in graph write
            refinement_log.append({
                "user_input": user_input,
                "assistant_response": assistant_response,
                "timestamp": datetime.now().isoformat()
            })

        except KeyboardInterrupt:
            print("\n\n[EXIT] Interrupted by user.")
            # Save refinement context before exiting
            save_refinement_context(refinement_log)
            break
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            continue

    # Save refinement context if user exited normally
    if refinement_log:
        save_refinement_context(refinement_log)


def save_refinement_context(refinement_log):
    """Save refinement context - user's mental models, framing, synthesis instructions"""
    if not refinement_log:
        return

    print("\n[REFINEMENT] Saving refinement context...")

    # Save to session directory
    refinement_file = os.path.join(CURRENT_SESSION_DIR, "refinement_context.json")
    with open(refinement_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "conversation": refinement_log,
            "note": "User's mental models, reframings, and synthesis instructions. WEIGHTED HIGHER than original research in graph write."
        }, f, indent=2)
    print(f"[REFINEMENT] Saved to {refinement_file}")

    # Also save human-readable version
    readable_file = os.path.join(CURRENT_SESSION_DIR, "refinement_context.txt")
    with open(readable_file, 'w', encoding='utf-8') as f:
        f.write("REFINEMENT CONTEXT\n")
        f.write("="*80 + "\n")
        f.write("User's mental models, reframings, and synthesis instructions.\n")
        f.write("IMPORTANT: This context is WEIGHTED HIGHER than original research.\n")
        f.write("="*80 + "\n\n")

        for i, turn in enumerate(refinement_log, 1):
            f.write(f"\n--- Turn {i} ({turn['timestamp']}) ---\n")
            f.write(f"USER: {turn['user_input']}\n\n")
            f.write(f"ASSISTANT: {turn['assistant_response']}\n")
            f.write("\n" + "-"*80 + "\n")

    print(f"[REFINEMENT] Human-readable version: {readable_file}")


async def commit_to_graph(narrative, full_context, refinement_log):
    """
    Commit refined findings to knowledge graph with WEIGHTED context.

    CRITICAL: Refinement context (user's mental models, framing) is weighted HIGHER
    than original research. This is context engineering - user teaches agent how to
    interpret the facts.
    """
    print("\n[COMMIT] Preparing context-engineered graph write...")

    # Extract user's mental models and synthesis instructions from refinement
    user_framing = []
    for turn in refinement_log:
        user_framing.append(f"User: {turn['user_input']}\nResponse: {turn['assistant_response']}")

    refinement_context = "\n\n".join(user_framing) if user_framing else "No refinement context"

    # Build weighted narrative for graph
    # Format emphasizes refinement context > original research
    weighted_narrative = f"""
USER'S CONTEXT AND FRAMING (PRIMARY - HIGHEST WEIGHT):
{refinement_context}

ORIGINAL RESEARCH FINDINGS (SUPPORTING CONTEXT):
{narrative}

SYNTHESIS INSTRUCTION:
When interpreting this research, prioritize the user's mental models and framing above.
The original research provides facts; the refinement context provides the lens through which to understand them.
"""

    print(f"[COMMIT] Refinement turns: {len(refinement_log)}")
    print(f"[COMMIT] Writing to Graphiti knowledge graph...")

    result = await graphiti_client.commit_episode(
        agent_id="helldiver_refined",
        original_query="Arthur AI - NYC-based company",
        tasking_context={
            "summary": "Multi-agent research with context-engineered refinement",
            "refinements": [turn['user_input'] for turn in refinement_log],
            "weighting": "refinement_context > original_research"
        },
        findings_narrative=weighted_narrative,
        user_context="Helldiver Research Agent - Context engineered through interactive refinement"
    )

    if result["status"] == "success":
        print(f"[SUCCESS] {result['message']}")
        print(f"[GRAPH] Episode: '{result['episode_name']}'")
        print(f"[GRAPH] Refinement context weighted HIGHER than original research")
    else:
        print(f"[ERROR] {result.get('message', 'Unknown error')}")


async def test_graphiti_integration():
    """Test Graphiti/MCP integration by writing context to knowledge graph"""
    print("\n[GRAPHITI TEST] Testing Graphiti/MCP Integration")
    print("="*80)

    # Check if context files exist
    context_files = [
        os.path.join(CONTEXT_DIR, "academic_researcher.txt"),
        os.path.join(CONTEXT_DIR, "industry_intelligence.txt"),
        os.path.join(CONTEXT_DIR, "tool_analyzer.txt"),
        os.path.join(CONTEXT_DIR, "critical_analysis.txt")
    ]

    missing_files = [f for f in context_files if not os.path.exists(f)]
    if missing_files:
        print(f"\n[ERROR] Missing context files. Run research first:")
        for f in missing_files:
            print(f"  - {f}")
        print("\nRun: python helldiver_agent.py")
        return

    print(f"\n[GRAPHITI] Found {len(context_files)} context files")

    # Load all context
    all_context = ""
    for context_file in context_files:
        print(f"[GRAPHITI] Loading {os.path.basename(context_file)}...")
        with open(context_file, 'r', encoding='utf-8') as f:
            all_context += f"\n\n{'='*80}\n"
            all_context += f.read()

    print(f"\n[GRAPHITI] Total context: {len(all_context)} characters")

    # Load narrative for summary
    narrative = ""
    if os.path.exists(FINDINGS_FILE):
        with open(FINDINGS_FILE, 'r', encoding='utf-8') as f:
            narrative = f.read()

    # Test write to graph using commit_episode
    try:
        print(f"\n[GRAPHITI] Writing context to knowledge graph...")

        result = await graphiti_client.commit_episode(
            agent_id="helldiver_test",
            original_query="Arthur AI - NYC-based company",
            tasking_context={
                "summary": "Test of Graphiti integration with full research context",
                "refinements": []
            },
            findings_narrative=narrative if narrative else all_context,
            user_context="Testing Helldiver Research Agent Graphiti/MCP integration"
        )

        if result["status"] == "success":
            print(f"[GRAPHITI] {result['message']}")
            print(f"[GRAPHITI] Episode: '{result['episode_name']}'")
        else:
            print(f"[GRAPHITI ERROR] {result.get('message', 'Unknown error')}")

    except Exception as e:
        print(f"\n[GRAPHITI ERROR] Failed to write to graph: {str(e)}")
        raise


def main(skip_research=False, test_graphiti=False, refine=False):
    """Main entry point"""
    global CURRENT_SESSION_DIR

    # Handle interactive refinement mode
    if refine:
        # Use latest session
        CURRENT_SESSION_DIR = get_latest_session()
        if not CURRENT_SESSION_DIR:
            print("[ERROR] No research session found. Run research first.")
            return
        print(f"[SESSION] Using session: {os.path.basename(CURRENT_SESSION_DIR)}")
        interactive_refinement()
        return

    # Handle test modes
    if test_graphiti:
        asyncio.run(test_graphiti_integration())
        return

    research_query = "Arthur AI - NYC-based company"
    tasking_context = """Research Arthur AI company: their product, story, competitive edge, competitors,
    what differentiates them. Focus on what makes their product uniquely valuable vs competitors.
    Emphasize their competitive advantages and unique selling points."""

    # Create new research session
    session_name = "arthur_ai"
    CURRENT_SESSION_DIR = create_session_dir(session_name)
    print(f"\n[HELLDIVER] Starting Research Mission with Batch API")
    print(f"[SESSION] Created session: {os.path.basename(CURRENT_SESSION_DIR)}")
    print(f"Query: {research_query}")
    print(f"Context: {tasking_context}\n")

    # Create session metadata
    session_meta = os.path.join(CURRENT_SESSION_DIR, "session.json")
    with open(session_meta, 'w') as f:
        json.dump({
            "query": research_query,
            "tasking_context": tasking_context,
            "created_at": datetime.now().isoformat(),
            "session_name": session_name
        }, f, indent=2)

    try:
        # Skip research if requested
        if skip_research:
            print("[SKIP] Skipping research, loading from context files...")
            if not os.path.exists(CONTEXT_DIR):
                print("[ERROR] No context directory found. Run research first.")
                return

            # Load from context files
            worker_results = {}
            for worker_name in ['academic_researcher', 'industry_intelligence', 'tool_analyzer']:
                context_file = os.path.join(CONTEXT_DIR, f"{worker_name}.txt")
                if os.path.exists(context_file):
                    with open(context_file, 'r', encoding='utf-8') as f:
                        worker_results[worker_name] = f.read()

            critical_file = os.path.join(CONTEXT_DIR, "critical_analysis.txt")
            if os.path.exists(critical_file):
                with open(critical_file, 'r', encoding='utf-8') as f:
                    critical_analysis = f.read()
            else:
                critical_analysis = "No critical analysis found"

            # Skip to synthesis
            narrative = synthesize_narrative(worker_results, critical_analysis, research_query, tasking_context)
            write_findings(narrative, research_query)
            write_status("complete", f"Research complete! See {FINDINGS_FILE}")
            print(f"\n[COMPLETE] Synthesis complete! Findings written to {FINDINGS_FILE}")
            return
        # Check if we can resume from an existing batch
        resume_batch_id = None
        if os.path.exists(BATCH_STATE_FILE):
            with open(BATCH_STATE_FILE, 'r') as f:
                batch_state = json.load(f)
                resume_batch_id = batch_state.get("batch_id")
                print(f"[RESUME] Found existing batch {resume_batch_id}")

        if resume_batch_id:
            # Resume from existing batch
            print(f"[RESUME] Resuming from batch {resume_batch_id}...")
            batch_id = resume_batch_id
        else:
            # Step 1: Create batch with 3 workers
            batch = create_worker_batch(research_query, tasking_context)
            batch_id = batch.id

            # Save batch ID for resumption
            with open(BATCH_STATE_FILE, 'w') as f:
                json.dump({"batch_id": batch_id, "timestamp": datetime.now().isoformat()}, f)

        # Step 2: Poll until complete
        completed_batch = poll_batch_completion(batch_id)

        # Step 3: Extract results
        worker_results = extract_batch_results(batch_id)

        # Step 4: Critical analyst review
        critical_analysis = run_critical_analyst(worker_results, research_query, tasking_context)

        # Step 5: Synthesize narrative
        narrative = synthesize_narrative(worker_results, critical_analysis, research_query, tasking_context)

        # Step 6: Write findings
        write_findings(narrative, research_query)
        write_status("complete", f"Research complete! See {FINDINGS_FILE}")

        print(f"\n[COMPLETE] Research complete! Findings written to {FINDINGS_FILE}")
        print(f"\nNarrative Preview:")
        print("="*80)
        print(narrative[:500] + "...")

    except Exception as e:
        write_status("error", str(e))
        print(f"\n[ERROR] {str(e)}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Helldiver Research Agent - Multi-agent research with Batch API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python helldiver_agent.py                    # Run full research
  python helldiver_agent.py --refine           # Interactive chat with research (like Claude Desktop)
  python helldiver_agent.py --test-graphiti    # Test Graphiti/MCP integration
  python helldiver_agent.py --skip-research    # Skip research, use cached context
        """
    )
    parser.add_argument(
        '--refine',
        action='store_true',
        help='Interactive refinement mode - chat with research using cached context'
    )
    parser.add_argument(
        '--test-graphiti',
        action='store_true',
        help='Test Graphiti/MCP integration (write context to knowledge graph)'
    )
    parser.add_argument(
        '--skip-research',
        action='store_true',
        help='Skip research phase, load from cached context files'
    )

    args = parser.parse_args()
    main(skip_research=args.skip_research, test_graphiti=args.test_graphiti, refine=args.refine)
