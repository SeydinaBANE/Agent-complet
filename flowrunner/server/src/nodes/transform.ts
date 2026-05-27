import type { WorkflowContext, WorkflowNode } from "../types.js";

function interpolate(template: string, ctx: WorkflowContext): string {
  return template.replace(/\{\{(\w+)\}\}/g, (_, key) => {
    const val = ctx[key];
    return val !== undefined ? String(val) : `{{${key}}}`;
  });
}

export async function executeTransformNode(
  node: WorkflowNode,
  ctx: WorkflowContext,
  _runId: string,
): Promise<WorkflowContext> {
  const { mappings } = node.data as {
    mappings: Array<{ output_key: string; template: string }>;
  };

  const result: WorkflowContext = { ...ctx };
  for (const { output_key, template } of mappings) {
    result[output_key] = interpolate(template, ctx);
  }
  return result;
}
