"""
Knowledge Graph Ontology for Research Intelligence System

Defines entity types, edge types, and relationship rules for Graphiti extraction.

Built from ontology research 2.md specification.
Optimized for NER-based extraction with deliberate verbalization strategy.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# =============================================================================
# TIER 1: CONCRETE DOMAIN ENTITIES
# =============================================================================

class Company(BaseModel):
    """Organization being researched or analyzed"""
    company_name: str = Field(description="Full company name")
    industry: Optional[str] = Field(None, description="Primary industry vertical")
    stage: Optional[str] = Field(None, description="e.g., Series A, Public, Bootstrap")
    employee_count: Optional[int] = Field(None, description="Team size")
    founded_year: Optional[int] = Field(None, description="Year established")


class Tool(BaseModel):
    """Software, platform, or technology being analyzed"""
    tool_name: str = Field(description="Product/tool name")
    category: Optional[str] = Field(None, description="e.g., Clay, Outreach, Analytics")
    pricing_model: Optional[str] = Field(None, description="Freemium, Enterprise, Usage-based")
    key_capabilities: Optional[str] = Field(None, description="Core features extracted")


class Person(BaseModel):
    """Individual mentioned in research"""
    person_name: str = Field(description="Full name")
    role: Optional[str] = Field(None, description="Job title or function")
    company: Optional[str] = Field(None, description="Current organization")
    expertise_area: Optional[str] = Field(None, description="Domain specialization")


# =============================================================================
# TIER 2: STRATEGIC CONCEPT ENTITIES (Requires Deliberate Verbalization)
# =============================================================================

class ResearchObjective(BaseModel):
    """Named strategic question or goal being investigated"""
    objective_name: str = Field(description="Concise objective identifier")
    objective_type: Optional[str] = Field(
        None,
        description="market_analysis, competitive_research, tool_evaluation, strategic_planning"
    )
    priority: Optional[str] = Field(None, description="critical, high, medium, low")
    status: Optional[str] = Field(None, description="active, completed, parked")


class Hypothesis(BaseModel):
    """Specific testable assumption or strategic premise"""
    hypothesis_name: str = Field(description="Short hypothesis identifier")
    statement: Optional[str] = Field(None, description="Full hypothesis statement")
    confidence: Optional[float] = Field(None, description="Belief strength 0-1")
    validation_status: Optional[str] = Field(
        None,
        description="unvalidated, partially_validated, validated, refuted"
    )


class Methodology(BaseModel):
    """Specific approach, workflow, or playbook"""
    methodology_name: str = Field(description="Method identifier")
    method_type: Optional[str] = Field(
        None,
        description="workflow, framework, analysis_technique"
    )
    maturity: Optional[str] = Field(None, description="experimental, proven, best_practice")
    implementation_complexity: Optional[str] = Field(None, description="low, medium, high")


class Finding(BaseModel):
    """Discrete insight or discovery from research"""
    finding_name: str = Field(description="Short finding identifier")
    finding_type: Optional[str] = Field(
        None,
        description="insight, data_point, pattern, risk"
    )
    novelty: Optional[str] = Field(None, description="novel, confirming, contradicting")
    actionability: Optional[str] = Field(
        None,
        description="immediate, strategic, informational"
    )
    confidence: Optional[float] = Field(None, description="Reliability score 0-1")


# =============================================================================
# TIER 3: EXECUTION AND OUTCOME ENTITIES
# =============================================================================

class Implementation(BaseModel):
    """Concrete execution attempt of a methodology"""
    implementation_name: str = Field(description="Execution identifier with date/context")
    outcome: Optional[str] = Field(None, description="success, partial_success, failure")
    metrics_achieved: Optional[str] = Field(None, description="Quantitative results")
    lessons_learned: Optional[str] = Field(None, description="Key takeaways")
    executed_date: Optional[datetime] = Field(None, description="When implementation occurred")


class Market(BaseModel):
    """Market segment, vertical, or opportunity space"""
    market_name: str = Field(description="Market identifier")
    size: Optional[str] = Field(None, description="TAM/market size estimate")
    growth_rate: Optional[str] = Field(None, description="Annual growth estimate")
    maturity: Optional[str] = Field(None, description="emerging, growth, mature, declining")


class Capability(BaseModel):
    """Organizational or product capability"""
    capability_name: str = Field(description="Capability identifier")
    capability_type: Optional[str] = Field(
        None,
        description="technical, operational, strategic"
    )
    maturity_level: Optional[str] = Field(None, description="nascent, developing, established")


# =============================================================================
# EDGE TYPES (Relationship Classifications)
# =============================================================================

# NOTE: Custom edge properties don't extract in practice (attributes dict stays empty).
# All properties must be captured in the relationship's 'fact' text.
# These models define the semantic relationship types that will appear in r.name property.

class Investigates(BaseModel):
    """ResearchObjective → Company/Tool/Market - Links research objectives to their targets"""
    pass  # Properties go in r.fact text: "with high priority", "started Jan 2025"


class Tests(BaseModel):
    """Methodology/Implementation → Hypothesis - Links execution to hypotheses being validated"""
    pass  # Properties go in r.fact text: "supports with strong evidence", "refutes conclusively"


class Implements(BaseModel):
    """Implementation → Methodology - Links concrete executions to abstract methods"""
    pass  # Properties go in r.fact text: "high fidelity implementation", "adapted for context"


class Reveals(BaseModel):
    """Finding → Company/Tool/Market/Capability - Finding uncovers information about entity"""
    pass  # Properties go in r.fact text: "reveals capability", "high impact discovery"


class Supports(BaseModel):
    """Finding → Hypothesis - Finding provides evidence for hypothesis"""
    pass  # Properties go in r.fact text: "with high confidence", "strong quantitative evidence"


class Contradicts(BaseModel):
    """Finding → Finding/Hypothesis - Identifies conflicting information"""
    pass  # Properties go in r.fact text: "unresolved conflict", "resolved via additional research"


class Enables(BaseModel):
    """Tool/Capability → Methodology - Tool/capability makes methodology possible"""
    pass  # Properties go in r.fact text: "required for execution", "enhances but not critical"


class Requires(BaseModel):
    """Methodology → Capability/Tool - Methodology depends on specific capabilities"""
    pass  # Properties go in r.fact text: "critical requirement", "optional enhancement"


class Informs(BaseModel):
    """Finding → Implementation - Research finding guides implementation decisions"""
    pass  # Properties go in r.fact text: "high priority action", "strategic guidance"


class Targets(BaseModel):
    """Company → Market - Company targets specific market segment"""
    pass  # Properties go in r.fact text: "primary target market", "expansion opportunity"


class CompetesWith(BaseModel):
    """Company → Company - Competitive relationship between companies"""
    pass  # Properties go in r.fact text: "direct competition", "indirect overlap", "emerging threat"


# =============================================================================
# CONFIGURATION EXPORTS
# =============================================================================

# Entity type dictionary for Graphiti
ENTITY_TYPES = {
    # Tier 1: Concrete domain entities
    "Company": Company,
    "Tool": Tool,
    "Person": Person,

    # Tier 2: Strategic concept entities (require deliberate verbalization)
    "ResearchObjective": ResearchObjective,
    "Hypothesis": Hypothesis,
    "Methodology": Methodology,
    "Finding": Finding,

    # Tier 3: Execution and outcome entities
    "Implementation": Implementation,
    "Market": Market,
    "Capability": Capability,
}

# Edge type dictionary for Graphiti
EDGE_TYPES = {
    # Structural relationships
    "INVESTIGATES": Investigates,
    "TESTS": Tests,
    "IMPLEMENTS": Implements,

    # Discovery relationships
    "REVEALS": Reveals,
    "SUPPORTS": Supports,
    "CONTRADICTS": Contradicts,

    # Execution relationships
    "ENABLES": Enables,
    "REQUIRES": Requires,
    "INFORMS": Informs,

    # Competition and market relationships
    "TARGETS": Targets,
    "COMPETES_WITH": CompetesWith,
}

# Edge type map: Defines which entity pairs can have which relationships
# Format: (source_entity_type, target_entity_type): [allowed_edge_types]
EDGE_TYPE_MAP = {
    # ResearchObjective relationships
    ("ResearchObjective", "Company"): ["INVESTIGATES"],
    ("ResearchObjective", "Tool"): ["INVESTIGATES"],
    ("ResearchObjective", "Market"): ["INVESTIGATES"],
    ("ResearchObjective", "Hypothesis"): ["INVESTIGATES"],

    # Hypothesis relationships
    ("Hypothesis", "Finding"): ["TESTS"],  # Hypothesis tested by findings
    ("Finding", "Hypothesis"): ["SUPPORTS", "CONTRADICTS"],  # Findings support/contradict hypotheses

    # Methodology relationships
    ("Methodology", "Hypothesis"): ["TESTS"],  # Methodology tests hypothesis
    ("Methodology", "Tool"): ["REQUIRES"],  # Methodology requires tools
    ("Methodology", "Capability"): ["REQUIRES"],  # Methodology requires capabilities
    ("Tool", "Methodology"): ["ENABLES"],  # Tool enables methodology
    ("Capability", "Methodology"): ["ENABLES"],  # Capability enables methodology

    # Implementation relationships
    ("Implementation", "Methodology"): ["IMPLEMENTS"],  # Implementation executes methodology
    ("Implementation", "Hypothesis"): ["TESTS"],  # Implementation tests hypothesis

    # Finding relationships
    ("Finding", "Company"): ["REVEALS"],  # Finding reveals info about company
    ("Finding", "Tool"): ["REVEALS"],  # Finding reveals info about tool
    ("Finding", "Market"): ["REVEALS"],  # Finding reveals info about market
    ("Finding", "Capability"): ["REVEALS"],  # Finding reveals capability
    ("Finding", "Implementation"): ["INFORMS"],  # Finding informs implementation
    ("Finding", "Finding"): ["CONTRADICTS"],  # Findings can contradict each other

    # Company relationships
    ("Company", "Market"): ["TARGETS"],  # Company targets market
    ("Company", "Company"): ["COMPETES_WITH"],  # Companies compete
    ("Company", "Tool"): ["REQUIRES", "ENABLES"],  # Company uses/provides tools

    # Tool relationships
    ("Tool", "Capability"): ["ENABLES"],  # Tool enables capability
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_entity_count() -> int:
    """Return total number of entity types defined"""
    return len(ENTITY_TYPES)


def get_edge_count() -> int:
    """Return total number of edge types defined"""
    return len(EDGE_TYPES)


def get_relationship_rules() -> dict:
    """Return human-readable relationship rules"""
    rules = {}
    for (source, target), edges in EDGE_TYPE_MAP.items():
        rule_key = f"{source} → {target}"
        rules[rule_key] = edges
    return rules


if __name__ == "__main__":
    # Quick validation
    print(f"Ontology Configuration")
    print(f"=" * 80)
    print(f"Entity Types: {get_entity_count()}")
    print(f"Edge Types: {get_edge_count()}")
    print(f"Relationship Rules: {len(EDGE_TYPE_MAP)}")
    print()
    print("Entity Types:")
    for name in ENTITY_TYPES.keys():
        print(f"  - {name}")
    print()
    print("Edge Types:")
    for name in EDGE_TYPES.keys():
        print(f"  - {name}")
