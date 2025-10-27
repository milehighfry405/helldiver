"""
Research workers using Anthropic Batch API.

TWO-STAGE ARCHITECTURE:
Stage 1: Research LLMs (unrestricted deep thinking, natural prose)
Stage 2: Structuring LLM (transform to graph-optimized format)

Uses batch API for:
- 50% cost savings
- Progress polling every 30s
- Optimal performance per Anthropic docs
"""

import os
import time
from datetime import datetime
from typing import Dict, Tuple
from anthropic import Anthropic
from dotenv import load_dotenv
from workers.prompts import (
    ACADEMIC_RESEARCHER_PROMPT,
    INDUSTRY_ANALYST_PROMPT,
    TOOL_ANALYZER_PROMPT,
    STRUCTURING_PROMPT_TEMPLATE,
    CRITICAL_ANALYST_PROMPT,
)

# Load environment variables
load_dotenv()

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# Test mode flag (set by main.py)
TEST_MODE = False


def execute_research(query: str, tasking_summary: str, research_dir: str) -> Tuple[Dict[str, str], str]:
    """
    Execute full research cycle using batch API.

    Args:
        query: What to research
        tasking_summary: Context from tasking conversation
        research_dir: Where to save worker files

    Returns:
        (worker_results, critical_analysis)
        - worker_results: Dict with academic_researcher, industry_intelligence, tool_analyzer
        - critical_analysis: Critical analyst output

    Process:
        1. Create batch with 3 workers
        2. Poll with progress updates every 30s
        3. Extract results and save to files
        4. Run critical analyst
        5. Return all findings

    Why batch API:
    - 50% cost savings vs regular API
    - Can poll for progress
    - Optimal per Anthropic docs
    """
    print(f"[RESEARCH] Starting research on: {query}")
    print("[BATCH] Creating research batch...")

    # Create batch with 3 workers
    batch = create_worker_batch(query, tasking_summary)

    print(f"[SUBMITTED] Batch {batch.id}")
    print("[WORKERS] Academic | Industry | Tool")
    print()

    # Poll with progress updates every 30s
    start_time = time.time()
    update_interval = 30
    last_update = 0

    while True:
        batch_status = anthropic_client.messages.batches.retrieve(batch.id)

        if batch_status.processing_status == "ended":
            print("[COMPLETE] All workers finished!")
            break

        elapsed = int(time.time() - start_time)

        # Show progress every 30s (max 6 updates = 3 minutes)
        if elapsed - last_update >= update_interval and elapsed // update_interval <= 6:
            counts = batch_status.request_counts
            print(f"[PROGRESS] {elapsed}s elapsed - Processing: {counts.processing} | Complete: {counts.succeeded}")
            last_update = elapsed

        time.sleep(10)  # Poll every 10s

    print()

    # Extract results and save to files
    print("[EXTRACTING] Gathering findings from workers...")
    worker_results = extract_batch_results(batch.id, research_dir)

    # Run critical analyst
    print("[CRITICAL] Running critical analyst...")
    critical_analysis = run_critical_analyst(worker_results, query, tasking_summary, research_dir)

    return worker_results, critical_analysis


def create_worker_batch(research_query: str, tasking_context: str):
    """
    Create batch jobs for 3 specialist workers.

    Uses optimized prompts built with Anthropic best practices (2025):
    - XML tags for structure
    - Role-based prompting
    - Few-shot examples
    - Clear task decomposition
    """

    # Test mode: minimal research for fast testing
    if TEST_MODE:
        academic_prompt = "You are an academic researcher. Provide 2-3 key points about this topic."
        industry_prompt = "You are an industry analyst. Provide 2-3 key real-world insights."
        tool_prompt = "You are a tools researcher. Provide 2-3 key technical points."
        user_message = f"Research Query: {research_query}\n\nProvide brief, focused insights (2-3 points max)."
        model = "claude-haiku-4-5"
        max_tokens = 500
        tools = []  # No web search in test mode
    else:
        # Use elite optimized prompts from prompts.py
        academic_prompt = ACADEMIC_RESEARCHER_PROMPT
        industry_prompt = INDUSTRY_ANALYST_PROMPT
        tool_prompt = TOOL_ANALYZER_PROMPT

        user_message = f"""<research_query>
{research_query}
</research_query>

<tasking_context>
{tasking_context}
</tasking_context>

<instructions>
Conduct deep research using your specialized expertise. Use web_search extensively to find the highest-signal evidence.
</instructions>"""
        model = "claude-sonnet-4-5"
        max_tokens = 4000
        tools = [{"type": "web_search_20250305", "name": "web_search"}]

    batch = anthropic_client.messages.batches.create(
        requests=[
            {
                "custom_id": "academic_researcher",
                "params": {
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": 0.3,
                    "system": academic_prompt,
                    "tools": tools,
                    "messages": [{"role": "user", "content": user_message}]
                }
            },
            {
                "custom_id": "industry_intelligence",
                "params": {
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": 0.3,
                    "system": industry_prompt,
                    "tools": tools,
                    "messages": [{"role": "user", "content": user_message}]
                }
            },
            {
                "custom_id": "tool_analyzer",
                "params": {
                    "model": model,
                    "max_tokens": max_tokens,
                    "temperature": 0.3,
                    "system": tool_prompt,
                    "tools": tools,
                    "messages": [{"role": "user", "content": user_message}]
                }
            }
        ]
    )

    return batch


def structure_research_for_graph(raw_research: str, worker_type: str, research_dir: str) -> str:
    """
    Stage 2: Transform natural research into graph-optimized format.

    This runs AFTER research is complete, using a specialized structuring LLM
    to add entity naming and relationship markers without constraining research quality.

    Args:
        raw_research: Natural prose from Stage 1 research LLM
        worker_type: Worker name (academic_researcher, industry_intelligence, tool_analyzer)
        research_dir: Where to save structured output

    Returns:
        Structured research with entity markers and relationship declarations
    """

    # Use elite optimized structuring prompt (XML tags, examples, clear rules)
    structuring_prompt = STRUCTURING_PROMPT_TEMPLATE.format(
        worker_type=worker_type,
        raw_research=raw_research
    )

    # Use cheaper model for structured task (Haiku is excellent at following formats)
    response = anthropic_client.messages.create(
        model="claude-haiku-4-5",  # Cost-effective for structured transformation
        max_tokens=6000,  # Slightly longer to ensure no truncation
        temperature=0,  # Deterministic for formatting
        messages=[{"role": "user", "content": structuring_prompt}]
    )

    structured_output = ""
    for block in response.content:
        if block.type == "text":
            structured_output += block.text

    # Save structured version
    structured_file = os.path.join(research_dir, f"{worker_type}.txt")
    with open(structured_file, 'w', encoding='utf-8') as f:
        f.write(f"Worker: {worker_type}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Format: Graph-optimized (Stage 2 - structured from raw research)\n")
        f.write("="*80 + "\n\n")
        f.write(structured_output)

    return structured_output


def extract_batch_results(batch_id: str, research_dir: str) -> dict:
    """
    Extract results from completed batch and save to research directory.

    TWO-STAGE PROCESSING:
    Stage 1: Save raw natural research (what the research LLM produced)
    Stage 2: Transform into graph-optimized format (entity naming + relationships)

    This separation ensures research quality isn't constrained by formatting requirements.
    """
    results = {}

    for result in anthropic_client.messages.batches.results(batch_id):
        if result.result.type == "succeeded":
            custom_id = result.custom_id
            message = result.result.message

            findings = ""
            for block in message.content:
                if block.type == "text":
                    findings += block.text

            # STAGE 1: Save raw research (natural prose)
            raw_file = os.path.join(research_dir, f"{custom_id}_raw.txt")
            with open(raw_file, 'w', encoding='utf-8') as f:
                f.write(f"Worker: {custom_id}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Batch ID: {batch_id}\n")
                f.write(f"Format: Natural research (Stage 1 - before structuring)\n")
                f.write("="*80 + "\n\n")
                f.write(findings)

            # STAGE 2: Transform for graph extraction
            print(f"[STRUCTURING] {custom_id} for graph extraction...")
            structured_findings = structure_research_for_graph(findings, custom_id, research_dir)

            results[custom_id] = structured_findings  # Return structured version for graph

    return results


def run_critical_analyst(worker_results: dict, research_query: str, tasking_context: str, research_dir: str) -> str:
    """
    Run critical analyst to review worker findings.

    Uses optimized prompt with XML tags and clear evaluation criteria.
    """

    critical_message = f"""<research_query>
{research_query}
</research_query>

<tasking_context>
{tasking_context}
</tasking_context>

<academic_researcher_findings>
{worker_results.get('academic_researcher', 'No findings')}
</academic_researcher_findings>

<industry_intelligence_findings>
{worker_results.get('industry_intelligence', 'No findings')}
</industry_intelligence_findings>

<tool_analyzer_findings>
{worker_results.get('tool_analyzer', 'No findings')}
</tool_analyzer_findings>

<instructions>
Review all three workers' findings critically. Score relevance, filter noise, identify gaps, challenge weak evidence, and synthesize patterns.
</instructions>"""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        temperature=0.3,
        system=CRITICAL_ANALYST_PROMPT,
        messages=[{"role": "user", "content": critical_message}]
    )

    findings = ""
    for block in response.content:
        if block.type == "text":
            findings += block.text

    # Save critical analysis to file
    critical_file = os.path.join(research_dir, "critical_analysis.txt")
    with open(critical_file, 'w', encoding='utf-8') as f:
        f.write(f"CRITICAL ANALYSIS\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write("="*80 + "\n\n")
        f.write(findings)

    return findings
