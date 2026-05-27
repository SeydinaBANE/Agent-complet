import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import postgres from "postgres";

const __dirname = dirname(fileURLToPath(import.meta.url));
const sql = postgres(process.env["FLOWRUNNER_DATABASE_URL"] ?? "");

const migrationsDir = join(__dirname, "..", "migrations");
const files = ["001_initial.sql"];

for (const file of files) {
  const content = readFileSync(join(migrationsDir, file), "utf8");
  console.log(`Running migration: ${file}`);
  await sql.unsafe(content);
  console.log(`✓ ${file}`);
}

await sql.end();
console.log("Migrations complete.");
