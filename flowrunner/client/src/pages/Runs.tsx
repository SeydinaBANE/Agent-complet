import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

type Run = {
  id: string;
  status: "pending" | "running" | "completed" | "failed";
  workflow_id: string;
  started_at: string;
  finished_at?: string;
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-500",
  running: "bg-blue-500 animate-pulse",
  completed: "bg-green-500",
  failed: "bg-red-500",
};

async function fetchRuns(): Promise<{ data: Run[] }> {
  const res = await fetch("/api/v1/runs", {
    headers: { "x-api-key": import.meta.env["VITE_FLOWRUNNER_API_KEY"] ?? "" },
  });
  return res.json() as Promise<{ data: Run[] }>;
}

export default function Runs() {
  const { data, isLoading } = useQuery({ queryKey: ["runs"], queryFn: fetchRuns });

  if (isLoading) return <div className="p-8 text-gray-400">Loading…</div>;

  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold mb-6">Runs</h1>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-500 border-b border-gray-800">
            <th className="pb-3 pr-4">ID</th>
            <th className="pb-3 pr-4">Workflow</th>
            <th className="pb-3 pr-4">Status</th>
            <th className="pb-3">Started</th>
          </tr>
        </thead>
        <tbody>
          {(data?.data ?? []).map((run) => (
            <tr key={run.id} className="border-b border-gray-800 hover:bg-gray-800/50">
              <td className="py-3 pr-4 font-mono text-xs">
                <Link to={`/runs/${run.id}`} className="text-indigo-400 hover:underline">
                  {run.id.slice(0, 8)}
                </Link>
              </td>
              <td className="py-3 pr-4 font-mono text-xs">{run.workflow_id.slice(0, 8)}</td>
              <td className="py-3 pr-4">
                <span className={`inline-block w-2 h-2 rounded-full mr-2 ${STATUS_COLORS[run.status] ?? "bg-gray-500"}`} />
                {run.status}
              </td>
              <td className="py-3 text-gray-400">{new Date(run.started_at).toLocaleString()}</td>
            </tr>
          ))}
          {!data?.data.length && (
            <tr>
              <td colSpan={4} className="py-8 text-center text-gray-500">No runs yet</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
