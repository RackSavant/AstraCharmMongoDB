// -----------------------------------------------------------------------
// Vector Beast — Canvas Topology Pipeline Compiler MVP Demo
// Runs locally with standard Node.js (no npm install required)
//
// Demonstrates how graph canvas topology translates directly into executable
// MongoDB Atlas aggregation pipelines, showing pre-filter vs post-filter re-ordering,
// Voyage AI reranking, MongoDB AI Voyage embeddings, and zero-code LLM provider swapping.
//
// Run with: node demo.js
// -----------------------------------------------------------------------

function compile(graph) {
  const nodesById = Object.fromEntries(graph.nodes.map((n) => [n.id, n]));

  // Find the start node (no incoming edges)
  const hasIncoming = new Set(graph.edges.map((e) => e.target));
  const startId = graph.nodes.map((n) => n.id).find((id) => !hasIncoming.has(id));

  // Walk the chain in directed edge order
  const order = [startId];
  let current = startId;
  while (current) {
    const next = graph.edges.find((e) => e.source === current);
    if (!next) break;
    order.push(next.target);
    current = next.target;
  }

  const stages = [];
  const rerankStages = [];
  const llmStages = [];
  let collection = null;
  let embeddingMode = "external_vector";

  for (const nodeId of order) {
    const node = nodesById[nodeId];
    if (!node) continue;

    if (node.type === "dataSource") {
      collection = node.config.collection;
    }

    if (node.type === "filter") {
      stages.push({
        $match: { [node.config.field]: { $eq: node.config.value } },
      });
    }

    if (node.type === "vectorSearch") {
      stages.push({
        $vectorSearch: {
          index: node.config.index,
          path: node.config.field,
          queryVector: "[DYNAMIC_EMBEDDING_VECTOR]",
          numCandidates: node.config.numCandidates || 100,
          limit: node.config.limit || 10,
        },
      });
    }

    if (node.type === "atlasNativeEmbedding" || node.type === "mongoDbAiEmbedding") {
      embeddingMode = node.type === "mongoDbAiEmbedding" ? "mongodb_ai_voyage" : "native_atlas";
      stages.push({
        $vectorSearch: {
          index: node.config.index,
          path: node.config.field || "review_embedding",
          queryText: node.config.queryText || "{{user_prompt}}",
          numCandidates: (node.config.limit || 10) * 5,
          limit: node.config.limit || 10,
          embeddingEndpoint: "https://ai.mongodb.com/v1/embeddings",
          model: "voyage-4-large"
        },
      });
    }

    if (node.type === "rerank") {
      rerankStages.push({
        stageType: "rerank",
        stageName: node.id,
        provider: node.config.provider || "voyage",
        model: node.config.model || "voyage-rerank-2",
        topK: node.config.topK || 5
      });
    }

    if (node.type === "llmAgent") {
      llmStages.push({
        stageType: "llmAgent",
        stageName: node.id,
        provider: node.config.provider || "gemini",
        model: node.config.model || "gemini-2.5-flash",
        promptTemplate: node.config.promptTemplate || "",
        outputField: node.config.outputField || "output"
      });
    }
  }

  return {
    collection,
    embeddingMode,
    pipeline: stages,
    rerankStages,
    llmStages,
    executionOrder: order.map(id => `${id} (${nodesById[id]?.type})`)
  };
}

// ---- Scenario 1: The 3-node graph: Data Source -> Vector Search -> Filter (Post-Filter) ----

const graphDefault = {
  id: "graph_post_filter",
  nodes: [
    { id: "n1", type: "dataSource", config: { collection: "employees" } },
    {
      id: "n2",
      type: "vectorSearch",
      config: { index: "expertise_vector_index", field: "expertise_embedding", limit: 10 },
    },
    { id: "n3", type: "filter", config: { field: "department", value: "Engineering" } },
  ],
  edges: [
    { source: "n1", target: "n2" },
    { source: "n2", target: "n3" },
  ],
};

// ---- Scenario 2: Same 3 nodes, user dragged Filter BEFORE Vector Search (Pre-Filter) ----

const graphRearranged = {
  id: "graph_pre_filter",
  nodes: graphDefault.nodes,
  edges: [
    { source: "n1", target: "n3" },
    { source: "n3", target: "target" in graphDefault.edges[0] ? "n2" : "n2" },
  ],
};

// ---- Scenario 3: Full Vector Beast Pipeline (Atlas Native Embedding + Pre-Filter + Voyage Rerank + LLM) ----

const graphFullVectorBeast = {
  id: "graph_full_beast",
  nodes: [
    { id: "n1", type: "dataSource", config: { collection: "employees" } },
    { id: "n2_filter", type: "filter", config: { field: "department", value: "Platform Engineering" } },
    {
      id: "n3_native_emb",
      type: "mongoDbAiEmbedding",
      config: {
        index: "review_vector_index",
        field: "review_embedding",
        queryText: "Top cloud software architects with distributed systems experience",
        limit: 20
      },
    },
    {
      id: "n4_rerank",
      type: "rerank",
      config: { provider: "voyage", model: "voyage-rerank-2", topK: 5 },
    },
    {
      id: "n5_llm",
      type: "llmAgent",
      config: {
        provider: "anthropic",
        model: "claude-sonnet-5",
        promptTemplate: "Summarize why these candidates are top matches:\n{{documents}}",
        outputField: "summary"
      },
    }
  ],
  edges: [
    { source: "n1", target: "n2_filter" },
    { source: "n2_filter", target: "n3_native_emb" },
    { source: "n3_native_emb", target: "n4_rerank" },
    { source: "n4_rerank", target: "n5_llm" }
  ]
};

// ---- Console Output Runner ----

console.log("=======================================================================");
console.log("🐉 VECTOR BEAST — VISUAL TOPOLOGY COMPILER MVP DEMO");
console.log("=======================================================================\n");

console.log("=== Scenario A: Default Canvas Topology (Vector Search -> Filter) ===");
console.log(JSON.stringify(compile(graphDefault), null, 2));

console.log("\n=== Scenario B: Rewired Canvas Topology (User Dragged Filter BEFORE Vector Search) ===");
console.log(JSON.stringify(compile(graphRearranged), null, 2));

console.log("\n=== Scenario C: Full Vector Beast (MongoDB AI Voyage-4-Large + Pre-Filter + Voyage Rerank + Claude) ===");
console.log(JSON.stringify(compile(graphFullVectorBeast), null, 2));

console.log("\n-----------------------------------------------------------------------");
console.log("✅ SUMMARY:");
console.log("1. Same nodes. Same edge count.");
console.log("2. Moving ONE connection on the canvas rewrites the compiled MongoDB aggregation pipeline");
console.log("   from post-filtering to native pre-filtering ($match stage precedes $vectorSearch).");
console.log("3. Automatically incorporates MongoDB AI (voyage-4-large) and Voyage Rerank (voyage-rerank-2).");
console.log("-----------------------------------------------------------------------\n");
