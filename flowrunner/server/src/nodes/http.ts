import type { WorkflowContext, WorkflowNode } from "../types.js";

const BLOCKED_HOSTS = new Set([
  "localhost",
  "127.0.0.1",
  "0.0.0.0",
  "169.254.169.254",
  "[::1]",
  "metadata.google.internal",
  "instance-data",
]);

function isUrlBlocked(urlStr: string): boolean {
  try {
    const parsed = new URL(urlStr);
    const hostname = parsed.hostname.toLowerCase();

    if (BLOCKED_HOSTS.has(hostname)) return true;
    if (hostname.endsWith(".internal")) return true;
    if (hostname.endsWith(".local")) return true;
    if (/^10\./.test(hostname) || /^172\.(1[6-9]|2\d|3[01])\./.test(hostname)) return true;
    if (/^192\.168\./.test(hostname)) return true;

    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return true;

    return false;
  } catch {
    return true;
  }
}

const HTTP_TIMEOUT_MS = 30_000;

export async function executeHttpNode(
  node: WorkflowNode,
  ctx: WorkflowContext,
  _runId: string,
): Promise<WorkflowContext> {
  const { url, method = "GET", headers = {}, body } = node.data as {
    url: string;
    method?: string;
    headers?: Record<string, string>;
    body?: unknown;
  };

  if (isUrlBlocked(url)) {
    throw new Error(`URL blocked by security policy: ${url}`);
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), HTTP_TIMEOUT_MS);

  try {
    const init: RequestInit = {
      method,
      headers: { "Content-Type": "application/json", ...headers },
      signal: controller.signal,
    };
    if (body !== undefined) init.body = JSON.stringify(body);

    const response = await fetch(url, init);
    const responseBody = await response.text();
    let parsedBody: unknown = responseBody;
    try {
      parsedBody = JSON.parse(responseBody);
    } catch {
      // keep as string
    }

    return {
      ...ctx,
      [`${node.id}_status`]: response.status,
      [`${node.id}_body`]: parsedBody,
    };
  } finally {
    clearTimeout(timeout);
  }
}
