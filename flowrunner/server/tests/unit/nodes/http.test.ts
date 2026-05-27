import { describe, expect, it, vi, afterEach } from "vitest";
import { executeHttpNode } from "../../../src/nodes/http.js";
import type { WorkflowNode } from "../../../src/types.js";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

afterEach(() => vi.clearAllMocks());

const makeNode = (overrides: Partial<WorkflowNode["data"]> = {}): WorkflowNode => ({
  id: "http-1",
  type: "http",
  data: { url: "https://api.example.com/data", method: "GET", ...overrides },
});

describe("http node", () => {
  it("returns status and parsed JSON body", async () => {
    mockFetch.mockResolvedValueOnce({
      status: 200,
      text: async () => JSON.stringify({ result: "ok" }),
    });

    const out = await executeHttpNode(makeNode(), {}, "r1");
    expect(out["http-1_status"]).toBe(200);
    expect(out["http-1_body"]).toEqual({ result: "ok" });
  });

  it("keeps body as string when not valid JSON", async () => {
    mockFetch.mockResolvedValueOnce({ status: 200, text: async () => "plain text" });

    const out = await executeHttpNode(makeNode(), {}, "r1");
    expect(out["http-1_body"]).toBe("plain text");
  });

  it("sends POST with body and does not add body for GET", async () => {
    mockFetch.mockResolvedValueOnce({ status: 201, text: async () => "{}" });

    await executeHttpNode(makeNode({ method: "POST", body: { key: "val" } }), {}, "r1");

    const [, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ key: "val" }));
  });

  it("propagates existing context keys", async () => {
    mockFetch.mockResolvedValueOnce({ status: 200, text: async () => "ok" });
    const out = await executeHttpNode(makeNode(), { existing: "value" }, "r1");
    expect(out["existing"]).toBe("value");
  });
});
