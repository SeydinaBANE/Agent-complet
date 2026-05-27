import type { FastifyInstance } from "fastify";
import { z } from "zod";

import { sql } from "../db.js";
import { workflowQueue } from "../queue.js";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const j = (v: unknown) => sql.json(v as any);

const WorkflowSchema = z.object({
  name: z.string().min(1).max(255),
  graph: z.object({
    nodes: z.array(z.record(z.unknown())),
    edges: z.array(z.record(z.unknown())),
  }),
  active: z.boolean().default(true),
});

export async function workflowRoutes(app: FastifyInstance): Promise<void> {
  app.get("/workflows", async (request) => {
    const { cursor, limit = "20" } = request.query as { cursor?: string; limit?: string };
    const take = Math.min(Number(limit) || 20, 100);

    const rows = cursor
      ? await sql`
          SELECT id, name, active, created_at FROM workflows
          WHERE created_at < (SELECT created_at FROM workflows WHERE id = ${cursor})
          ORDER BY created_at DESC LIMIT ${take}`
      : await sql`
          SELECT id, name, active, created_at FROM workflows
          ORDER BY created_at DESC LIMIT ${take}`;

    const nextCursor = rows.length === take ? String(rows[rows.length - 1]!.id) : null;
    return { data: rows, next_cursor: nextCursor };
  });

  app.post("/workflows", async (request, reply) => {
    const body = WorkflowSchema.parse(request.body);
    const [row] = await sql`
      INSERT INTO workflows (name, graph, active)
      VALUES (${body.name}, ${j(body.graph)}, ${body.active})
      RETURNING *`;
    reply.status(201);
    return row;
  });

  app.put<{ Params: { id: string } }>("/workflows/:id", async (request, reply) => {
    const body = WorkflowSchema.partial().parse(request.body);
    const updates: Record<string, unknown> = {};
    if (body.name !== undefined) updates["name"] = body.name;
    if (body.graph !== undefined) updates["graph"] = body.graph;
    if (body.active !== undefined) updates["active"] = body.active;

    if (Object.keys(updates).length === 0) {
      reply.status(400);
      return { error: "no_fields", detail: "No updatable fields provided" };
    }

    const [row] = await sql`
      UPDATE workflows
      SET ${sql(updates)}
      WHERE id = ${request.params.id}
      RETURNING *`;

    if (!row) {
      reply.status(404);
      return { error: "not_found", detail: "Workflow not found" };
    }
    return row;
  });

  app.delete<{ Params: { id: string } }>("/workflows/:id", async (request, reply) => {
    const result = await sql`DELETE FROM workflows WHERE id = ${request.params.id}`;
    if (result.count === 0) {
      reply.status(404);
      return { error: "not_found", detail: "Workflow not found" };
    }
    reply.status(204);
  });

  app.post<{ Params: { id: string } }>("/workflows/:id/trigger", async (request, reply) => {
    const [workflow] = await sql`SELECT id FROM workflows WHERE id = ${request.params.id} AND active = true`;
    if (!workflow) {
      reply.status(404);
      return { error: "not_found", detail: "Workflow not found or inactive" };
    }

    const [run] = await sql`
      INSERT INTO runs (workflow_id, status)
      VALUES (${request.params.id}, 'pending')
      RETURNING id`;

    const runId = String(run!.id);

    await workflowQueue.add("run", {
      workflowId: request.params.id,
      runId,
      context: (request.body as Record<string, unknown> | null) ?? {},
    });

    app.log.info({ workflowId: request.params.id, runId }, "workflow_triggered");
    reply.status(202);
    return { run_id: runId, status: "pending" };
  });
}
