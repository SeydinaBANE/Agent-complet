import type { FastifyInstance } from "fastify";

export async function runRoutes(app: FastifyInstance): Promise<void> {
  app.get("/runs", async (request) => {
    const { cursor, limit = 20, status } = request.query as {
      cursor?: string;
      limit?: number;
      status?: string;
    };
    // TODO: fetch from DB with cursor pagination
    return { data: [], next_cursor: null };
  });

  app.get<{ Params: { id: string } }>("/runs/:id", async (request, reply) => {
    // TODO: fetch run from DB
    reply.status(404);
    return { error: "not_found", detail: "Run not found" };
  });

  app.get<{ Params: { id: string } }>("/runs/:id/logs", async (request, reply) => {
    // TODO: fetch run_steps from DB
    reply.status(404);
    return { error: "not_found", detail: "Run not found" };
  });
}
