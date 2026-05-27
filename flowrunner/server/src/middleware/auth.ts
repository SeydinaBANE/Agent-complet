import type { FastifyReply, FastifyRequest } from "fastify";
import { env } from "../config.js";

export async function requireApiKey(
  request: FastifyRequest,
  reply: FastifyReply,
): Promise<void> {
  const HEALTH_PATHS = ["/health", "/ready", "/documentation", "/documentation/json"];
  if (HEALTH_PATHS.some((p) => request.url.startsWith(p))) return;

  const key = request.headers["x-api-key"];
  if (typeof key !== "string" || key !== env.FLOWRUNNER_API_KEY) {
    reply.status(401).send({ error: "unauthorized", detail: "Invalid API key" });
  }
}
