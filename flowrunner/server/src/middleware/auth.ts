import type { FastifyReply, FastifyRequest } from "fastify";
import crypto from "crypto";
import { env } from "../config.js";

const HEALTH_PATHS = ["/health", "/ready"];

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b));
}

export async function requireApiKey(
  request: FastifyRequest,
  reply: FastifyReply,
): Promise<void> {
  if (HEALTH_PATHS.includes(request.url)) return;

  const key = request.headers["x-api-key"];
  if (typeof key !== "string" || !timingSafeEqual(key, env.FLOWRUNNER_API_KEY)) {
    reply.status(401).send({ error: "unauthorized", detail: "Invalid API key" });
  }
}
