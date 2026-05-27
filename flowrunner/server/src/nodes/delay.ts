import type { WorkflowContext, WorkflowNode } from "../types.js";

const MAX_DELAY_MS = 30_000;

export async function executeDelayNode(
  node: WorkflowNode,
  ctx: WorkflowContext,
  _runId: string,
): Promise<WorkflowContext> {
  const { ms } = node.data as { ms: number };
  const delay = Math.min(ms, MAX_DELAY_MS);
  await new Promise((resolve) => setTimeout(resolve, delay));
  return ctx;
}
