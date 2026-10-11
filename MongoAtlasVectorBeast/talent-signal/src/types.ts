export type NodeType =
  | "dataSource"
  | "vectorSearch"
  | "atlasNativeEmbedding"
  | "mongoDbAiEmbedding"
  | "filter"
  | "rerank"
  | "llmAgent"
  | "output";

export interface NodeConfig {
  collection?: string;
  index?: string;
  field?: string;
  path?: string;
  queryText?: string;
  embeddingEndpoint?: string;
  model?: string;
  limit?: number;
  topK?: number;
  provider?: string;
  apiKey?: string;
  op?: string;
  value?: any;
  promptTemplate?: string;
  outputField?: string;
  [key: string]: any;
}

export interface WorkflowNode {
  id: string;
  type: NodeType;
  position: { x: number; y: number };
  config: NodeConfig;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
}

export interface WorkflowGraph {
  id: string;
  name: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface CompiledStage {
  stageType: string;
  stageName: string;
  mongoStage?: Record<string, any>;
  embeddingConfig?: {
    endpoint: string;
    model: string;
  };
  rerankConfig?: {
    provider: string;
    model: string;
    topK: number;
  };
  llmConfig?: {
    provider: string;
    model: string;
    promptTemplate: string;
    outputField: string;
  };
  details: Record<string, any>;
}

export interface CompiledPlan {
  workflowId: string;
  workflowName: string;
  pipeline: Record<string, any>[];
  rerankStages: CompiledStage[];
  llmStages: CompiledStage[];
  executionOrder: string[];
  atlasEmbeddingMode: "native_atlas" | "mongodb_ai_voyage" | "external_vector";
}
