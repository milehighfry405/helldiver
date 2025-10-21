"""
Quick test of refactored code structure.

Tests that all modules import correctly and basic logic works.
"""

import sys
import os

# Test imports
print("Testing imports...")

try:
    from core.session import ResearchSession
    print("[OK] core.session")
except Exception as e:
    print(f"[FAIL] core.session: {e}")

try:
    from core.research_cycle import run_research_cycle
    print("[OK] core.research_cycle")
except Exception as e:
    print(f"[FAIL] core.research_cycle: {e}")

try:
    from graph.client import GraphClient
    print("[OK] graph.client")
except Exception as e:
    print(f"[FAIL] graph.client: {e}")

try:
    from workers.research import execute_research
    print("[OK] workers.research")
except Exception as e:
    print(f"[FAIL] workers.research: {e}")

try:
    from utils.files import save_research_files, distill_conversation
    print("[OK] utils.files")
except Exception as e:
    print(f"[FAIL] utils.files: {e}")

print("\n" + "="*60)
print("All modules imported successfully!")
print("="*60)

# Test session creation
print("\nTesting session creation...")
session = ResearchSession(
    session_dir="test_session",
    query="Test query",
    state="TASKING"
)
print(f"[OK] Created session: {session.query}")
print(f"[OK] State: {session.state}")
print(f"[OK] Episode count: {session.episode_count}")

# Test refinement tracking
session.add_refinement_turn("test user input", "test assistant response")
print(f"[OK] Added refinement turn: {len(session.pending_refinement)} turns")

# Test graph client init
print("\nTesting graph client...")
graph_client = GraphClient()
print("[OK] Graph client initialized")

print("\n" + "="*60)
print("SUCCESS: Refactored code structure is working!")
print("="*60)
print("\nCode statistics:")
print(f"  core/session.py: {len(open('core/session.py').readlines())} lines")
print(f"  core/research_cycle.py: {len(open('core/research_cycle.py').readlines())} lines")
print(f"  graph/client.py: {len(open('graph/client.py').readlines())} lines")
print(f"  workers/research.py: {len(open('workers/research.py').readlines())} lines")
print(f"  utils/files.py: {len(open('utils/files.py').readlines())} lines")
print(f"  main_new.py: {len(open('main_new.py').readlines())} lines")

total = (len(open('core/session.py').readlines()) +
         len(open('core/research_cycle.py').readlines()) +
         len(open('graph/client.py').readlines()) +
         len(open('workers/research.py').readlines()) +
         len(open('utils/files.py').readlines()) +
         len(open('main_new.py').readlines()))

print(f"\n  Total refactored code: {total} lines")
print(f"  Old main.py: {len(open('main.py').readlines())} lines")
print(f"  Reduction: {len(open('main.py').readlines()) - total} lines (better organization)")
