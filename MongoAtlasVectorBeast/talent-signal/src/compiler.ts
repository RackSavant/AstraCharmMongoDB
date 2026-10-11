import type { WorkflowGraph, CompiledPlan, CompiledStage, WorkflowNode } from "./types";

/**
 * Validates a workflow graph structure for completeness, required configs, and edge connections.
 */
export function validate(graph: WorkflowGraph): string[] {
  const errors: string[] = [];

  if (!graph.id) errors.push("Workflow graph missing id.");
  if (!graph.nodes || graph.nodes.length === 0) errors.push("Workflow graph must contain at least one node.");

  const nodeIds = new Set(graph.nodes.map((n) => n.id));

  for (const edge of graph.edges || []) {
    if (!nodeIds.has(edge.source)) errors.push(`Edge ${edge.id} references missing source node ${edge.source}.`);
    if (!nodeIds.has(edge.target)) errors.push(`Edge ${edge.id} references missing target node ${edge.target}.`);
  }

  for (const node of graph.nodes) {
    if (node.type === "dataSource" && !node.config.collection) {
      errors.push(`Node ${node.id} (dataSource) requires 'collection' in config.`);
    }
    if (node.type === "vectorSearch" && (!node.config.index || !node.config.field)) {
      errors.push(`Node ${node.id} (vectorSearch) requires 'index' and 'field' in config.`);
    }
    if (node.type === "atlasNativeEmbedding" && !node.config.index) {
      errors.push(`Node ${node.id} (atlasNativeEmbedding) requires 'index' in config.`);
    }
    if (node.type === "mongoDbAiEmbedding" && !node.config.index) {
      errors.push(`Node ${node.id} (mongoDbAiEmbedding) requires 'index' in config.`);
    }
    if (node.type === "filter" && (!node.config.field || !node.config.op)) {
      errors.push(`Node ${node.id} (filter) requires 'field' and 'op' in config.`);
    }
    if (node.type === "rerank" && (!node.config.provider || !node.config.model)) {
      errors.push(`Node ${node.id} (rerank) requires 'provider' and 'model' in config.`);
    }
    if (node.type === "llmAgent" && (!node.config.provider || !node.config.model)) {
      errors.push(`Node ${node.id} (llmAgent) requires 'provider' and 'model' in config.`);
    }
  }

  return errors;
}

function getTopologicalOrder(graph: WorkflowGraph): WorkflowNode[] {
  const inDegree: Record<string, number> = {};
  const adj: Record<string, string[]> = {};
  const nodeMap = new Map<string, WorkflowNode>();

  for (const node of graph.nodes) {
    nodeMap.set(node.id, node);
    inDegree[node.id] = 0;
    adj[node.id] = [];
  }

  for (const edge of graph.edges) {
    if (adj[edge.source]) {
      adj[edge.source].push(edge.target);
      inDegree[edge.target] = (inDegree[edge.target] || 0) + 1;
    }
  }

  const queue: string[] = [];
  for (const nodeId in inDegree) {
    if (inDegree[nodeId] === 0) queue.push(nodeId);
  }

  const sortedNodes: WorkflowNode[] = [];
  while (queue.length > 0) {
    const currId = queue.shift()!;
    const currNode = nodeMap.get(currId);
    if (currNode) sortedNodes.push(currNode);

    for (const neighborId of adj[currId] || []) {
      inDegree[neighborId]--;
      if (inDegree[neighborId] === 0) {
        queue.push(neighborId);
      }
    }
  }

  return sortedNodes.length === graph.nodes.length ? sortedNodes : graph.nodes;
}

export function compile(graph: WorkflowGraph): CompiledPlan {
  const sortedNodes = getTopologicalOrder(graph);
  const pipeline: Record<string, any>[] = [];
  const rerankStages: CompiledStage[] = [];
  const llmStages: CompiledStage[] = [];
  const executionOrder: string[] = [];
  let atlasEmbeddingMode: "native_atlas" | "mongodb_ai_voyage" | "external_vector" = "external_vector";

  for (const node of sortedNodes) {
    executionOrder.push(`${node.id} (${node.type})`);

    if (node.type === "mongoDbAiEmbedding") {
      atlasEmbeddingMode = "mongodb_ai_voyage";
      const stage = {
        $vectorSearch: {
          index: node.config.index,
          path: node.config.field || "review_embedding",
          queryText: node.config.queryText || "{{user_prompt}}",
          numCandidates: (node.config.limit || 20) * 5,
          limit: node.config.limit || 20,
          embeddingEndpoint: "https://ai.mongodb.com/v1/embeddings",
          model: "voyage-4-large"
        },
      };
      pipeline.push(stage);
    } else if (node.type === "atlasNativeEmbedding") {
      atlasEmbeddingMode = "native_atlas";
      const stage = {
        $vectorSearch: {
          index: node.config.index,
          path: node.config.field || "review_embedding",
          queryText: node.config.queryText || "{{user_prompt}}",
          numCandidates: (node.config.limit || 20) * 5,
          limit: node.config.limit || 20,
          embeddingModel: "atlas-automated-vectorizer"
        },
      };
      pipeline.push(stage);
    } else if (node.type === "vectorSearch") {
      const stage = {
        $vectorSearch: {
          index: node.config.index,
          path: node.config.field || node.config.path || "embedding",
          queryVector: "[DYNAMIC_EMBEDDING_VECTOR]",
          numCandidates: (node.config.limit || 10) * 5,
          limit: node.config.limit || 10,
        },
      };
      pipeline.push(stage);
    } else if (node.type === "filter") {
      const mongoOp = node.config.op === "eq" ? "$eq" : `$${node.config.op}`;
      const stage = {
        $match: {
          [node.config.field!]: { [mongoOp]: node.config.value },
        },
      };
      pipeline.push(stage);
    } else if (node.type === "rerank") {
      rerankStages.push({
        stageType: "rerank",
        stageName: node.id,
        rerankConfig: {
          provider: node.config.provider || "voyage",
          model: node.config.model || "voyage-rerank-2",
          topK: node.config.topK || node.config.limit || 5
        },
        details: {
          id: node.id,
          provider: node.config.provider || "voyage",
          model: node.config.model || "voyage-rerank-2",
          targetField: "relevance_score"
        }
      });
    } else if (node.type === "llmAgent") {
      llmStages.push({
        stageType: "llmAgent",
        stageName: node.id,
        llmConfig: {
          provider: node.config.provider!,
          model: node.config.model!,
          promptTemplate: node.config.promptTemplate || "",
          outputField: node.config.outputField || "output",
        },
        details: {
          id: node.id,
          provider: node.config.provider,
          model: node.config.model,
        },
      });
    }
  }

  return {
    workflowId: graph.id,
    workflowName: graph.name,
    pipeline,
    rerankStages,
    llmStages,
    executionOrder,
    atlasEmbeddingMode
  };
}
