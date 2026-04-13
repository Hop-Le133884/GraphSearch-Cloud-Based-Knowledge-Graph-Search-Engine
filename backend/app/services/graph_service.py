import os
from neo4j import GraphDatabase
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# -- Neo4j connection

def get_neo4j_driver():
    return GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
    )

# -- Langchain NL -> Cypher
CYPHER_PROMPT = PromptTemplate(
    input_variables = ["question"],
    template="""
You are an expert at conerting natural language questions into Neo4j Cypher queries.

The graph schema is:
- Nodes: (:Person {{name, bio, birthday, place_of_birth, pagerank_score}})
        (:Movie  {{title, released, tagline, revenue, bio, pagerank_score}})
        (:Genre  {{name}})
        (:Company {{name, country}})   

- Relationships:
    (:Person)-[:ACTED_IN {{role}}]->(:Movie)
    (:Person)-[:DIRECTED]->(:Movie)
    (:Movie)-[:GENRE_OF]->(:Genre)
    (:Movie)-[:PRODUCED_BY]->(:Company)

Rules:
1. Return ONLY the Cypher query, no explanation, no markdown, no backticks.
2. Always LIMIT results to 20.
3. Always ORDER BY pagerank_score DESC when available.
4. Embed values directly as string literals, never use Cypher parameters like $value. 
    Example: WHERE toLower(m.title) CONTAINS toLower("inception")
5. For person searches return: name, bio, pagerank_score
6. For movie searches return: title, released, bio, pagerank_score
7. Never use APOC procedures.

Question: {question}

Cypher query:
"""
)

def nl_to_cypher(question: str) -> str:
    """Convert a natural language question to a cypher query using gpt-40-mini."""
    llm = ChatOpenAI(
        model = "gpt-4o-mini",
        temperature=0, # deterministic output - same question = same Cypher
        api_key=os.environ["OPENAI_API_KEY"]
    )
    chain = CYPHER_PROMPT | llm | StrOutputParser()
    cypher = chain.invoke({"question": question})
    return cypher.strip()

# Execute Cypher
def execute_cypher(cypher: str) -> list[dict]:
    """
    Run a Cypher query against Neo4j and return results as a list of dicts.
    Each row is converted from Neo4j Record to a plain Python dict
    so Flask can serialize it to JSON.
    """
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            result = session.run(cypher)
            rows = []
            for record in result:
                row = {}
                for key in record.keys():
                    value = record[key]
                    # Neo4j Node objects aren't JSON-serializable — extract properties
                    if hasattr(value, "_properties"):
                        row[key] = dict(value._properties)
                    else:
                        row[key] = value
                rows.append(row)
            return rows
    finally:
        driver.close()

# Main search function
def search(question: str) -> dict:
    """
    Full pipeline: natural language → Cypher → Neo4j → results.
    Returns a dict with the cypher query and results list.
    """
    if not question or not question.strip():
        return {"error": "Empty query", "results": []}
    
    cypher = nl_to_cypher(question)
    results = execute_cypher(cypher)

    return {
        "query":   question,
        "cypher":  cypher,      # needed for debug
        "results": results,
        "count":   len(results)
    }
