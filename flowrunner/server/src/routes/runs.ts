import type { FastifyInstance } from "fastify";

import { sql } from "../db.js";

export async function runRoutes(app: FastifyInstance): Promise<void> {
  app.get("/runs", async (request) => {
    const {
      cursor,
      limit = "20",
      status,
    } = request.query as { cursor?: string; limit?: string; status?: string };
    const take = Math.min(Number(limit) || 20, 100);

    const baseQuery = cursor
      ? status
        ? sql`
            SELECT r.id, r.workflow_id, r.status, r.started_at, r.finished_at, r.created_at
            FROM runs r
            WHERE r.status = ${status}
              AND r.created_at < (SELECT created_at FROM runs WHERE id = ${cursor})
            ORDER BY r.created_at DESC LIMIT ${take}`
        : sql`
            SELECT r.id, r.workflow_id, r.status, r.started_at, r.finished_at, r.created_at
            FROM runs r
            WHERE r.created_at < (SELECT created_at FROM runs WHERE id = ${cursor})
            ORDER BY r.created_at DESC LIMIT ${take}`
      : status
        ? sql`
            SELECT r.id, r.workflow_id, r.status, r.started_at, r.finished_at, r.created_at
            FROM runs r
            WHERE r.status = ${status}
            ORDER BY r.created_at DESC LIMIT ${take}`
        : sql`
            SELECT r.id, r.workflow_id, r.status, r.started_at, r.finished_at, r.created_at
            FROM runs r
            ORDER BY r.created_at DESC LIMIT ${take}`;

    const rows = await baseQuery;
    const nextCursor = rows.length === take ? String(rows[rows.length - 1]!.id) : null;
    return { data: rows, next_cursor: nextCursor };
  });

  app.get<{ Params: { id: string } }>("/runs/:id", async (request, reply) => {
    const [run] = await sql`
      SELECT r.*, w.name AS workflow_name
      FROM runs r
      JOIN workflows w ON w.id = r.workflow_id
      WHERE r.id = ${request.params.id}`;

    if (!run) {
      reply.status(404);
      return { error: "not_found", detail: "Run not found" };
    }
    return run;
  });

  app.get<{ Params: { id: string } }>("/runs/:id/logs", async (request, reply) => {
    const [run] = await sql`SELECT id FROM runs WHERE id = ${request.params.id}`;
    if (!run) {
      reply.status(404);
      return { error: "not_found", detail: "Run not found" };
    }

    const steps = await sql`
      SELECT id, node_id, node_type, input, output, error, duration_ms, created_at
      FROM run_steps
      WHERE run_id = ${request.params.id}
      ORDER BY created_at ASC`;

    return { run_id: request.params.id, steps };
  });
}
