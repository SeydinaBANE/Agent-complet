import Fastify from "fastify";
import cors from "@fastify/cors";
import rateLimit from "@fastify/rate-limit";
import swagger from "@fastify/swagger";
import swaggerUi from "@fastify/swagger-ui";
import crypto from "crypto";

import { env } from "./config.js";
import { sql } from "./db.js";
import { startWorker } from "./queue.js";
import { healthRoutes } from "./routes/health.js";
import { workflowRoutes } from "./routes/workflows.js";
import { runRoutes } from "./routes/runs.js";
import { requireApiKey } from "./middleware/auth.js";

const app = Fastify({ logger: { level: "info" } });

await app.register(cors, {
  origin: env.NODE_ENV === "production" ? env.FLOWRUNNER_ORIGIN : true,
  credentials: true,
});
await app.register(rateLimit, { max: 60, timeWindow: "1 minute" });

if (env.NODE_ENV !== "production") {
  await app.register(swagger, {
    openapi: {
      info: { title: "FlowRunner", version: "1.0.0" },
      components: {
        securitySchemes: {
          apiKey: { type: "apiKey", name: "x-api-key", in: "header" },
        },
      },
    },
  });
  await app.register(swaggerUi, { routePrefix: "/documentation" });
}

app.addHook("preHandler", async (request) => {
  const requestId = (request.headers["x-request-id"] as string) || crypto.randomUUID();
  request.id = requestId;
  request.log = request.log.child({ requestId });
});

app.addHook("preHandler", requireApiKey);

await app.register(healthRoutes);
await app.register(workflowRoutes, { prefix: "/api/v1" });
await app.register(runRoutes, { prefix: "/api/v1" });

app.setErrorHandler((error, _request, reply) => {
  app.log.error(error);
  reply.status(error.statusCode ?? 500).send({
    error: error.code ?? "internal_error",
    detail: error.message,
  });
});

const worker = startWorker();
worker.on("failed", (job, err) => {
  app.log.error({ jobId: job?.id, err }, "workflow_job_failed");
});

try {
  await app.listen({ port: env.PORT, host: "0.0.0.0" });
} catch (err) {
  app.log.error(err);
  await worker.close();
  await sql.end();
  process.exit(1);
}
