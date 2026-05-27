export type WorkflowContext = Record<string, unknown>;

export interface WorkflowNode {
  id: string;
  type: string;
  data: Record<string, unknown>;
}

export interface NodeResult {
  node_id: string;
  node_type: string;
  input: WorkflowContext;
  output: WorkflowContext | null;
  duration_ms: number;
  error?: string;
}
