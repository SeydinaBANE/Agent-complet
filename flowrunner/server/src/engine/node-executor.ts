import type { WorkflowContext, WorkflowNode } from "../types.js";
import { executeHttpNode } from "../nodes/http.js";
import { executeConditionNode } from "../nodes/condition.js";
import { executeTransformNode } from "../nodes/transform.js";
import { executeDelayNode } from "../nodes/delay.js";
import { executeAiAgentNode } from "../nodes/ai-agent.js";

type NodeExecutor = (node: WorkflowNode, ctx: WorkflowContext, runId: string) => Promise<WorkflowContext>;

const EXECUTORS: Record<string, NodeExecutor> = {
  http: executeHttpNode,
  condition: executeConditionNode,
  transform: executeTransformNode,
  delay: executeDelayNode,
  "ai-agent": executeAiAgentNode,
};

export async function executeNode(
  node: WorkflowNode,
  ctx: WorkflowContext,
  runId: string,
): Promise<WorkflowContext> {
  const executor = EXECUTORS[node.type];
  if (!executor) {
    throw new Error(`Unknown node type: ${node.type}`);
  }
  return executor(node, ctx, runId);
}
