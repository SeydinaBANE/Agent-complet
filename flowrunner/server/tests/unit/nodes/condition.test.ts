import { describe, expect, it } from "vitest";
import { executeConditionNode } from "../../../src/nodes/condition.js";

const node = (operator: string, value: unknown) => ({
  id: "n1",
  type: "condition",
  data: { field: "score", operator, value },
});

describe("condition node", () => {
  it("eq — matches equal value", async () => {
    const result = await executeConditionNode(node("eq", 42), { score: 42 }, "r1");
    expect(result["n1_result"]).toBe(true);
  });

  it("eq — does not match different value", async () => {
    const result = await executeConditionNode(node("eq", 42), { score: 99 }, "r1");
    expect(result["n1_result"]).toBe(false);
  });

  it("gt — score > threshold", async () => {
    const result = await executeConditionNode(node("gt", 10), { score: 20 }, "r1");
    expect(result["n1_result"]).toBe(true);
  });

  it("lt — score < threshold", async () => {
    const result = await executeConditionNode(node("lt", 100), { score: 50 }, "r1");
    expect(result["n1_result"]).toBe(true);
  });

  it("contains — substring match", async () => {
    const result = await executeConditionNode(
      { id: "n1", type: "condition", data: { field: "text", operator: "contains", value: "hello" } },
      { text: "say hello world" },
      "r1",
    );
    expect(result["n1_result"]).toBe(true);
  });

  it("exists — present field", async () => {
    const result = await executeConditionNode(node("exists", null), { score: 0 }, "r1");
    expect(result["n1_result"]).toBe(true);
  });

  it("exists — missing field", async () => {
    const result = await executeConditionNode(node("exists", null), {}, "r1");
    expect(result["n1_result"]).toBe(false);
  });

  it("preserves existing context keys", async () => {
    const result = await executeConditionNode(node("eq", 1), { score: 1, other: "kept" }, "r1");
    expect(result["other"]).toBe("kept");
  });
});
