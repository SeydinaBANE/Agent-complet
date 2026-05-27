import { useQuery } from "@tanstack/react-query";

type Run = {
  id: string;
  status: string;
  workflow_id: string;
  started_at: string;
};

async function fetchActiveRuns(): Promise<{ data: Run[] }> {
  const res = await fetch("/api/v1/runs?status=running", {
    headers: { "x-api-key": import.meta.env["VITE_FLOWRUNNER_API_KEY"] ?? "" },
  });
  return res.json() as Promise<{ data: Run[] }>;
}

export default function Monitor() {
  const { data } = useQuery({
    queryKey: ["runs", "active"],
    queryFn: fetchActiveRuns,
    refetchInterval: 2000,
  });

  const activeRuns = data?.data ?? [];

  return (
    <div className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-xl font-semibold">Monitor</h1>
        <span className="text-xs text-gray-500">auto-refresh every 2s</span>
        {activeRuns.length > 0 && (
          <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full">
            {activeRuns.length} active
          </span>
        )}
      </div>

      {activeRuns.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <p className="text-4xl mb-4">✓</p>
          <p>No runs in progress</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {activeRuns.map((run) => (
            <div key={run.id} className="bg-gray-800 rounded-lg p-4 flex items-center gap-4">
              <span className="w-3 h-3 rounded-full bg-blue-500 animate-pulse shrink-0" />
              <div>
                <p className="font-mono text-sm">{run.id}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  Workflow {run.workflow_id.slice(0, 8)} · started{" "}
                  {new Date(run.started_at).toLocaleTimeString()}
                </p>
              </div>
              <span className="ml-auto text-xs text-blue-400">running</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
