import type { FastifyInstance } from "fastify";

export async function healthRoutes(app: FastifyInstance): Promise<void> {
  app.get("/health", async () => ({ status: "ok" }));

  app.get("/ready", async () => {
    // TODO: check DB and Redis connectivity
    return { status: "ok", db: "ok", redis: "ok" };
  });
}
