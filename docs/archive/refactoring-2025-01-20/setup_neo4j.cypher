// Neo4j Setup Script for Helldiver + Graphiti
// Run this in Neo4j Browser (http://localhost:7474) or via cypher-shell

// Create fulltext index for node_name_and_summary
// This is required by Graphiti for entity search
CREATE FULLTEXT INDEX node_name_and_summary IF NOT EXISTS
FOR (n:Entity)
ON EACH [n.name, n.summary];

// Create fulltext index for edge_name_and_fact
// This is required by Graphiti for relationship search
CREATE FULLTEXT INDEX edge_name_and_fact IF NOT EXISTS
FOR ()-[r:RELATES_TO]-()
ON EACH [r.name, r.fact];

// Verify the indexes were created
SHOW INDEXES;

// Expected output should include:
// 1. name: "node_name_and_summary"
//    type: "FULLTEXT"
//    entityType: "NODE"
//    labelsOrTypes: ["Entity"]
//    properties: ["name", "summary"]
//
// 2. name: "edge_name_and_fact"
//    type: "FULLTEXT"
//    entityType: "RELATIONSHIP"
//    labelsOrTypes: ["RELATES_TO"]
//    properties: ["name", "fact"]
