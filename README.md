# Helldiver Research Agent

Multi-agent research system with context engineering and human-in-the-loop refinement.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` file:
```
ANTHROPIC_API_KEY=your_key_here
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
OPENAI_API_KEY=your_openai_key
MODEL_NAME=gpt-4o-mini
```

### 3. Run Research
```bash
# Start new research
python helldiver_agent.py

# Interactive refinement (after research completes)
python helldiver_agent.py --refine

# Test Graphiti integration
python helldiver_agent.py --test-graphiti
```

## Features

- **Multi-Agent Research**: 4 specialized workers (Academic, Industry, Tool, Critical Analyst)
- **Batch API**: 50% cost savings, no rate limits
- **Prompt Caching**: 90% cost savings on refinement questions
- **Context Engineering**: User mental models weighted higher than raw research
- **Session-Based**: Each research creates isolated session with full audit trail
- **Wave Function Collapse**: Explore tangents, eventually converge to synthesis
- **Knowledge Graph**: Persist findings to Graphiti/Neo4j

## Session Structure

```
context/
└── session_arthur_ai_20250111_143022/
    ├── session.json
    ├── initial_research/
    │   ├── academic_researcher.txt
    │   ├── industry_intelligence.txt
    │   ├── tool_analyzer.txt
    │   └── critical_analysis.txt
    ├── refinement_context.txt (WEIGHTED HIGHER)
    └── deep_research_{topic}/
```

## Documentation

See [docs/ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md) for detailed architecture.

## Utilities

```bash
# Kill zombie Python processes (during debugging)
python scripts/kill_agents.py
```
