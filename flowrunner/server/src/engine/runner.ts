import type { NodeResult, WorkflowContext, WorkflowNode } from "../types.js";
import { executeNode } from "./node-executor.js";

export interface RunResult {
  status: "completed" | "failed";
  context: WorkflowContext;
  steps: NodeResult[];
  error?: string;
}

export async function runWorkflow(
  nodes: WorkflowNode[],
  initialContext: WorkflowContext,
  runId: string,
): Promise<RunResult> {
  let context = { ...initialContext };
  const steps: NodeResult[] = [];

  for (const node of nodes) {
    const startedAt = Date.now();
    try {
      const output = await executeNode(node, context, runId);
      const step: NodeResult = {
        node_id: node.id,
        node_type: node.type,
        input: context,
        output,
        duration_ms: Date.now() - startedAt,
      };
      steps.push(step);
      context = { ...context, ...output };
    } catch (err) {
      const error = err instanceof Error ? err.message : String(err);
      steps.push({
        node_id: node.id,
        node_type: node.type,
        input: context,
        output: null,
        duration_ms: Date.now() - startedAt,
        error,
      });
      return { status: "failed", context, steps, error };
    }
  }

  return { status: "completed", context, steps };
}
