"""
File I/O utilities for research episodes.

Each research episode creates 5 files:
1. academic_researcher.txt
2. industry_intelligence.txt
3. tool_analyzer.txt
4. critical_analysis.txt
5. refinement_distilled.txt (the conversation context that led to this research)

Plus narrative.txt (synthesized summary) and refinement_context.txt (full conversation audit trail).
"""

import os
from typing import Dict, List, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Anthropic client for distillation
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def save_research_files(
    research_dir: str,
    worker_results: Dict[str, str],
    critical_analysis: str,
    refinement_full: str,
    refinement_distilled: str
):
    """
    Save all research files to episode directory.

    Args:
        research_dir: Path to episode folder (e.g., context/Session/Episode_Name/)
        worker_results: Dict with keys: academic_researcher, industry_intelligence, tool_analyzer
        critical_analysis: Critical analyst output
        refinement_full: Full conversation transcript (audit trail)
        refinement_distilled: Distilled context (what goes to graph)

    Creates:
        - 3 worker files
        - critical_analysis.txt
        - refinement_context.txt (full conversation)
        - refinement_distilled.txt (distilled for graph)

    Why 2 refinement files:
    - refinement_context.txt = full transcript for audit/debugging
    - refinement_distilled.txt = signal extracted for graph commit (Episode 5)
    """
    os.makedirs(research_dir, exist_ok=True)

    # Save 3 worker outputs
    for worker_name, content in worker_results.items():
        filename = f"{worker_name}.txt"
        filepath = os.path.join(research_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    # Save critical analysis
    with open(os.path.join(research_dir, "critical_analysis.txt"), 'w', encoding='utf-8') as f:
        f.write(critical_analysis)

    # Save full refinement context (audit trail)
    with open(os.path.join(research_dir, "refinement_context.txt"), 'w', encoding='utf-8') as f:
        f.write("REFINEMENT CONTEXT - Full Conversation (Audit Trail)\n")
        f.write("="*80 + "\n")
        f.write("This is the full conversation that led to this research being executed.\n")
        f.write("For the distilled version (what goes to graph), see refinement_distilled.txt\n")
        f.write("="*80 + "\n\n")
        f.write(refinement_full)

    # Save distilled refinement (what goes to graph as Episode 5)
    with open(os.path.join(research_dir, "refinement_distilled.txt"), 'w', encoding='utf-8') as f:
        f.write("REFINEMENT CONTEXT - Distilled (Committed to Graph)\n")
        f.write("="*80 + "\n")
        f.write("This is the extracted gold/signal from the conversation.\n")
        f.write("This version is committed to the knowledge graph as Episode 5.\n")
        f.write("WEIGHTING: This context is weighted HIGHER than raw research findings.\n")
        f.write("="*80 + "\n\n")
        f.write(refinement_distilled)


def format_conversation_for_display(conversation: List[Dict]) -> str:
    """
    Format conversation log into human-readable text.

    Args:
        conversation: List of turns with user_input/assistant_response

    Returns:
        Formatted string for audit trail

    Why: Full conversation transcript is saved for debugging/audit.
    The distilled version goes to graph, but we keep original for reference.
    """
    output = []
    for i, turn in enumerate(conversation, 1):
        output.append(f"--- Turn {i} ---")
        output.append(f"USER: {turn.get('user_input', '')}")
        output.append(f"\nASSISTANT: {turn.get('assistant_response', '')}")
        output.append("\n" + "-"*80 + "\n")
    return "\n".join(output)


def convert_tasking_to_conversation(tasking_context: Dict) -> List[Dict]:
    """
    Convert tasking conversation history to standard format.

    Args:
        tasking_context: Dict with "conversation_history" key containing messages

    Returns:
        List of turns in standard format (user_input/assistant_response pairs)

    Why: Tasking phase uses Anthropic message format (role/content).
    Need to convert to our standard turn format for distillation.

    Handles both conversation orders:
    - User first: [user, assistant, user, assistant]
    - Assistant first: [assistant, user, assistant, user] ← happens in tasking clarification
    """
    conversation_history = tasking_context.get("conversation_history", [])
    turns = []
    pending_assistant = None

    for msg in conversation_history:
        role = msg.get("role", "")
        content = msg.get("content", "")

        if role == "assistant":
            # Store assistant message, pair with next user message
            pending_assistant = content

        elif role == "user":
            # Create turn: user message + any pending assistant message
            turns.append({
                "user_input": content,
                "assistant_response": pending_assistant or "",
                "timestamp": msg.get("timestamp", "")
            })
            pending_assistant = None

    return turns


def distill_conversation(conversation: List[Dict]) -> str:
    """
    Extract signal/gold from conversation using Sonnet 4.5.

    Args:
        conversation: List of turns (user_input/assistant_response format)

    Returns:
        Distilled context (mental models, key questions, constraints, priorities)

    Why this matters:
    - Raw conversation has noise (pleasantries, clarifications, tangents)
    - Graph needs SIGNAL: what mattered, what changed, what to remember
    - Distilled version becomes Episode 5 (weighted higher than research)

    What gets extracted:
    1. Mental models (how user frames the problem)
    2. Reframings (when/how user corrected direction)
    3. Constraints (explicit boundaries or requirements)
    4. Priorities (what matters most)
    5. Synthesis instructions (how to interpret research)

    Uses explicit entity names (not "they"/"it") for better graph extraction.
    """
    if not conversation:
        return "(No refinement conversation - research triggered immediately)"

    # Format conversation for distillation
    conversation_text = "\n\n".join([
        f"USER: {turn['user_input']}\n\nASSISTANT: {turn['assistant_response']}"
        for turn in conversation
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
- Avoid vague references - always name the thing

Format: Write 3-8 concise paragraphs that capture the essential context.
</instructions>

<conversation>
{conversation_text}
</conversation>"""

    # Use Sonnet 4.5 for distillation (fast, cheap, good at extraction)
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        temperature=0.3,  # Lower temp for more factual extraction
        messages=[{
            "role": "user",
            "content": distillation_prompt
        }]
    )

    distilled = ""
    for block in response.content:
        if block.type == "text":
            distilled += block.text

    return distilled.strip()


def load_research_files(research_dir: str) -> Dict[str, str]:
    """
    Load all research files from episode directory.

    Args:
        research_dir: Path to episode folder

    Returns:
        Dict with keys: academic_researcher, industry_intelligence, tool_analyzer,
                       critical_analysis, narrative, refinement_distilled

    Why: Used during migration to load old research and commit to graph.
    """
    files = {}

    # Load 3 workers
    for worker in ["academic_researcher", "industry_intelligence", "tool_analyzer"]:
        filepath = os.path.join(research_dir, f"{worker}.txt")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                files[worker] = f.read()

    # Load critical analysis
    critical_path = os.path.join(research_dir, "critical_analysis.txt")
    if os.path.exists(critical_path):
        with open(critical_path, 'r', encoding='utf-8') as f:
            files["critical_analysis"] = f.read()

    # Load narrative
    narrative_path = os.path.join(research_dir, "narrative.txt")
    if os.path.exists(narrative_path):
        with open(narrative_path, 'r', encoding='utf-8') as f:
            files["narrative"] = f.read()

    # Load refinement distilled
    distilled_path = os.path.join(research_dir, "refinement_distilled.txt")
    if os.path.exists(distilled_path):
        with open(distilled_path, 'r', encoding='utf-8') as f:
            files["refinement_distilled"] = f.read()

    return files
