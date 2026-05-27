import { useCallback, useState } from "react";
import ReactFlow, {
  addEdge,
  Background,
  Controls,
  type Connection,
  type Edge,
  type Node,
  useEdgesState,
  useNodesState,
} from "reactflow";
import "reactflow/dist/style.css";

const NODE_TYPES = ["http", "condition", "transform", "delay", "ai-agent"];

const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

export default function Editor() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge(connection, eds)),
    [setEdges],
  );

  const addNode = (type: string) => {
    const newNode: Node = {
      id: crypto.randomUUID(),
      type: "default",
      position: { x: 200 + nodes.length * 50, y: 200 },
      data: { label: type, type },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  return (
    <div className="flex h-[calc(100vh-53px)]">
      {/* Palette */}
      <div className="w-48 border-r border-gray-800 p-4 flex flex-col gap-2">
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Nodes</p>
        {NODE_TYPES.map((type) => (
          <button
            key={type}
            onClick={() => addNode(type)}
            className="text-left px-3 py-2 rounded bg-gray-800 hover:bg-gray-700 text-sm"
          >
            {type}
          </button>
        ))}
      </div>

      {/* Canvas */}
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={(_, node) => setSelectedNode(node)}
          fitView
        >
          <Background />
          <Controls />
        </ReactFlow>
      </div>

      {/* Config panel */}
      {selectedNode && (
        <div className="w-64 border-l border-gray-800 p-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Node config</p>
          <p className="text-sm font-medium">{String(selectedNode.data.label)}</p>
          <p className="text-xs text-gray-500 mt-1">ID: {selectedNode.id.slice(0, 8)}</p>
          <button
            onClick={() => setSelectedNode(null)}
            className="mt-4 text-xs text-gray-500 hover:text-gray-300"
          >
            Close
          </button>
        </div>
      )}
    </div>
  );
}
