import { Route, Routes, NavLink } from "react-router-dom";
import Editor from "./pages/Editor.js";
import Runs from "./pages/Runs.js";
import Monitor from "./pages/Monitor.js";

const navClass = ({ isActive }: { isActive: boolean }) =>
  `px-4 py-2 rounded text-sm font-medium transition-colors ${
    isActive ? "bg-indigo-600 text-white" : "text-gray-300 hover:bg-gray-700"
  }`;

export default function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <nav className="border-b border-gray-800 px-6 py-3 flex items-center gap-4">
        <span className="font-bold text-indigo-400 mr-4">FlowRunner</span>
        <NavLink to="/editor" className={navClass}>Editor</NavLink>
        <NavLink to="/runs" className={navClass}>Runs</NavLink>
        <NavLink to="/monitor" className={navClass}>Monitor</NavLink>
      </nav>

      <Routes>
        <Route path="/" element={<Monitor />} />
        <Route path="/editor" element={<Editor />} />
        <Route path="/runs" element={<Runs />} />
        <Route path="/monitor" element={<Monitor />} />
      </Routes>
    </div>
  );
}
