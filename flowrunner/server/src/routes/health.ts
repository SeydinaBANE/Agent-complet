import type { FastifyInstance } from "fastify";
import { sql } from "../db.js";
import Redis from "ioredis";
import { env } from "../config.js";

export async function healthRoutes(app: FastifyInstance): Promise<void> {
  app.get("/health", async () => ({ status: "ok" }));

  app.get("/ready", async (_request, reply) => {
    const checks: Record<string, string> = {};
    let healthy = true;

    try {
      await sql`SELECT 1`;
      checks.db = "ok";
    } catch {
      checks.db = "error";
      healthy = false;
    }

    let redis: Redis | null = null;
    try {
      redis = new Redis(env.REDIS_URL);
      const pong = await redis.ping();
      checks.redis = pong === "PONG" ? "ok" : "error";
      if (checks.redis !== "ok") healthy = false;
    } catch {
      checks.redis = "error";
      healthy = false;
    } finally {
      if (redis) redis.disconnect();
    }

    reply.status(healthy ? 200 : 503).send({ status: healthy ? "ok" : "degraded", ...checks });
  });
}
