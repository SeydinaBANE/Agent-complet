import type { FastifyReply, FastifyRequest } from "fastify";
import crypto from "crypto";
import { env } from "../config.js";

/** Paths that are exempt from API key authentication. */
const HEALTH_PATHS = ["/health", "/ready"];

/**
 * Constant-time string comparison to prevent timing attacks.
 *
 * @param a - First string.
 * @param b - Second string.
 * @returns True if the strings are equal (same length and content).
 */
function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b));
}

/**
 * Fastify preHandler hook that validates the X-API-Key header.
 *
 * Skips validation for health check paths (/health, /ready).
 * Returns 401 with a structured error if the key is missing or invalid.
 *
 * @param request - The incoming Fastify request.
 * @param reply - The Fastify reply object.
 */
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
