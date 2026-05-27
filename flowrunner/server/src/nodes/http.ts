import type { WorkflowContext, WorkflowNode } from "../types.js";

export async function executeHttpNode(
  node: WorkflowNode,
  ctx: WorkflowContext,
  _runId: string,
): Promise<WorkflowContext> {
  const { url, method = "GET", headers = {}, body } = node.data as {
    url: string;
    method?: string;
    headers?: Record<string, string>;
    body?: unknown;
  };

  const response = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json", ...headers },
    body: body ? JSON.stringify(body) : undefined,
  });

  const responseBody = await response.text();
  let parsedBody: unknown = responseBody;
  try {
    parsedBody = JSON.parse(responseBody);
  } catch {
    // keep as string
  }

  return {
    ...ctx,
    [`${node.id}_status`]: response.status,
    [`${node.id}_body`]: parsedBody,
  };
}
