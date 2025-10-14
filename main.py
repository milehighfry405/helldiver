"""
Helldiver Research Agent - Conversational Interface
Single continuous conversation: Tasking → Research → Refinement → Commit

The agent maintains goal awareness and guides toward knowledge graph commit.
"""

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

# Base context directory
BASE_CONTEXT_DIR = "context"
os.makedirs(BASE_CONTEXT_DIR, exist_ok=True)


class ResearchSession:
    """Manages a single research session with state machine

    ARCHITECTURE NOTE:
    - Session creation is DECOUPLED from filesystem creation
    - Folders are created AFTER episode names are generated and approved
    - This enables clean, user-approved episode names for all research
    """

    def __init__(self):
        """Initialize session state (NO FILESYSTEM I/O)"""
        # Session state
        self.state = "TASKING"
        self.query = None
        self.original_query = None  # Store original query separately (never overwritten)
        self.episode_name = None  # Clean episode name (for folder naming)
        self.tasking_context = {}
        self.research_findings = {}
        self.narrative = ""
        self.refinement_log = []
        self.deep_research_count = 0
        self.full_context = ""  # Cached research context
        self.distilled_context = ""  # Distilled mental models from refinement

        # Episode tracking for graph commits
        self.initial_episode_id = ""  # ID of initial research episode
        self.deep_episode_ids = []  # List of deep research episode IDs

        # Filesystem paths (set by initialize_filesystem)
        self.session_dir = None
        self.initial_research_dir = None

    def initialize_filesystem(self, episode_name: str):
        """Create filesystem structure with clean episode name

        Called AFTER tasking conversation when we have an approved episode name.

        Structure:
            context/
            └── {episode_name}/
                ├── {episode_name}/  (initial research folder)
                ├── session.json
                └── (deep research folders created later)
        """
        # Clean episode name for filesystem (replace spaces with underscores)
        safe_name = episode_name.replace(" ", "_").replace("/", "_")

        # Session folder = episode name
        self.session_dir = os.path.join(BASE_CONTEXT_DIR, safe_name)
        os.makedirs(self.session_dir, exist_ok=True)

        # Initial research folder = same episode name
        self.initial_research_dir = os.path.join(self.session_dir, safe_name)
        os.makedirs(self.initial_research_dir, exist_ok=True)

        # Store clean episode name
        self.episode_name = episode_name

        # Save initial metadata
        self.save_metadata()

        print_status("FILESYSTEM", f"Created session: {safe_name}")

    def create_deep_research_dir(self, episode_name: str) -> str:
        """Create directory for deep research with clean episode name

        Args:
            episode_name: Clean, approved episode name (e.g., "ICP signals for downmarket")

        Returns:
            Path to deep research directory
        """
        self.deep_research_count += 1

        # Clean episode name for filesystem
        safe_name = episode_name.replace(" ", "_").replace("/", "_")

        # Folder name = clean episode name (NO prefixes like "deep_research_1_")
        deep_dir = os.path.join(self.session_dir, safe_name)
        os.makedirs(deep_dir, exist_ok=True)

        return deep_dir

    def save_metadata(self):
        """Save session metadata"""
        if not self.session_dir:
            # Filesystem not initialized yet
            return

        meta_file = os.path.join(self.session_dir, "session.json")
        with open(meta_file, 'w') as f:
            json.dump({
                "created_at": datetime.now().isoformat(),
                "state": self.state,
                "query": self.query,
                "original_query": self.original_query,
                "episode_name": self.episode_name,
                "deep_research_count": self.deep_research_count,
                "initial_episode_id": self.initial_episode_id,
                "deep_episode_ids": self.deep_episode_ids
            }, f, indent=2)

    def load_research_context(self):
        """Load all research context into memory for refinement"""
        context_parts = []

        # Load initial research
        initial_dir = self.initial_research_dir
        if os.path.exists(initial_dir):
            for filename in ['academic_researcher.txt', 'industry_intelligence.txt', 'tool_analyzer.txt', 'critical_analysis.txt']:
                filepath = os.path.join(initial_dir, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        context_parts.append(f"\n{'='*80}\n{filename.upper()}\n{'='*80}\n{f.read()}")

        # Load deep research - supports both old and new folder structure
        # Old: deep_research_1_Topic_Name/
        # New: Clean_Episode_Name/
        if self.session_dir and os.path.exists(self.session_dir):
            # Find all subdirectories that contain research files (exclude session folder itself)
            initial_folder_name = os.path.basename(self.initial_research_dir)
            for subdir in os.listdir(self.session_dir):
                subdir_path = os.path.join(self.session_dir, subdir)

                # Skip if not a directory, or if it's the initial research folder
                if not os.path.isdir(subdir_path) or subdir == initial_folder_name:
                    continue

                # Check if it's a research folder (has worker txt files)
                if os.path.exists(os.path.join(subdir_path, "academic_researcher.txt")):
                    # This is a deep research folder
                    for filename in os.listdir(subdir_path):
                        if filename.endswith('.txt'):
                            with open(os.path.join(subdir_path, filename), 'r', encoding='utf-8') as f:
                                context_parts.append(f"\n{'='*80}\nDEEP RESEARCH - {subdir}: {filename.upper()}\n{'='*80}\n{f.read()}")

        self.full_context = "\n".join(context_parts)
        return self.full_context


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "="*80)
    print(text)
    print("="*80)


def print_status(status: str, message: str = ""):
    """Print status message"""
    if message:
        print(f"[{status}] {message}")
    else:
        print(f"[{status}]")


def generate_episode_name(query: str, research_content: str = None) -> str:
    """
    Generate a clean episode name for research using LLM.

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
        research_content: Optional - actual research content to analyze

    Returns:
        Clean episode name (approved by user)
    """

    if research_content:
        # Generate name from research content (retroactive naming)
        prompt = f"""Based on this research content, generate a clean episode name.

RESEARCH QUERY: {query}

RESEARCH CONTENT (first 3000 chars):
{research_content[:3000]}

Episode names are CRITICAL for:
1. File organization - folders are named after episodes
2. Knowledge graph titles - users search by episode name
3. Future discoverability - must contain key terms

Generate a concise episode name (3-8 words) that:
- Captures what was researched
- Uses searchable keywords
- Is professional and clean
- Omits verbose metadata like "based on conversation" or "they want"

Examples of GOOD episode names:
- "Arthur AI product and market analysis"
- "Downmarket ICP signals for Arthur AI"
- "React performance optimization strategies"
- "Kubernetes security best practices"

Examples of BAD episode names:
- "Based on the conversation, they want deep research on..." (verbose metadata)
- "Research about some stuff" (vague)
- "AI ML monitoring tools competitive landscape market analysis 2024" (too long)

Respond with ONLY the episode name, nothing else."""
    else:
        # Generate name from query (prospective naming)
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


def tasking_conversation(session: ResearchSession) -> str:
    """
    Tasking phase: Socratic questioning to understand what user wants.
    Agent is a mentor helping refine the research question.

    Returns next state
    """
    print_header("HELLDIVER RESEARCH AGENT - Tasking Phase")
    print("\nI'm here to help you conduct deep research. Think of me as your research mentor.")
    print("I'll ask some questions to understand exactly what you're looking for.\n")

    # Initial query
    query = input("What would you like to research? ").strip()
    if not query:
        print("No query provided. Exiting.")
        return "COMPLETE"

    session.query = query
    session.original_query = query  # Store original query (never overwritten)

    # Socratic questioning using Claude
    print_status("THINKING", "Let me ask some clarifying questions...")

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

    print(f"\n{clarifying_questions}\n")

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

    # Synthesize tasking context from full conversation
    session.tasking_context = {
        "original_query": query,
        "conversation_history": conversation_history,
        "refined_at": datetime.now().isoformat()
    }

    # Confirm understanding
    print_status("UNDERSTANDING", "Let me confirm what I'll research...")

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

    # Wait for explicit "go"
    print("Ready to start deep research? This will take 3-5 minutes.")
    approval = input("Type 'go' to start: ").strip().lower()

    if approval in ['go', 'yes', 'start', 'do it', 'research']:
        # Generate clean episode name before creating filesystem
        episode_name = generate_episode_name(session.query)

        # Initialize filesystem with clean episode name
        session.initialize_filesystem(episode_name)

        session.state = "RESEARCH"
        session.save_metadata()
        return "RESEARCH"
    else:
        print("Research cancelled.")
        return "COMPLETE"


def run_research_phase(session: ResearchSession, research_dir: str = None) -> str:
    """
    Research phase: Run batch API with 3 workers + critical analyst.
    Shows progress updates every 30s.

    Returns next state
    """
    if research_dir is None:
        research_dir = session.initial_research_dir

    print_header("Deep Research in Progress")
    print("Dispatching 4 specialist workers (this takes 3-5 minutes)")
    print("I'll show progress updates every 30 seconds.\n")

    # Create batch
    tasking_summary = json.dumps(session.tasking_context)

    print_status("BATCH", "Creating research batch...")

    batch = create_worker_batch(session.query, tasking_summary)

    print_status("SUBMITTED", f"Batch {batch.id} submitted")
    print_status("WORKERS", "Academic | Industry | Tool | Critical Analyst")
    print()

    # Poll with progress updates
    start_time = time.time()
    update_interval = 30  # Show update every 30s
    last_update = 0

    while True:
        batch_status = anthropic_client.messages.batches.retrieve(batch.id)

        if batch_status.processing_status == "ended":
            print_status("COMPLETE", "All workers finished!")
            break

        elapsed = int(time.time() - start_time)

        # Show progress every 30s (max 6 updates = 3 minutes)
        if elapsed - last_update >= update_interval and elapsed // update_interval <= 6:
            counts = batch_status.request_counts
            print_status("PROGRESS", f"{elapsed}s elapsed - Processing: {counts.processing} | Complete: {counts.succeeded}")
            last_update = elapsed

        time.sleep(10)  # Poll every 10s

    print()

    # Extract results
    print_status("EXTRACTING", "Gathering findings from workers...")
    worker_results = extract_batch_results(batch.id, research_dir)

    # Run critical analyst
    print_status("ANALYZING", "Critical Analyst reviewing findings...")
    critical_analysis = run_critical_analyst(worker_results, session.query, tasking_summary, research_dir)

    # Synthesize narrative
    print_status("SYNTHESIS", "Synthesizing narrative with Opus 4...")
    narrative = synthesize_narrative(worker_results, critical_analysis, session.query, tasking_summary)

    session.narrative = narrative
    session.research_findings = worker_results

    # Save narrative
    narrative_file = os.path.join(session.session_dir, "narrative.txt")
    with open(narrative_file, 'w', encoding='utf-8') as f:
        f.write(narrative)

    print()
    print_header("Research Complete!")
    print(narrative)
    print()

    # Determine if this is initial or deep research
    is_deep_research = research_dir != session.initial_research_dir
    research_type = "deep" if is_deep_research else "initial"
    parent_id = session.initial_episode_id if is_deep_research else None

    # Commit research episodes to graph (one per worker)
    print_status("GRAPH", f"Writing {research_type} research episodes to knowledge graph...")
    episode_result = asyncio.run(commit_research_episode(
        session=session,
        research_type=research_type,
        narrative=narrative,
        worker_results=worker_results,
        critical_analysis=critical_analysis,
        parent_episode_id=parent_id
    ))

    if episode_result and episode_result.get("status") == "success":
        episode_names = episode_result.get("episode_names", [])
        episode_count = episode_result.get("episode_count", 0)

        # Store first episode name as representative ID
        if episode_names:
            representative_id = f"{session.episode_name} ({episode_count} worker episodes)"
            if is_deep_research:
                session.deep_episode_ids.append(representative_id)
                print_status("SUCCESS", f"Deep research: {episode_count} episodes committed")
            else:
                session.initial_episode_id = representative_id
                print_status("SUCCESS", f"Initial research: {episode_count} episodes committed")
    else:
        print_status("WARNING", "Graph write failed, but continuing")

    # Only transition to refinement if this was initial research
    if not is_deep_research:
        session.state = "REFINEMENT"
        session.save_metadata()
        return "REFINEMENT"
    else:
        # Deep research completes but stays in refinement
        return None


def refinement_conversation(session: ResearchSession) -> str:
    """
    Refinement phase: Interactive conversation with research context loaded.
    User can ask questions, request deep research, or commit to graph.

    Returns next state
    """
    print_header("Refinement Phase")
    print("\nResearch complete! I have all the findings loaded in my context.")
    print("\nYou can:")
    print("  - Ask questions about the research")
    print("  - Request deep research on a specific topic")
    print("  - Type 'commit' to write findings to knowledge graph")
    print("  - Type 'exit' to end session\n")

    # Load all research context
    print_status("LOADING", "Loading research context...")
    session.load_research_context()
    print_status("READY", f"Loaded {len(session.full_context)} characters of research\n")

    # Refinement loop - initialize with previous conversation if resuming session
    conversation_history = []
    if session.refinement_log:
        # Load previous conversation turns for continuity
        for turn in session.refinement_log:
            conversation_history.append({
                "user": turn["user_input"],
                "assistant": turn["assistant_response"]
            })
        print_status("CONTINUITY", f"Loaded {len(session.refinement_log)} previous conversation turns\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        # Use LLM to detect intent - NO KEYWORD MATCHING
        intent_prompt = f"""User said: "{user_input}"

Context: We're in refinement phase after completing research. The user can:
1. Ask questions about the research
2. Request deep research on a specific topic
3. Commit findings to knowledge graph
4. Exit the session

What is the user's intent?

Respond with ONE of these intents:
- EXIT - wants to end session
- COMMIT - wants to write to knowledge graph
- DEEP_RESEARCH - wants to spawn deep research on a topic
- QUESTION - wants to ask about the research
- UNCLEAR - the input is ambiguous, incomplete, or you cannot confidently determine intent

IMPORTANT: If you're unsure or the message seems incomplete, respond with UNCLEAR.
Do not guess. Be explicit about uncertainty.

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
            return "COMPLETE"

        if "UNCLEAR" in intent:
            # Ask for clarification instead of guessing
            print("\nI'm not sure what you want me to do. Could you clarify?")
            print("You can:")
            print("  - Ask a question about the research")
            print("  - Request deep research on a specific topic")
            print("  - Type 'commit' to write to knowledge graph")
            print("  - Type 'exit' to end session\n")
            continue

        if "COMMIT" in intent:
            session.state = "COMMIT"
            session.save_metadata()
            return "COMMIT"

        if "DEEP_RESEARCH" in intent:
            # Extract topic using LLM WITH conversation context
            # Build recent conversation context (last 3 turns to keep it focused)
            recent_context = ""
            if conversation_history:
                recent_turns = conversation_history[-3:]  # Last 3 turns
                recent_context = "\n\nRECENT CONVERSATION:\n"
                for turn in recent_turns:
                    recent_context += f"USER: {turn['user']}\nASSISTANT: {turn['assistant']}\n\n"

            topic_extract = f"""User said: "{user_input}"
{recent_context}

They want deep research. What specific topic do they want researched?

If they said something like "all of those" or "those topics", look at the recent conversation to see what topics were just discussed.

Extract ONLY the topic (2-10 words). Be specific. If multiple topics, list them comma-separated."""

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

            print(f"\nYou're requesting deep research on: '{topic}'")
            print("This will spawn 4 new specialist workers (3-5 minutes).")

            # Confirm with intent detection
            confirm_input = input("\nProceed? ").strip()

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
                    # Generate clean episode name for this deep research
                    episode_name = generate_episode_name(topic)

                    # Create deep research dir with clean name
                    deep_dir = session.create_deep_research_dir(episode_name)

                    # Temporarily change state
                    old_query = session.query
                    session.query = episode_name

                    # Run research
                    run_research_phase(session, research_dir=deep_dir)

                    # Restore query
                    session.query = old_query

                    # Reload context with new research
                    session.load_research_context()
                    print_status("UPDATED", "Research context updated with new findings\n")
                    continue
            continue

        # Regular refinement question - use cached context
        print_status("THINKING", "")

        # Build message with prompt caching
        system_prompt = """You are a research assistant in refinement mode - CONTEXT ENGINEERING phase.

CONTEXT: Deep research was conducted. You have detailed findings from specialist workers.

YOUR CRITICAL ROLE:
1. EXTRACT USER'S MENTAL MODEL - When user says:
   - "I'm more interested in X than Y"
   - "Think about this as [framing]"
   - "The real story here is..."
   → These are INSTRUCTIONS for how to interpret the research.

2. IDENTIFY REFRAMING - When user shifts perspective:
   - "It's not about the tech, it's about GTM"
   → Make these reframings explicit

3. CAPTURE SYNTHESIS INSTRUCTIONS:
   - "When you write to graph, emphasize X"
   → These are WEIGHTED HIGHER than original research

4. SUPPORT WAVE FUNCTION COLLAPSE:
   - User may explore tangents
   - Answer naturally, trust they'll connect back

5. GOAL AWARENESS:
   - The ultimate outcome is committing to knowledge graph
   - Guide user toward that, but never assume
   - Suggest "ready to commit?" when appropriate

Be conversational, insightful, and help them think deeper."""

        user_message_parts = [
            {
                "type": "text",
                "text": f"RESEARCH CONTEXT:\n{session.full_context}",
                "cache_control": {"type": "ephemeral"}
            }
        ]

        # Add distilled context from previous refinement (if resuming session)
        if session.distilled_context:
            user_message_parts.append({
                "type": "text",
                "text": f"\n\nPREVIOUS REFINEMENT INSIGHTS:\n{session.distilled_context}\n\n(The user has already explored these aspects. Build on this understanding.)"
            })

        # Add conversation history from THIS session
        if conversation_history:
            history_text = "\n\nCURRENT CONVERSATION:\n"
            for turn in conversation_history[-4:]:
                history_text += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n\n"
            user_message_parts.append({"type": "text", "text": history_text})

        # Add current question
        user_message_parts.append({"type": "text", "text": f"\nCURRENT QUESTION: {user_input}"})

        # Call Claude
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2000,
            temperature=0.3,
            system=[{
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}
            }],
            messages=[{"role": "user", "content": user_message_parts}]
        )

        assistant_response = ""
        for block in response.content:
            if block.type == "text":
                assistant_response += block.text

        # Show cache stats
        cache_read = getattr(response.usage, 'cache_read_input_tokens', 0)
        if cache_read > 0:
            print_status("CACHE", f"Read {cache_read} cached tokens (90% savings!)")

        print(f"\nAssistant: {assistant_response}\n")

        # Log refinement
        conversation_history.append({"user": user_input, "assistant": assistant_response})
        session.refinement_log.append({
            "user_input": user_input,
            "assistant_response": assistant_response,
            "timestamp": datetime.now().isoformat()
        })

        # Save refinement context
        save_refinement_context(session)


async def commit_research_episode(
    session: ResearchSession,
    research_type: str,  # "initial" or "deep"
    narrative: str,
    worker_results: dict,
    critical_analysis: str,
    parent_episode_id: str = None
) -> dict:
    """
    Commit research episodes to knowledge graph - ONE EPISODE PER WORKER for optimal chunking.

    Based on Graphiti best practices:
    - Episode size should be 1,000-2,000 tokens for rich entity extraction
    - Smaller episodes = more granular, detailed entity extraction
    - Larger episodes = sparse, high-level extraction

    Worker reports are ~1,400-2,600 tokens each (optimal range).

    Args:
        session: Current research session
        research_type: "initial" or "deep"
        narrative: Synthesized narrative from workers
        worker_results: Dict of worker findings
        critical_analysis: Critical analyst review
        parent_episode_id: ID of parent episode (for deep research)

    Returns:
        Dict with status and list of episode_names
    """
    from datetime import datetime

    # Generate metadata for grouping episodes
    session_name = session.episode_name or session.query
    safe_session_name = session_name.replace(" ", "_").replace("/", "_")
    timestamp = datetime.now().isoformat()

    # Group ID hierarchy: helldiver_research/{session}/{type}
    group_id = f"helldiver_research/{safe_session_name}/{research_type}"

    # Commit one episode per worker (optimal chunking)
    worker_mapping = {
        "academic_researcher": "Academic Research",
        "industry_intelligence": "Industry Intelligence",
        "tool_analyzer": "Tool Analysis",
        "critical_analysis": "Critical Analysis"  # Critical analyst gets own episode too
    }

    episode_results = []

    # Commit worker episodes
    for worker_id, worker_name in worker_mapping.items():
        if worker_id == "critical_analysis":
            findings = critical_analysis
        else:
            findings = worker_results.get(worker_id, "")

        if not findings:
            continue

        # Episode name: "{session_name} - {worker_name}"
        episode_name = f"{session_name} - {worker_name}"

        # Episode body: Just the worker findings (focused, optimal size)
        episode_body = f"""Research Query: {session.query}
Research Type: {research_type.title()} Research
Worker Role: {worker_name}

{findings}"""

        if parent_episode_id:
            episode_body += f"\n\nThis deep research builds on initial research: {parent_episode_id}"

        # Source description: Links episodes from same session
        source_description = f"{research_type.title()} Research | Session: {session_name} | {timestamp}"

        # Commit episode
        result = await graphiti_client.commit_episode(
            agent_id="helldiver",
            original_query=episode_name,  # Use full episode name as query
            tasking_context={
                "type": research_type,
                "worker": worker_name,
                "session": session_name,
                "parent_episode": parent_episode_id if parent_episode_id else "root",
                "group_id": group_id,
                "source_description": source_description
            },
            findings_narrative=episode_body,
            user_context=source_description
        )

        if result and result.get("status") == "success":
            episode_results.append(result.get("episode_name", episode_name))
            print_status("EPISODE", f"✓ {episode_name}")

    # Return summary
    return {
        "status": "success" if episode_results else "error",
        "episode_names": episode_results,
        "episode_count": len(episode_results),
        "message": f"Committed {len(episode_results)} worker episodes"
    }


def commit_to_graph_phase(session: ResearchSession) -> str:
    """
    Commit phase: Write refinement episode linking all research.

    Returns next state
    """
    print_header("Committing Refined Understanding to Knowledge Graph")

    # Distill context at commit time (ONLY ONCE - avoids frequency bias)
    distilled_context = ""
    if session.refinement_log:
        print_status("DISTILLING", "Extracting mental models from full conversation arc...")
        distilled_context = distill_refinement_context(session.refinement_log)
        session.distilled_context = distilled_context

        # Save distilled context to file
        distilled_file = os.path.join(session.session_dir, "refinement_distilled.txt")
        with open(distilled_file, 'w', encoding='utf-8') as f:
            f.write("REFINEMENT CONTEXT - DISTILLED SIGNAL\n")
            f.write("="*80 + "\n")
            f.write("Extracted mental models, reframings, and synthesis instructions.\n")
            f.write("Created at commit time from full conversation arc.\n")
            f.write("IMPORTANT: This context is WEIGHTED HIGHER than original research.\n")
            f.write("="*80 + "\n\n")
            f.write(distilled_context)

        print_status("SAVED", "Distilled context saved to refinement_distilled.txt")

    refinement_context = distilled_context if distilled_context else "No refinement context"

    # Build refinement episode that LINKS to research episodes
    refinement_narrative = f"""
USER'S REFINED UNDERSTANDING (GRAPH-OPTIMIZED):
{refinement_context}

RESEARCH LINEAGE:
- Initial Research Episode: {session.initial_episode_id}"""

    if session.deep_episode_ids:
        for i, episode_id in enumerate(session.deep_episode_ids, 1):
            refinement_narrative += f"\n- Deep Research Episode {i}: {episode_id}"

    refinement_narrative += f"""

SYNTHESIS INSTRUCTION:
This refined understanding provides the interpretive lens for all research episodes listed above.
When connecting concepts from this episode to research findings, prioritize the user's mental models and framing.
The research episodes provide facts; this refinement episode provides the context for understanding them.

Original Query: {session.query}
Refinement Turns: {len(session.refinement_log)}
Weighting: User's context > Research findings
"""

    print_status("WRITING", "Writing refinement episode to knowledge graph...")

    result = asyncio.run(graphiti_client.commit_episode(
        agent_id="helldiver",
        original_query=f"{session.query} - Refined Understanding",
        tasking_context={
            "type": "refinement",
            "initial_episode": session.initial_episode_id,
            "deep_episodes": session.deep_episode_ids,
            "refinement_turns": len(session.refinement_log),
            "weighting": "refinement_context > original_research"
        },
        findings_narrative=refinement_narrative,
        user_context="Helldiver Refinement - User's context-engineered understanding"
    ))

    if result["status"] == "success":
        print_status("SUCCESS", "Refinement episode created")
        print_status("EPISODE", result['episode_name'])
        print_status("LINKED", f"Links to {1 + len(session.deep_episode_ids)} research episodes")
        print_status("WEIGHTING", "Refinement context weighted HIGHER than research")
    else:
        print_status("ERROR", result.get('message', 'Unknown error'))

    print("\nWould you like to start a new research session?")
    new_session = input("You: ").strip()

    # LLM-based intent detection for new session
    intent_prompt = f"""User said: "{new_session}"

Context: We just finished committing research to the knowledge graph. I asked if they want to start a new research session.

What is the user's intent?

Respond with ONLY ONE WORD:
- "YES" if they want to start a new session (e.g., "yes", "sure", "let's do it", "yeah", "okay", etc.)
- "NO" if they don't want a new session (e.g., "no", "nope", "I'm done", "exit", "that's all", etc.)"""

    intent_response = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=10,
        temperature=0,
        messages=[{"role": "user", "content": intent_prompt}]
    )

    intent = ""
    for block in intent_response.content:
        if block.type == "text":
            intent = block.text.strip().upper()

    if "YES" in intent:
        return "NEW_SESSION"
    else:
        return "COMPLETE"


# Helper functions from old helldiver_agent.py

def create_worker_batch(research_query: str, tasking_context: str):
    """Create batch jobs for 3 specialist workers"""

    academic_prompt = """You are an academic researcher specializing in deep technical literature.
Search for papers, technical documentation, and theoretical frameworks.
Use web_search tool extensively. Return dense, signal-rich findings with citations."""

    industry_prompt = """You are an industry analyst who tracks real implementations.
Find case studies, engineering blogs, production use cases.
Use web_search tool extensively. Return proven, real-world usage with metrics."""

    tool_prompt = """You are a tools researcher who understands frameworks and implementations.
Search GitHub, documentation, tool comparisons.
Use web_search tool extensively. Return technical trade-offs and usage patterns."""

    user_message = f"""Research Query: {research_query}

Tasking Context: {tasking_context}

Conduct deep research using your specialized expertise. Use web search extensively."""

    batch = anthropic_client.messages.batches.create(
        requests=[
            {
                "custom_id": "academic_researcher",
                "params": {
                    "model": "claude-sonnet-4-5",
                    "max_tokens": 4000,
                    "temperature": 0.3,
                    "system": academic_prompt,
                    "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                    "messages": [{"role": "user", "content": user_message}]
                }
            },
            {
                "custom_id": "industry_intelligence",
                "params": {
                    "model": "claude-sonnet-4-5",
                    "max_tokens": 4000,
                    "temperature": 0.3,
                    "system": industry_prompt,
                    "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                    "messages": [{"role": "user", "content": user_message}]
                }
            },
            {
                "custom_id": "tool_analyzer",
                "params": {
                    "model": "claude-sonnet-4-5",
                    "max_tokens": 4000,
                    "temperature": 0.3,
                    "system": tool_prompt,
                    "tools": [{"type": "web_search_20250305", "name": "web_search"}],
                    "messages": [{"role": "user", "content": user_message}]
                }
            }
        ]
    )

    return batch


def extract_batch_results(batch_id: str, research_dir: str) -> dict:
    """Extract results from completed batch and save to research directory"""
    results = {}

    for result in anthropic_client.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            custom_id = result.custom_id
            message = result.result.message

            findings = ""
            for block in message.content:
                if block.type == "text":
                    findings += block.text

            results[custom_id] = findings

            # Save to file
            context_file = os.path.join(research_dir, f"{custom_id}.txt")
            with open(context_file, 'w', encoding='utf-8') as f:
                f.write(f"Worker: {custom_id}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Batch ID: {batch_id}\n")
                f.write("="*80 + "\n\n")
                f.write(findings)

    return results


def run_critical_analyst(worker_results: dict, research_query: str, tasking_context: str, research_dir: str) -> str:
    """Run critical analyst to review worker findings"""

    critical_prompt = """You are a skeptical senior researcher who reviews findings.
Score relevance (1-10), filter noise, identify gaps, highlight insights.
Be ruthless about cutting noise. User's time is valuable."""

    critical_message = f"""Original Research Query: {research_query}

Tasking Context: {tasking_context}

ACADEMIC RESEARCHER FINDINGS:
{worker_results.get('academic_researcher', 'No findings')}

INDUSTRY INTELLIGENCE FINDINGS:
{worker_results.get('industry_intelligence', 'No findings')}

TOOL ANALYZER FINDINGS:
{worker_results.get('tool_analyzer', 'No findings')}

Review critically. Score relevance, filter noise, identify gaps."""

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

    # Save to file
    context_file = os.path.join(research_dir, "critical_analysis.txt")
    with open(context_file, 'w', encoding='utf-8') as f:
        f.write(f"Worker: Critical Analyst\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write("="*80 + "\n\n")
        f.write(findings)

    return findings


def synthesize_narrative(worker_results: dict, critical_analysis: str, research_query: str, tasking_context: str) -> str:
    """Synthesize worker findings into dense narrative using Opus 4"""

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

Write as flowing prose, not bullets. Every sentence should carry signal."""

    response = anthropic_client.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=2000,
        temperature=0.4,
        system=[{
            "type": "text",
            "text": "You are a brilliant research synthesizer who creates dense, narrative summaries. Create flowing prose that shows connections and builds understanding.",
            "cache_control": {"type": "ephemeral"}
        }],
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": cached_research, "cache_control": {"type": "ephemeral"}},
                {"type": "text", "text": synthesis_instruction}
            ]
        }]
    )

    narrative = ""
    for block in response.content:
        if block.type == "text":
            narrative += block.text

    return narrative


def distill_refinement_context(refinement_log: list) -> str:
    """
    Distill conversational transcript into structured mental models and key insights.
    Extracts SIGNAL from NOISE for graph commits and agent continuity.
    """
    if not refinement_log:
        return ""

    # Build full conversation for distillation
    conversation_text = "\n\n".join([
        f"USER: {turn['user_input']}\nASSISTANT: {turn['assistant_response']}"
        for turn in refinement_log
    ])

    distillation_prompt = f"""<task>
Extract the essential signal from a conversational refinement session and prepare it for knowledge graph ingestion.

This output will be written to a knowledge graph (Graphiti/Neo4j) that:
- Extracts entities from sentences (people, companies, concepts, tools)
- Identifies relationships between entities (is, has, requires, enables, connects to)
- Links this context to research findings to form a coherent knowledge structure

Your goal: Create clear, entity-rich sentences that enable strong graph connections.
</task>

<instructions>
Analyze the full conversation arc and extract:

1. **Mental Models** - How the user frames the problem
2. **Reframings** - When/how the user corrected direction
3. **Constraints** - Explicit boundaries or requirements
4. **Priorities** - What matters most (relative importance)
5. **Synthesis Instructions** - How to interpret the research findings

Think step-by-step:
- Read the entire conversation to understand the full context
- Identify key moments where the user clarified their thinking
- Note when the user said "actually no" or redirected
- Extract explicit constraints or requirements
- Identify stated priorities or preferences
- Capture synthesis instructions about how to weight findings

CRITICAL for knowledge graph optimization:
- Use explicit entity names (e.g., "Arthur AI" not "they", "Clay enrichment system" not "it")
- Write complete sentences with clear subject-verb-object structure
- Use relational language (is, has, requires, connects to, enables, influences)
- Connect the user's mental models to research concepts explicitly
- Be specific about tools, companies, methodologies, frameworks mentioned
</instructions>

<conversation>
{conversation_text}
</conversation>

<output_format>
Structure your extraction using complete, entity-rich sentences:

## Mental Models
[Complete sentences capturing how the user frames the problem. Use explicit entity names and clear relationships.]

## Reframings
[Complete sentences noting when/how the user corrected direction. Show the before→after shift explicitly.]

## Constraints
[Complete sentences listing explicit boundaries or requirements. Be specific about scope, scale, timeline.]

## Priorities
[Complete sentences or ordered list showing relative importance. Use comparative language.]

## Synthesis Instructions
[Complete sentences capturing directives for interpreting the research. Connect to specific research areas or findings.]

## Key Entities
[List the main entities mentioned: companies, tools, methodologies, roles, concepts. This helps the graph create strong entity nodes.]

Be concise but complete. Each statement should be graph-ready (extractable entities + clear relationships). Omit sections with no relevant content.
</output_format>

<examples>
<example>
<sample_conversation>
USER: I want to research competitors in the ML space
ASSISTANT: [provides general ML competitive landscape]
USER: Actually, I'm only interested in the monitoring tools, not training platforms
ASSISTANT: [provides monitoring-specific research]
USER: Focus on companies under $50M revenue. That's the segment we're targeting.
</sample_conversation>

<sample_output>
## Mental Models
- Interested in ML monitoring tools specifically, not broader ML infrastructure

## Reframings
- Corrected from general "ML space" to specific focus on monitoring tools

## Constraints
- Target companies: under $50M revenue

## Priorities
- Market segment focus more important than comprehensive competitive analysis

## Synthesis Instructions
- None explicitly stated
</sample_output>
</example>

<example>
<sample_conversation>
USER: Can you research pricing models for SaaS analytics tools?
ASSISTANT: [provides pricing research]
USER: This is helpful but I'm not trying to copy them. I want to understand what customers actually value, not just what people charge.
ASSISTANT: [provides value-based analysis]
USER: Perfect. When you write this up, emphasize the value drivers more than the pricing tiers.
</sample_conversation>

<sample_output>
## Mental Models
- Goal is understanding customer value perception, not competitive pricing mimicry

## Reframings
- Shifted from "pricing models" to "what customers value"

## Constraints
- None explicitly stated

## Priorities
- Value drivers > pricing mechanics

## Synthesis Instructions
- Emphasize value drivers over pricing tiers in final writeup
</sample_output>
</example>
</examples>

Now extract the signal from the conversation above."""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,
        temperature=0,
        messages=[{"role": "user", "content": distillation_prompt}]
    )

    distilled = ""
    for block in response.content:
        if block.type == "text":
            distilled = block.text

    return distilled


def save_refinement_context(session: ResearchSession):
    """Save refinement context to session directory"""
    if not session.refinement_log:
        return

    # Save full transcript (for audit trail)
    refinement_file = os.path.join(session.session_dir, "refinement_context.json")
    with open(refinement_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "conversation": session.refinement_log,
            "note": "Full conversation transcript - AUDIT TRAIL ONLY. See refinement_distilled.txt for signal."
        }, f, indent=2)

    # Save full transcript (human-readable for audit)
    readable_file = os.path.join(session.session_dir, "refinement_context.txt")
    with open(readable_file, 'w', encoding='utf-8') as f:
        f.write("REFINEMENT CONTEXT - FULL TRANSCRIPT\n")
        f.write("="*80 + "\n")
        f.write("Full conversation for audit trail.\n")
        f.write("Distilled context created at commit time.\n")
        f.write("="*80 + "\n\n")

        for i, turn in enumerate(session.refinement_log, 1):
            f.write(f"\n--- Turn {i} ({turn['timestamp']}) ---\n")
            f.write(f"USER: {turn['user_input']}\n\n")
            f.write(f"ASSISTANT: {turn['assistant_response']}\n")
            f.write("\n" + "-"*80 + "\n")

    # NOTE: Distillation happens ONLY at commit time to avoid frequency bias
    # (otherwise early turns get distilled 10x more than later turns)


def load_existing_session(session_dir: str) -> ResearchSession:
    """Load an existing session from directory"""
    import json

    if not os.path.exists(session_dir):
        raise ValueError(f"Session directory not found: {session_dir}")

    session_file = os.path.join(session_dir, "session.json")
    if not os.path.exists(session_file):
        raise ValueError(f"No session.json found in {session_dir}")

    with open(session_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Reconstruct session object
    session = ResearchSession.__new__(ResearchSession)
    session.session_dir = session_dir
    session.episode_name = metadata.get('episode_name', None)
    session.state = metadata.get('state', 'REFINEMENT')  # Default to refinement
    session.query = metadata.get('query', '')
    session.original_query = metadata.get('original_query', metadata.get('query', ''))  # Fallback to query if not set
    session.tasking_context = metadata.get('tasking_context', {})
    session.deep_research_count = metadata.get('deep_research_count', 0)
    session.initial_episode_id = metadata.get('initial_episode_id', '')
    session.deep_episode_ids = metadata.get('deep_episode_ids', [])

    # Detect initial research directory (supports both old and new structure)
    # New structure: context/Episode_Name/Episode_Name/
    # Old structure: context/session_research_timestamp/initial_research/
    if session.episode_name:
        safe_name = session.episode_name.replace(" ", "_").replace("/", "_")
        session.initial_research_dir = os.path.join(session_dir, safe_name)
    else:
        # Fallback to old "initial_research" folder for backward compatibility
        session.initial_research_dir = os.path.join(session_dir, "initial_research")

    # If neither exists, try to detect any subdirectory with research files
    if not os.path.exists(session.initial_research_dir):
        for subdir in os.listdir(session_dir):
            subdir_path = os.path.join(session_dir, subdir)
            if os.path.isdir(subdir_path) and os.path.exists(os.path.join(subdir_path, "academic_researcher.txt")):
                session.initial_research_dir = subdir_path
                break

    # Load narrative
    narrative_file = os.path.join(session_dir, "narrative.txt")
    if os.path.exists(narrative_file):
        with open(narrative_file, 'r', encoding='utf-8') as f:
            session.narrative = f.read()
    else:
        session.narrative = ""

    # Load refinement log
    refinement_file = os.path.join(session_dir, "refinement_context.json")
    if os.path.exists(refinement_file):
        with open(refinement_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both old format (dict with 'conversation' key) and new format (direct list)
            if isinstance(data, dict) and 'conversation' in data:
                session.refinement_log = data['conversation']
            elif isinstance(data, list):
                session.refinement_log = data
            else:
                session.refinement_log = []
    else:
        session.refinement_log = []

    # Load distilled context (if exists)
    distilled_file = os.path.join(session_dir, "refinement_distilled.txt")
    if os.path.exists(distilled_file):
        with open(distilled_file, 'r', encoding='utf-8') as f:
            # Skip header lines, read actual content
            content = f.read()
            # Extract content after the header
            if "="*80 in content:
                parts = content.split("="*80)
                if len(parts) >= 2:
                    session.distilled_context = parts[-1].strip()
                else:
                    session.distilled_context = content
            else:
                session.distilled_context = content
    else:
        session.distilled_context = ""

    session.research_findings = {}
    session.full_context = ""

    print_status("LOADED", f"Resumed session: {session.query}")
    print_status("STATE", f"Current state: {session.state}")

    if session.distilled_context:
        print_status("CONTEXT", f"Loaded {len(session.distilled_context)} characters of distilled refinement context")

    # Check if research episodes need to be retroactively committed
    needs_initial_commit = not session.initial_episode_id and os.path.exists(os.path.join(session_dir, "narrative.txt"))
    needs_deep_commits = session.deep_research_count > len(session.deep_episode_ids)

    if needs_initial_commit or needs_deep_commits:
        print_status("MIGRATION", "Detected research from before multi-episode feature...")
        print("This session has research that wasn't committed to graph yet.")
        print("I can retroactively commit the research episodes now, or skip graph writes.")

        commit_old_research = input("\nCommit old research to graph? (yes/no): ").strip().lower()

        if commit_old_research in ['yes', 'y']:
            asyncio.run(retroactive_commit_research(session, session_dir))
        else:
            print_status("SKIPPED", "Old research won't be committed to graph")

    return session


async def retroactive_commit_research(session: ResearchSession, session_dir: str):
    """Retroactively commit research episodes from old session"""
    import json

    print_status("COMMITTING", "Writing research episodes to graph...")

    # Commit initial research if needed
    if not session.initial_episode_id:
        narrative_file = os.path.join(session_dir, "narrative.txt")
        if os.path.exists(narrative_file):
            with open(narrative_file, 'r', encoding='utf-8') as f:
                narrative = f.read()

            # Load worker results
            worker_results = {}
            initial_dir = os.path.join(session_dir, "initial_research")
            for filename in ['academic_researcher.txt', 'industry_intelligence.txt', 'tool_analyzer.txt']:
                filepath = os.path.join(initial_dir, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        worker_results[filename.replace('.txt', '')] = f.read()

            # Load critical analysis
            critical_file = os.path.join(initial_dir, "critical_analysis.txt")
            critical_analysis = ""
            if os.path.exists(critical_file):
                with open(critical_file, 'r', encoding='utf-8') as f:
                    critical_analysis = f.read()

            # Use original_query field (not current query which may be overwritten by deep research)
            # For old sessions without original_query, try to infer or prompt
            if not session.original_query or session.original_query == session.query:
                # Query was lost - try to infer from narrative or prompt user
                print("\n" + "="*80)
                print("MIGRATION NOTE: Original research query not found in session metadata.")
                print("This happens with old sessions from before the multi-episode feature.")
                print("="*80)
                print(f"\nCurrent query in session: {session.query[:200]}...")
                print("\nThis looks like a deep research query (verbose/structured).")
                user_original = input("\nWhat was the ORIGINAL research query? (e.g., 'arthur ai based on out nyc'): ").strip()
                if user_original:
                    session.original_query = user_original
                    print(f"[MIGRATION] Using original query: {user_original}")
                else:
                    print("[MIGRATION] No original query provided, using current query")
                    session.original_query = session.query

            # Temporarily set correct query for episode commit
            old_query = session.query
            session.query = session.original_query

            result = await commit_research_episode(
                session=session,
                research_type="initial",
                narrative=narrative,
                worker_results=worker_results,
                critical_analysis=critical_analysis
            )

            session.query = old_query

            if result and result.get("status") == "success":
                session.initial_episode_id = result.get("episode_name", "")
                print_status("SUCCESS", f"Initial research episode: {session.initial_episode_id}")

    # Commit deep research episodes if needed
    for i in range(1, session.deep_research_count + 1):
        if i > len(session.deep_episode_ids):
            deep_dirs = [d for d in os.listdir(session_dir) if d.startswith(f"deep_research_{i}_")]
            if deep_dirs:
                deep_dir = os.path.join(session_dir, deep_dirs[0])

                # Load deep research files
                worker_results = {}
                for filename in ['academic_researcher.txt', 'industry_intelligence.txt', 'tool_analyzer.txt']:
                    filepath = os.path.join(deep_dir, filename)
                    if os.path.exists(filepath):
                        with open(filepath, 'r', encoding='utf-8') as f:
                            worker_results[filename.replace('.txt', '')] = f.read()

                critical_file = os.path.join(deep_dir, "critical_analysis.txt")
                critical_analysis = ""
                if os.path.exists(critical_file):
                    with open(critical_file, 'r', encoding='utf-8') as f:
                        critical_analysis = f.read()

                # Extract topic from directory name and clean it up
                raw_topic = deep_dirs[0].replace(f"deep_research_{i}_", "").replace("_", " ")

                # Check if topic looks like extraction metadata rather than clean topic
                topic = raw_topic
                looks_verbose = (
                    len(raw_topic.split()) > 8 or
                    "based on" in raw_topic.lower() or
                    "they want" in raw_topic.lower() or
                    "conversation" in raw_topic.lower()
                )

                if looks_verbose:
                    # For migration: prompt user for clean topic
                    print(f"\n[MIGRATION] Deep research {i} has verbose topic: '{raw_topic[:80]}...'")
                    clean_topic = input("Enter a clean topic name (e.g., 'ICP signals for downmarket'): ").strip()
                    if clean_topic:
                        topic = clean_topic
                        print(f"[MIGRATION] Using clean topic: {topic}")

                old_query = session.query
                session.query = topic

                result = await commit_research_episode(
                    session=session,
                    research_type="deep",
                    narrative=f"Deep research on: {topic}",
                    worker_results=worker_results,
                    critical_analysis=critical_analysis,
                    parent_episode_id=session.initial_episode_id
                )

                session.query = old_query

                if result and result.get("status") == "success":
                    episode_id = result.get("episode_name", "")
                    session.deep_episode_ids.append(episode_id)
                    print_status("SUCCESS", f"Deep research {i} episode: {episode_id}")

    print_status("COMPLETE", f"Committed {1 + len(session.deep_episode_ids)} research episodes")


def main():
    """Main conversational loop"""
    import argparse

    parser = argparse.ArgumentParser(description="Helldiver Research Agent")
    parser.add_argument('--refine', type=str, help='Resume existing session from folder path')
    args = parser.parse_args()

    print_header("Welcome to Helldiver Research Agent")

    session = None

    # Load existing session if --refine provided
    if args.refine:
        try:
            session = load_existing_session(args.refine)
            # Force to refinement state
            session.state = "REFINEMENT"
        except Exception as e:
            print_status("ERROR", str(e))
            return

    while True:
        if session is None or session.state == "TASKING":
            session = ResearchSession()
            next_state = tasking_conversation(session)
            session.state = next_state

        elif session.state == "RESEARCH":
            next_state = run_research_phase(session)
            session.state = next_state

        elif session.state == "REFINEMENT":
            next_state = refinement_conversation(session)
            session.state = next_state

        elif session.state == "COMMIT":
            next_state = commit_to_graph_phase(session)
            session.state = next_state

        elif session.state == "NEW_SESSION":
            print("\nStarting new research session...\n")
            session = None
            continue

        elif session.state == "COMPLETE":
            print_status("COMPLETE", f"Session saved to: {session.session_dir}")
            break

        else:
            print(f"Unknown state: {session.state}")
            break


if __name__ == "__main__":
    main()
