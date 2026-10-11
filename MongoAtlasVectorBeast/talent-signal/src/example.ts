// Demonstrates: (1) compiling a workflow with Atlas Native Embedding & Voyage Rerank node,
// (2) what happens to the compiled output when a node is rewired (pre vs post filter),
// and (3) swapping an LLM Agent node's provider with no code change.

import { compile, validate } from "./compiler";
import type { WorkflowGraph } from "./types";

const baseWorkflow: WorkflowGraph = {
  id: "wf_demo",
  name: "Talent Signal — Atlas Native & Voyage Rerank Pipeline",
  nodes: [
    { id: "n1", type: "dataSource", position: { x: 0, y: 0 }, config: { collection: "employees" } },
    {
      id: "n2",
      type: "atlasNativeEmbedding",
      position: { x: 250, y: 0 },
      config: {
        index: "review_vector_index",
        field: "review_embedding",
        queryText: "Top engineering talent with cloud architecture expertise",
        limit: 20
      },
    },
    {
      id: "n3",
      type: "filter",
      position: { x: 500, y: 0 },
      config: { field: "department", op: "eq", value: "Platform Engineering" },
    },
    {
      id: "n4_rerank",
      type: "rerank",
      position: { x: 750, y: 0 },
      config: { provider: "voyage", model: "voyage-rerank-2", topK: 5 },
    },
    {
      id: "n5",
      type: "llmAgent",
      position: { x: 1000, y: 0 },
      config: {
        provider: "anthropic",
        model: "claude-sonnet-5",
        promptTemplate: "Summarize why these reranked employees stand out:\n{{documents}}",
        outputField: "summary",
      },
    },
    { id: "n6", type: "output", position: { x: 1250, y: 0 }, config: {} },
  ],
  edges: [
    { id: "e1", source: "n1", target: "n2" },
    { id: "e2", source: "n2", target: "n3" },
    { id: "e3", source: "n3", target: "n4_rerank" },
    { id: "e4", source: "n4_rerank", target: "n5" },
    { id: "e5", source: "n5", target: "n6" },
  ],
};

console.log("=== Base workflow: validate ===");
console.log(validate(baseWorkflow)); // expect []

console.log("\n=== Base workflow: compiled plan ===");
console.log(JSON.stringify(compile(baseWorkflow), (k, v) => (k === "run" ? "[fn]" : v), 2));

// --- Scenario: user drags the Filter node BEFORE the Atlas Native Embedding node ---
const rewired: WorkflowGraph = {
  ...baseWorkflow,
  edges: [
    { id: "e1", source: "n1", target: "n3" }, // dataSource -> filter (pre-filter)
    { id: "e2", source: "n3", target: "n2" }, // filter -> atlasNativeEmbedding
    { id: "e3", source: "n2", target: "n4_rerank" },
    { id: "e4", source: "n4_rerank", target: "n5" },
    { id: "e5", source: "n5", target: "n6" },
  ],
};

console.log("\n=== Rewired workflow (filter moved before native vector search): compiled plan ===");
console.log(JSON.stringify(compile(rewired), (k, v) => (k === "run" ? "[fn]" : v), 2));

// --- Scenario: swap the LLM Agent's provider from Anthropic to OpenAI ---
const swappedProvider: WorkflowGraph = {
  ...baseWorkflow,
  nodes: baseWorkflow.nodes.map((n) =>
    n.id === "n5" ? { ...n, config: { ...n.config, provider: "openai", model: "gpt-4o" } } : n
  ),
};

console.log("\n=== Provider swapped (anthropic -> openai): validate ===");
console.log(validate(swappedProvider)); // still []
