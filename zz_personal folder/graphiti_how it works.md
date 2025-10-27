How Graphiti Custom Types Work (From the Maintainer's Perspective)
Custom Entity Types
Purpose: Let you define domain-specific entities with custom attributes that Graphiti should extract. How it works:
You define a Pydantic model for entities you expect to appear in your text:
class Company(BaseModel):
    """A company mentioned in text"""
    company_name: str  # required
    industry: Optional[str]  # optional
    stage: Optional[str]  # optional
Graphiti extracts entities from text using Named Entity Recognition:
Finds proper nouns: "Arthur.ai", "Google", "Microsoft"
Classifies them: Is this a Company? A Person? A Tool?
For each entity found, Graphiti extracts attributes:
Text: "Arthur.ai is a machine learning monitoring company in financial services"
Extracted: company_name="Arthur.ai", industry="financial services"
Creates node: (:Company {company_name: "Arthur.ai", industry: "financial services"})
Key point: Custom entity types are for things mentioned in the text - companies, people, products, etc. The LLM finds the entity name, then populates your custom fields from context.
Custom Edge Types
Purpose: Let you define domain-specific relationships with custom attributes. How it works (according to docs):
You define edge types between entity pairs:
class Uses(BaseModel):
    """One entity uses another"""
    usage_type: Optional[str]  # e.g., "core_product", "internal_tool"
    adoption_level: Optional[str]  # e.g., "pilot", "enterprise-wide"
You define edge_type_map to constrain which edges can exist:
edge_type_map = {
    ("Company", "Tool"): ["USES", "EVALUATES"],
    ("Company", "Company"): ["COMPETES_WITH", "PARTNERS_WITH"],
}
Graphiti extracts relationships from text:
Text: "Arthur.ai uses Kubernetes for their infrastructure"
Finds: Company (Arthur.ai) → Tool (Kubernetes)
Checks map: Can Company→Tool have USES edge? Yes!
Creates: (Arthur.ai)-[:USES {usage_type: "infrastructure"}]->(Kubernetes)
Key point: Edge types should be verbs describing how entities relate. Custom properties add context about the relationship.
What Graphiti Does NOT Do
Graphiti does not extract conceptual/abstract entities that are the structure of your text rather than things mentioned in it. Example of what DOESN'T work:
class ResearchFinding(BaseModel):
    """A finding from research"""
    finding_type: str
    confidence: float
Why it doesn't work:
Text: "Key finding: Arthur.ai has strong ML monitoring"
Graphiti looks for: What is "ResearchFinding"? Where is it mentioned?
There's no entity named "ResearchFinding" - the finding IS the sentence itself
Result: No extraction
This is by design - Graphiti extracts entities (nouns mentioned in text), not meta-information (your analysis of the text).
So What Actually Happened in Your PoC?
Entities ✅
Worked: Company nodes with industry attribute populated
Why: "Arthur.ai" is mentioned → NER finds it → custom attributes extract → works as designed
Edges ❌
Didn't work: No custom edge types created, only generic RELATES_TO
Why: This is the confusing part...
Let me check what the actual behavior is supposed to be by looking at what we observed vs what the docs claim... Actually, I need to be honest: I don't know exactly how edge_types is supposed to work because:
The docs say it should extract custom edge properties
Our PoC showed it didn't
The parameter exists in the API
But I haven't seen working examples
My honest answer as a maintainer would be: "Edge types are for defining valid relationship types between entities. The system will extract relationships as verb-based edges (USES, COMPETES_WITH) and if they match your edge_type_map, it uses your custom type. If not, falls back to RELATES_TO." But I'm not confident that's how it actually works, because our test didn't create custom edge types even though we provided them.
Does this help? Or does it reveal that I'm still mixing what the docs SAY vs what we OBSERVED?