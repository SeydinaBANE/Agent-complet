import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";

type Step = {
  id: string;
  node_id: string;
  node_type: string;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  error: string | null;
  duration_ms: number;
  created_at: string;
};

type RunLogs = {
  run_id: string;
  steps: Step[];
};

type RunDetail = {
  id: string;
  workflow_id: string;
  workflow_name: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
};

const API_KEY = import.meta.env["VITE_FLOWRUNNER_API_KEY"] ?? "";

async function fetchRun(id: string): Promise<RunDetail> {
  const res = await fetch(`/api/v1/runs/${id}`, { headers: { "x-api-key": API_KEY } });
  if (!res.ok) throw new Error("Run not found");
  return res.json() as Promise<RunDetail>;
}

async function fetchLogs(id: string): Promise<RunLogs> {
  const res = await fetch(`/api/v1/runs/${id}/logs`, { headers: { "x-api-key": API_KEY } });
  if (!res.ok) throw new Error("Logs not found");
  return res.json() as Promise<RunLogs>;
}

const STATUS_BADGE: Record<string, string> = {
  pending: "bg-yellow-600 text-yellow-100",
  running: "bg-blue-600 text-blue-100",
  completed: "bg-green-700 text-green-100",
  failed: "bg-red-700 text-red-100",
};

export default function RunDetail() {
  const { id } = useParams<{ id: string }>();
  const runId = id ?? "";

  const { data: run, isLoading: runLoading } = useQuery({
    queryKey: ["run", runId],
    queryFn: () => fetchRun(runId),
    refetchInterval: (q) =>
      q.state.data?.status === "running" || q.state.data?.status === "pending" ? 2000 : false,
  });

  const { data: logs, isLoading: logsLoading } = useQuery({
    queryKey: ["run-logs", runId],
    queryFn: () => fetchLogs(runId),
    refetchInterval: run?.status === "running" || run?.status === "pending" ? 2000 : false,
    enabled: !!run,
  });

  if (runLoading) return <div className="p-8 text-gray-400">Loading…</div>;
  if (!run) return <div className="p-8 text-red-400">Run not found</div>;

  return (
    <div className="p-6 max-w-4xl">
      <div className="flex items-center gap-3 mb-6">
        <Link to="/runs" className="text-gray-500 hover:text-gray-300 text-sm">← Runs</Link>
        <span className="text-gray-700">/</span>
        <span className="font-mono text-sm">{run.id.slice(0, 8)}</span>
        <span
          className={`ml-2 text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_BADGE[run.status] ?? "bg-gray-600 text-gray-100"}`}
        >
          {run.status}
        </span>
      </div>

      <div className="bg-gray-800 rounded-lg p-4 mb-6 grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-gray-500 text-xs mb-1">Workflow</p>
          <p>{run.workflow_name}</p>
        </div>
        <div>
          <p className="text-gray-500 text-xs mb-1">Run ID</p>
          <p className="font-mono">{run.id}</p>
        </div>
        {run.started_at && (
          <div>
            <p className="text-gray-500 text-xs mb-1">Started</p>
            <p>{new Date(run.started_at).toLocaleString()}</p>
          </div>
        )}
        {run.finished_at && (
          <div>
            <p className="text-gray-500 text-xs mb-1">Finished</p>
            <p>{new Date(run.finished_at).toLocaleString()}</p>
          </div>
        )}
        {run.error && (
          <div className="col-span-2">
            <p className="text-gray-500 text-xs mb-1">Error</p>
            <p className="text-red-400">{run.error}</p>
          </div>
        )}
      </div>

      <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
        Steps
      </h2>

      {logsLoading ? (
        <div className="text-gray-500 text-sm">Loading steps…</div>
      ) : (logs?.steps.length ?? 0) === 0 ? (
        <div className="text-gray-600 text-sm py-8 text-center">No steps yet</div>
      ) : (
        <div className="space-y-3">
          {logs?.steps.map((step, idx) => (
            <StepCard key={step.id} step={step} index={idx + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

function StepCard({ step, index }: { step: Step; index: number }) {
  const hasError = !!step.error;

  return (
    <div
      className={`rounded-lg border ${hasError ? "border-red-700 bg-red-950/30" : "border-gray-700 bg-gray-800"}`}
    >
      <div className="flex items-center gap-3 px-4 py-3">
        <span className="w-6 h-6 rounded-full bg-gray-700 text-xs flex items-center justify-center shrink-0">
          {index}
        </span>
        <div className="flex-1">
          <span className="font-mono text-sm">{step.node_id}</span>
          <span className="ml-2 text-xs text-gray-500 bg-gray-700 px-1.5 py-0.5 rounded">
            {step.node_type}
          </span>
        </div>
        <span className="text-xs text-gray-500">{step.duration_ms}ms</span>
        {hasError && <span className="text-xs text-red-400">failed</span>}
      </div>

      {(hasError || step.output) && (
        <div className="px-4 pb-3 space-y-2">
          {step.output && !hasError && (
            <details className="text-xs">
              <summary className="cursor-pointer text-gray-500 hover:text-gray-300">Output</summary>
              <pre className="mt-1 p-2 bg-gray-900 rounded overflow-x-auto text-green-400">
                {JSON.stringify(step.output, null, 2)}
              </pre>
            </details>
          )}
          {hasError && (
            <p className="text-xs text-red-400 bg-red-950/50 px-2 py-1 rounded">{step.error}</p>
          )}
        </div>
      )}
    </div>
  );
}
