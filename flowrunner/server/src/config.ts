import { cleanEnv, str, url, num } from "envalid";

export const env = cleanEnv(process.env, {
  FLOWRUNNER_DATABASE_URL: url({ desc: "PostgreSQL connection URL" }),
  REDIS_URL: url({ default: "redis://localhost:6379" }),
  FLOWRUNNER_API_KEY: str({ desc: "API key for this service" }),
  AGENTCORE_ORIGIN: url({ default: "http://localhost:8000" }),
  AGENTCORE_API_KEY: str({ desc: "AgentCore API key (for ai-agent node)" }),
  PORT: num({ default: 3001 }),
  NODE_ENV: str({ choices: ["development", "production", "test"], default: "development" }),
});
