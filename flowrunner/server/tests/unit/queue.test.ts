import { describe, expect, it, vi, beforeEach } from "vitest";

// Mock db and queue before importing the worker logic
vi.mock("../../src/db.js", () => ({
  sql: Object.assign(
    vi.fn((_parts: TemplateStringsArray, ..._args: unknown[]) => Promise.resolve([])),
    { json: (v: unknown) => v },
  ),
}));

vi.mock("../../src/engine/runner.js", () => ({
  runWorkflow: vi.fn(),
}));

vi.mock("bullmq", () => ({
  Queue: vi.fn().mockImplementation(() => ({ add: vi.fn() })),
  Worker: vi.fn().mockImplementation((_name: string, processor: (...args: unknown[]) => unknown) => ({
    _processor: processor,
    on: vi.fn(),
    close: vi.fn(),
  })),
}));

import { runWorkflow } from "../../src/engine/runner.js";
import { sql } from "../../src/db.js";

describe("queue worker processor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("runs workflow and updates run to completed", async () => {
    const mockWorkflow = { graph: { nodes: [{ id: "n1", type: "delay", data: { ms: 0 } }] } };
    const mockResult = {
      status: "completed" as const,
      context: { done: true },
      steps: [
        {
          node_id: "n1",
          node_type: "delay",
          input: {},
          output: { done: true },
          duration_ms: 5,
        },
      ],
    };

    const sqlMock = sql as unknown as ReturnType<typeof vi.fn>;
    sqlMock.mockResolvedValueOnce([mockWorkflow]); // SELECT graph
    sqlMock.mockResolvedValueOnce([]); // UPDATE running
    sqlMock.mockResolvedValueOnce([]); // INSERT step
    sqlMock.mockResolvedValueOnce([]); // UPDATE completed

    vi.mocked(runWorkflow).mockResolvedValueOnce(mockResult);

    // Import queue after mocks are in place
    const { startWorker } = await import("../../src/queue.js");
    const { Worker } = await import("bullmq");

    startWorker();

    const workerCtor = vi.mocked(Worker);
    expect(workerCtor).toHaveBeenCalled();
    const processor = workerCtor.mock.calls[0]![1] as (...args: unknown[]) => unknown;

    const result = await processor({ data: { workflowId: "wf-1", runId: "run-1", context: {} } });
    expect(result).toEqual({ status: "completed" });
    expect(runWorkflow).toHaveBeenCalledWith(mockWorkflow.graph.nodes, {}, "run-1");
  });

  it("throws when workflow not found", async () => {
    const sqlMock = sql as unknown as ReturnType<typeof vi.fn>;
    sqlMock.mockResolvedValueOnce([]); // SELECT graph → empty

    const { startWorker } = await import("../../src/queue.js");
    const { Worker } = await import("bullmq");

    startWorker();

    const processor = vi.mocked(Worker).mock.calls[0]![1] as (...args: unknown[]) => unknown;
    await expect(
      processor({ data: { workflowId: "missing", runId: "run-2", context: {} } }),
    ).rejects.toThrow("missing");
  });
});
