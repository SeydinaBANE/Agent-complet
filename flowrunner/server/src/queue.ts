import { Queue, Worker } from "bullmq";

import { env } from "./config.js";
import { sql } from "./db.js";
import { runWorkflow } from "./engine/runner.js";
import type { WorkflowNode } from "./types.js";

const redisUrl = new URL(env.REDIS_URL);
const connection = {
  host: redisUrl.hostname,
  port: Number(redisUrl.port) || 6379,
  ...(redisUrl.password ? { password: redisUrl.password } : {}),
};

export const workflowQueue = new Queue("workflow-runs", { connection });

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const j = (v: unknown) => sql.json(v as any);

export function startWorker(): Worker {
  return new Worker(
    "workflow-runs",
    async (job) => {
      const { workflowId, runId, context } = job.data as {
        workflowId: string;
        runId: string;
        context: Record<string, unknown>;
      };

      const rows = await sql`SELECT graph FROM workflows WHERE id = ${workflowId}`;
      if (rows.length === 0) throw new Error(`Workflow ${workflowId} not found`);

      const graph = rows[0]!.graph as { nodes: WorkflowNode[] };
      const nodes: WorkflowNode[] = graph.nodes ?? [];

      await sql`UPDATE runs SET status = 'running', started_at = NOW() WHERE id = ${runId}`;

      const result = await runWorkflow(nodes, context ?? {}, runId);

      for (const step of result.steps) {
        await sql`
          INSERT INTO run_steps (id, run_id, node_id, node_type, input, output, error, duration_ms, created_at)
          VALUES (
            gen_random_uuid(), ${runId}, ${step.node_id}, ${step.node_type},
            ${j(step.input)},
            ${step.output !== null ? j(step.output) : null},
            ${step.error ?? null}, ${step.duration_ms}, NOW()
          )`;
      }

      await sql`
        UPDATE runs
        SET status = ${result.status},
            finished_at = NOW(),
            context = ${j(result.context)},
            error = ${result.error ?? null}
        WHERE id = ${runId}`;

      return { status: result.status };
    },
    { connection },
  );
}
