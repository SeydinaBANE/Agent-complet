import type { WorkflowContext, WorkflowNode } from "../types.js";

type Operator = "eq" | "neq" | "gt" | "lt" | "contains" | "exists";

function evaluate(value: unknown, operator: Operator, expected: unknown): boolean {
  switch (operator) {
    case "eq": return value === expected;
    case "neq": return value !== expected;
    case "gt": return typeof value === "number" && typeof expected === "number" && value > expected;
    case "lt": return typeof value === "number" && typeof expected === "number" && value < expected;
    case "contains": return typeof value === "string" && typeof expected === "string" && value.includes(expected);
    case "exists": return value !== undefined && value !== null;
    default: return false;
  }
}

export async function executeConditionNode(
  node: WorkflowNode,
  ctx: WorkflowContext,
  _runId: string,
): Promise<WorkflowContext> {
  const { field, operator, value } = node.data as {
    field: string;
    operator: Operator;
    value: unknown;
  };

  const fieldValue = ctx[field];
  const result = evaluate(fieldValue, operator, value);

  return { ...ctx, [`${node.id}_result`]: result };
}
