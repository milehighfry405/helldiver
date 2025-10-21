"""
Research workers using Anthropic Batch API.

COPIED DIRECTLY FROM OLD CODE - uses batch API for:
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
    """Create batch jobs for 3 specialist workers - COPIED FROM OLD CODE"""

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


def extract_batch_results(batch_id: str, research_dir: str) -> dict:
    """Extract results from completed batch and save to research directory - COPIED FROM OLD CODE"""
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
    """Run critical analyst to review worker findings - COPIED FROM OLD CODE"""

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

    # Save critical analysis to file
    critical_file = os.path.join(research_dir, "critical_analysis.txt")
    with open(critical_file, 'w', encoding='utf-8') as f:
        f.write(f"CRITICAL ANALYSIS\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write("="*80 + "\n\n")
        f.write(findings)

    return findings
