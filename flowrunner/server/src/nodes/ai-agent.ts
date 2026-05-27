import type { WorkflowContext, WorkflowNode } from "../types.js";
import { env } from "../config.js";

const POLL_INTERVAL_MS = 2000;
const POLL_TIMEOUT_MS = 120_000;

export async function executeAiAgentNode(
  node: WorkflowNode,
  ctx: WorkflowContext,
  runId: string,
): Promise<WorkflowContext> {
  const { goal_template, model, max_iterations = 5, budget_usd = 0.05 } = node.data as {
    goal_template: string;
    model?: string;
    max_iterations?: number;
    budget_usd?: number;
  };

  const goal = goal_template.replace(/\{\{(\w+)\}\}/g, (_, key) => {
    const val = ctx[key];
    return val !== undefined ? String(val) : `{{${key}}}`;
  });

  const startResponse = await fetch(`${env.AGENTCORE_ORIGIN}/api/v1/agents/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": env.AGENTCORE_API_KEY,
    },
    body: JSON.stringify({ goal, model, max_iterations, budget_usd }),
  });

  if (!startResponse.ok) {
    throw new Error(`AgentCore error: ${startResponse.status}`);
  }

  const { run_id } = (await startResponse.json()) as { run_id: string };

  // Poll until done
  const deadline = Date.now() + POLL_TIMEOUT_MS;
  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));

    const statusResponse = await fetch(`${env.AGENTCORE_ORIGIN}/api/v1/agents/${run_id}`, {
      headers: { "X-API-Key": env.AGENTCORE_API_KEY },
    });
    const status = (await statusResponse.json()) as { status: string; error?: string };

    if (status.status === "completed") {
      return { ...ctx, [`${node.id}_run_id`]: run_id, [`${node.id}_status`]: "completed" };
    }
    if (status.status === "failed" || status.status === "killed") {
      throw new Error(`AgentCore run ${run_id} ${status.status}: ${status.error ?? ""}`);
    }
  }

  throw new Error(`AgentCore run ${run_id} timed out after ${POLL_TIMEOUT_MS}ms`);
}
