import postgres from "postgres";
import { env } from "./config.js";

export const sql = postgres(env.FLOWRUNNER_DATABASE_URL, {
  max: 10,
  idle_timeout: 30,
  connect_timeout: 10,
});
