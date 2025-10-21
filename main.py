"""
Helldiver Research Agent - Entry Point

Clean, minimal main that orchestrates the research cycle.

Flow:
1. User provides research query
2. Tasking conversation (clarify what to research)
3. Research execution (3 workers → critical → synthesis)
4. Refinement conversation (user asks questions, explores findings)
5. Trigger deep research OR exit

Repeat steps 4-5 until user exits.
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.session import ResearchSession
from core.research_cycle import run_research_cycle
from graph.client import GraphClient
import workers.research  # Import module to set TEST_MODE
from utils.files import distill_conversation

# Parse command line args
parser = argparse.ArgumentParser(description='Helldiver Research Agent')
parser.add_argument('--test', action='store_true', help='Test mode: fast research with Haiku')
parser.add_argument('--refine', type=str, help='Resume existing session from directory')
args = parser.parse_args()

# Set test mode globally
if args.test:
    import workers.research
    workers.research.TEST_MODE = True
    print("[TEST MODE] Fast 30-second research (Haiku, 500 tokens, no web search)\n")


def print_header(text: str):
    """Print section header."""
    print("\n" + "="*80)
    print(text)
    print("="*80 + "\n")


def generate_episode_name(query: str) -> str:
    """
    Generate a clean episode name for research using LLM.

    COPIED FROM OLD CODE - uses LLM to convert query to clean episode name

    IMPORTANT: Episode names are used for:
    1. Folder names in the file system
    2. Episode titles in the knowledge graph
    3. Future search and retrieval

    Episode names should be:
    - Concise (3-8 words)
    - Descriptive of what was researched
    - Keyword-focused (easy to find later)
    - Professional (no verbose metadata)

    Args:
        query: The research query

    Returns:
        Clean episode name (approved by user)
    """
    from anthropic import Anthropic
    anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = f"""Generate a clean episode name for this research query.

RESEARCH QUERY: {query}

Episode names are CRITICAL for:
1. File organization - folders are named after episodes
2. Knowledge graph titles - users search by episode name
3. Future discoverability - must contain key terms

Generate a concise episode name (3-8 words) that:
- Captures what will be researched
- Uses searchable keywords
- Is professional and clean
- Converts conversational queries into structured names

Examples:
Query: "arthur ai based on out nyc" → "Arthur AI product and market analysis"
Query: "how to optimize react performance" → "React performance optimization strategies"
Query: "kubernetes security best practices 2024" → "Kubernetes security best practices"
Query: "I want to learn about lighthouse construction" → "Lighthouse construction engineering and design"

Respond with ONLY the episode name, nothing else."""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=100,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )

    suggested_name = ""
    for block in response.content:
        if block.type == "text":
            suggested_name = block.text.strip()

    # Show to user and get approval
    print(f"\n{'='*80}")
    print("EPISODE NAME GENERATION")
    print(f"{'='*80}")
    print(f"\nI suggest naming this episode: '{suggested_name}'")
    print("\nThis name will be used for:")
    print("  - Folder name in your file system")
    print("  - Episode title in the knowledge graph")
    print("  - Future search and retrieval")
    print("\nYou can approve it or provide a different name.\n")

    user_input = input("Episode name (press Enter to approve, or type a different name): ").strip()

    if user_input:
        final_name = user_input
        print(f"[APPROVED] Using your name: '{final_name}'")
    else:
        final_name = suggested_name
        print(f"[APPROVED] Using suggested name: '{final_name}'")

    return final_name


def tasking_conversation(query: str) -> dict:
    """
    Tasking phase: Socratic questioning to understand what user wants.
    Agent is a mentor helping refine the research question.

    COPIED FROM OLD CODE - uses intent detection, not trigger phrases

    Returns:
        Dict with:
        - refined_query: What we're going to research
        - conversation_history: Full conversation
        - summary: Summary for context
    """
    from anthropic import Anthropic
    anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    print("\nI'm here to help you conduct deep research. Think of me as your research mentor.")
    print("I'll ask some questions to understand exactly what you're looking for.\n")

    # Socratic questioning using Claude
    print("[THINKING] Let me ask some clarifying questions...\n")

    clarifying_prompt = f"""You are a research mentor helping a user refine their research question.

User wants to research: "{query}"

Your role:
1. Ask 2-3 clarifying questions to understand:
   - What specific aspects they care about most
   - What they plan to do with this information
   - Any particular angles or focus areas

2. Be socratic - help them think deeper about what they really want to know
3. Be concise but insightful
4. Remember: the ultimate outcome is writing findings to a knowledge graph for future reference

Format your response as a natural conversation. Ask your clarifying questions."""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        temperature=0.7,
        messages=[{"role": "user", "content": clarifying_prompt}]
    )

    clarifying_questions = ""
    for block in response.content:
        if block.type == "text":
            clarifying_questions = block.text

    print(f"{clarifying_questions}\n")

    # Open-ended conversational loop - user decides when done
    conversation_history = [{"role": "assistant", "content": clarifying_questions}]

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        # Use LLM to detect intent - don't keyword match!
        intent_check = f"""User said: "{user_input}"

Is the user indicating they're ready to proceed with research, or do they want to continue the conversation?

Respond with ONLY ONE WORD:
- "PROCEED" if they want to start research (e.g., "go", "let's do it", "start", "yes do it", etc.)
- "CONTINUE" if they're still clarifying or asking questions"""

        intent_response = anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=10,
            temperature=0,
            messages=[{"role": "user", "content": intent_check}]
        )

        intent = ""
        for block in intent_response.content:
            if block.type == "text":
                intent = block.text.strip().upper()

        if "PROCEED" in intent:
            # Capture the final user message before breaking
            conversation_history.append({"role": "user", "content": user_input})
            break

        # Continue conversation
        conversation_history.append({"role": "user", "content": user_input})

        # Agent responds with more questions or acknowledgment
        follow_up_prompt = f"""You are a research mentor in conversation with a user.

Original query: "{query}"

Conversation so far:
{chr(10).join([f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history])}

The user just said: "{user_input}"

Your role:
- If you need more clarity, ask follow-up questions
- If you understand their direction, acknowledge and ask if they're ready to proceed
- Be conversational and natural
- Don't artificially limit the conversation

Respond naturally to continue the conversation."""

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=800,
            temperature=0.7,
            messages=[{"role": "user", "content": follow_up_prompt}]
        )

        agent_response = ""
        for block in response.content:
            if block.type == "text":
                agent_response = block.text

        print(f"\n{agent_response}\n")
        conversation_history.append({"role": "assistant", "content": agent_response})

    # Confirm understanding
    print("\n[UNDERSTANDING] Let me confirm what I'll research...")

    # Build conversation summary for confirmation
    conversation_text = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in conversation_history])

    confirmation_prompt = f"""Based on this entire conversation:

{conversation_text}

Summarize what you understand they want to research.
Be specific about focus areas and what will be valuable for them."""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        temperature=0.3,
        messages=[{"role": "user", "content": confirmation_prompt}]
    )

    summary = ""
    for block in response.content:
        if block.type == "text":
            summary = block.text

    print(f"\n{summary}\n")

    # Wait for explicit confirmation
    print("Ready to start deep research? This will take 3-5 minutes.")
    approval = input("Type 'go' to start: ").strip().lower()

    if approval not in ['go', 'yes', 'start', 'do it', 'research']:
        print("[CANCELLED] Research cancelled.")
        sys.exit(0)

    # Return tasking context
    return {
        "refined_query": query,  # Keep original query
        "conversation_history": conversation_history,
        "summary": summary
    }


def refinement_conversation(session: ResearchSession):
    """
    Refinement phase: Interactive conversation with research context loaded.
    User can ask questions, request deep research, or exit.

    SIMPLIFIED VERSION - uses intent detection from old code

    Args:
        session: Current research session

    Returns:
        Deep research topic (str) or None if exiting
    """
    from anthropic import Anthropic
    anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    print_header("Refinement Phase")
    print("\nResearch complete! Ready to discuss findings.")
    print("\nYou can:")
    print("  - Ask questions about the research")
    print("  - Request deep research on a specific topic")
    print("  - Type 'exit' to end session\n")

    # Load research findings
    research_findings = ""
    research_dir = session.next_episode_dir(session.query)

    # Try to load worker files for context
    worker_files = ["academic_researcher.txt", "industry_intelligence.txt", "tool_analyzer.txt", "critical_analysis.txt"]
    for worker_file in worker_files:
        file_path = os.path.join(research_dir, worker_file)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                research_findings += f"\n\n=== {worker_file} ===\n{f.read()[:2000]}"  # First 2000 chars

    conversation_history = []

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        # Use LLM to detect intent - NO KEYWORD MATCHING
        intent_prompt = f"""User said: "{user_input}"

Context: We're in refinement phase after completing research. The user can:
1. Ask questions about the research
2. Request deep research on a specific topic
3. Exit the session

What is the user's intent?

Respond with ONE of these intents:
- EXIT - wants to end session
- DEEP_RESEARCH - wants to spawn deep research on a topic
- QUESTION - wants to ask about the research

Respond with ONLY the intent word."""

        intent_response = anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=20,
            temperature=0,
            messages=[{"role": "user", "content": intent_prompt}]
        )

        intent = ""
        for block in intent_response.content:
            if block.type == "text":
                intent = block.text.strip().upper()

        # Handle intents
        if "EXIT" in intent:
            print("\n[EXITING] Session complete.")
            session.state = "COMPLETE"
            session.save()
            return None

        if "DEEP_RESEARCH" in intent:
            # Save user's deep research request to refinement history
            # This captures "research option 1" or similar request
            session.add_refinement_turn(user_input, f"[Triggering deep research based on: {user_input}]")

            # Extract topic using LLM
            topic_extract = f"""User said: "{user_input}"

They want deep research. What specific topic do they want researched?

Extract ONLY the topic (2-10 words). Be specific."""

            topic_response = anthropic_client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=100,
                temperature=0,
                messages=[{"role": "user", "content": topic_extract}]
            )

            topic = ""
            for block in topic_response.content:
                if block.type == "text":
                    topic = block.text.strip()

            print(f"\n[UNDERSTANDING] Deep research topic: {topic}")
            print("This will spawn 3 new specialist workers + critical analyst (3-5 minutes).")

            # Confirm with intent detection
            confirm_input = input("\nReady to proceed? ").strip()

            confirm_check = f"""User said: "{confirm_input}"

Are they confirming to proceed?

Respond with ONLY:
- YES if confirming
- NO if declining"""

            confirm_response = anthropic_client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=5,
                temperature=0,
                messages=[{"role": "user", "content": confirm_check}]
            )

            confirmation = ""
            for block in confirm_response.content:
                if block.type == "text":
                    confirmation = block.text.strip().upper()

            if "YES" in confirmation:
                # Don't save the "go" confirmation - just return topic
                return topic
            else:
                print("[CANCELLED] Deep research cancelled.\n")
                continue

        # Regular question - answer from research context
        conversation_history.append({"role": "user", "content": user_input})

        # Answer using research findings as context
        system_prompt = f"""You are helping the user explore research findings.

Research query: {session.query}

Research findings (excerpts):
{research_findings[:8000]}

Help the user understand the findings, explore specific aspects, and identify what's worth deep-diving on."""

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2000,
            temperature=0.7,
            system=system_prompt,
            messages=conversation_history
        )

        assistant_msg = ""
        for block in response.content:
            if block.type == "text":
                assistant_msg += block.text

        print(f"\n{assistant_msg}\n")
        conversation_history.append({"role": "assistant", "content": assistant_msg})

        # Record in session
        session.add_refinement_turn(user_input, assistant_msg)
        session.save()


async def main():
    """Main entry point."""
    print_header("Welcome to Helldiver Research Agent")

    # Initialize graph client
    graph_client = GraphClient()

    # Load or create session
    if args.refine:
        # Resume existing session
        try:
            session = ResearchSession.load(args.refine)
            print(f"[LOADED] Resumed session: {session.original_query}")
            print(f"[STATE] Episodes completed: {session.episode_count}\n")

        except Exception as e:
            print(f"[ERROR] Could not load session: {e}")
            return

    else:
        # Start new session
        query = input("What would you like to research? ").strip()

        if not query:
            print("[ERROR] No query provided")
            return

        # Tasking conversation
        tasking_result = tasking_conversation(query)
        refined_query = tasking_result["refined_query"]
        tasking_summary = tasking_result["summary"]

        # Generate clean episode name using LLM (FROM OLD CODE)
        episode_name = generate_episode_name(refined_query)

        # Create session directory using clean episode name
        # Just replace spaces and slashes - KEEP IT SIMPLE
        session_name = episode_name.replace(" ", "_").replace("/", "_")
        # Limit to 80 chars for safety
        if len(session_name) > 80:
            session_name = session_name[:80]
        session_dir = os.path.join("context", session_name)
        os.makedirs(session_dir, exist_ok=True)

        session = ResearchSession(
            session_dir=session_dir,
            query=refined_query,
            state="RESEARCH"
        )
        session.tasking_context = tasking_result
        session.save()

        # Execute initial research (use clean episode name, not raw query)
        print_header("Executing Initial Research")
        result = await run_research_cycle(
            session=session,
            graph_client=graph_client,
            query=episode_name,  # Use clean episode name
            tasking_summary=tasking_summary
        )

        print(f"\n[COMPLETE] Research finished! Ready to discuss findings.\n")

    # Refinement loop (ask questions, trigger deep research, or exit)
    while True:
        deep_topic = refinement_conversation(session)

        if not deep_topic:
            # User exited
            break

        # Generate clean episode name for deep research (FROM OLD CODE)
        episode_name = generate_episode_name(deep_topic)

        # Execute deep research
        print_header(f"Executing Deep Research: {episode_name}")

        # Create summary of refinement context
        from utils.files import convert_tasking_to_conversation, format_conversation_for_display
        refinement_text = format_conversation_for_display(session.pending_refinement)
        tasking_summary = f"Context from refinement conversation:\n{refinement_text[:500]}..."

        result = await run_research_cycle(
            session=session,
            graph_client=graph_client,
            query=episode_name,  # Use clean episode name
            tasking_summary=tasking_summary
        )

        print(f"\n[COMPLETE] Research finished! Ready to discuss findings.\n")

    # Cleanup
    graph_client.close()
    print("\n[COMPLETE] Session saved to:", session.session_dir)


if __name__ == "__main__":
    asyncio.run(main())
