import type { FastifyInstance } from "fastify";
import { z } from "zod";

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
    const { cursor, limit = 20 } = request.query as { cursor?: string; limit?: number };
    // TODO: fetch from DB with cursor pagination
    return { data: [], next_cursor: null };
  });

  app.post("/workflows", async (request, reply) => {
    const body = WorkflowSchema.parse(request.body);
    // TODO: insert into DB
    reply.status(201);
    return { id: crypto.randomUUID(), ...body, created_at: new Date().toISOString() };
  });

  app.put<{ Params: { id: string } }>("/workflows/:id", async (request) => {
    const body = WorkflowSchema.partial().parse(request.body);
    // TODO: update in DB
    return { id: request.params.id, ...body };
  });

  app.delete<{ Params: { id: string } }>("/workflows/:id", async (_request, reply) => {
    // TODO: delete from DB
    reply.status(204);
  });

  app.post<{ Params: { id: string } }>("/workflows/:id/trigger", async (request, reply) => {
    const runId = crypto.randomUUID();
    // TODO: enqueue BullMQ job
    app.log.info({ workflowId: request.params.id, runId }, "workflow_triggered");
    reply.status(202);
    return { run_id: runId, status: "pending" };
  });
}
