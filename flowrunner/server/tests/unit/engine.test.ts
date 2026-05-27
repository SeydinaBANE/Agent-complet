import { describe, expect, it } from "vitest";
import { runWorkflow } from "../../src/engine/runner.js";
import type { WorkflowNode } from "../../src/types.js";

describe("workflow runner", () => {
  it("completes an empty workflow", async () => {
    const result = await runWorkflow([], { input: "hello" }, "r1");
    expect(result.status).toBe("completed");
    expect(result.steps).toHaveLength(0);
  });

  it("propagates context between nodes", async () => {
    const nodes: WorkflowNode[] = [
      {
        id: "t1",
        type: "transform",
        data: { mappings: [{ output_key: "greeting", template: "Hello {{name}}!" }] },
      },
    ];
    const result = await runWorkflow(nodes, { name: "Alice" }, "r1");
    expect(result.status).toBe("completed");
    expect(result.context["greeting"]).toBe("Hello Alice!");
  });

  it("fails on unknown node type", async () => {
    const nodes: WorkflowNode[] = [{ id: "u1", type: "unknown-type", data: {} }];
    const result = await runWorkflow(nodes, {}, "r1");
    expect(result.status).toBe("failed");
    expect(result.error).toContain("unknown-type");
  });

  it("records step duration", async () => {
    const nodes: WorkflowNode[] = [{ id: "d1", type: "delay", data: { ms: 10 } }];
    const result = await runWorkflow(nodes, {}, "r1");
    expect(result.status).toBe("completed");
    expect(result.steps[0]?.duration_ms).toBeGreaterThanOrEqual(10);
  });
});
