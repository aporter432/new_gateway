import React from 'react';

const ArchitectureDiagram = () => {
  return (
    <div className="flex flex-col items-center w-full">
      <h2 className="text-xl font-bold mb-4">Protexis Command Architecture</h2>

      {/* Main container */}
      <div className="relative border-2 border-gray-500 rounded-lg p-4 w-full max-w-4xl bg-gray-50 mb-8">
        <div className="absolute -top-3 left-4 bg-gray-50 px-2 text-gray-700 font-semibold">Application Layer</div>

        {/* User Interface */}
        <div className="border-2 border-blue-500 rounded-lg p-3 mb-4 bg-blue-50">
          <div className="font-semibold text-blue-700 mb-2">UI Layer (protexis_ui/)</div>
          <div className="grid grid-cols-3 gap-2">
            <div className="border border-blue-300 rounded p-2 bg-white text-sm">Login</div>
            <div className="border border-blue-300 rounded p-2 bg-white text-sm">Dashboard</div>
            <div className="border border-blue-300 rounded p-2 bg-white text-sm">User Management</div>
          </div>
        </div>

        {/* API Layer */}
        <div className="border-2 border-green-500 rounded-lg p-3 mb-4 bg-green-50">
          <div className="font-semibold text-green-700 mb-2">API Layer (api/)</div>
          <div className="grid grid-cols-1 gap-2 mb-3">
            <div className="border border-green-300 rounded p-2 bg-white text-sm font-semibold">Main FastAPI Application (main.py)</div>
          </div>
          <div className="grid grid-cols-4 gap-2">
            <div className="border border-green-300 rounded p-2 bg-white text-sm">Auth Routes</div>
            <div className="border border-green-300 rounded p-2 bg-white text-sm">User Routes</div>
            <div className="border border-green-300 rounded p-2 bg-white text-sm">Dashboard Routes</div>
            <div className="border border-green-300 rounded p-2 bg-white text-sm">Common Models</div>
          </div>
        </div>

        {/* Protocol-Specific APIs */}
        <div className="grid grid-cols-2 gap-4">
          {/* OGx API */}
          <div className="border-2 border-purple-500 rounded-lg p-3 bg-purple-50">
            <div className="font-semibold text-purple-700 mb-2">OGx API (api_ogx/)</div>
            <div className="grid grid-cols-1 gap-2 mb-2">
              <div className="border border-purple-300 rounded p-2 bg-white text-sm">OGx FastAPI App (ogx_main.py)</div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="border border-purple-300 rounded p-2 bg-white text-sm">Message Routes</div>
              <div className="border border-purple-300 rounded p-2 bg-white text-sm">Terminal Routes</div>
              <div className="border border-purple-300 rounded p-2 bg-white text-sm">Update Routes</div>
              <div className="border border-purple-300 rounded p-2 bg-white text-sm">OGx Models</div>
              <div className="border border-purple-300 rounded p-2 bg-white text-sm">OGx Services</div>
              <div className="border border-purple-300 rounded p-2 bg-white text-sm">OGx Middleware</div>
            </div>
          </div>

          {/* Future Protocol API (placeholder) */}
          <div className="border-2 border-yellow-500 rounded-lg p-3 bg-yellow-50">
            <div className="font-semibold text-yellow-700 mb-2">Future Protocol API (api_xxxxx/)</div>
            <div className="grid grid-cols-1 gap-2 mb-2">
              <div className="border border-yellow-300 rounded p-2 bg-white text-sm">Protocol FastAPI App</div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="border border-yellow-300 rounded p-2 bg-white text-sm">Protocol Routes</div>
              <div className="border border-yellow-300 rounded p-2 bg-white text-sm">Protocol Models</div>
              <div className="border border-yellow-300 rounded p-2 bg-white text-sm">Protocol Services</div>
              <div className="border border-yellow-300 rounded p-2 bg-white text-sm">Protocol Middleware</div>
            </div>
          </div>
        </div>
      </div>

      {/* Protocol Layer */}
      <div className="relative border-2 border-gray-500 rounded-lg p-4 w-full max-w-4xl bg-gray-50 mb-8">
        <div className="absolute -top-3 left-4 bg-gray-50 px-2 text-gray-700 font-semibold">Protocol Layer</div>

        <div className="grid grid-cols-2 gap-4">
          {/* OGx Protocol */}
          <div className="border-2 border-purple-500 rounded-lg p-3 bg-purple-50">
            <div className="font-semibold text-purple-700 mb-2">OGx Protocol (protocol/ogx/)</div>
            <div className="grid grid-cols-2 gap-2">
              <div className="border border-purple-300 rounded p-2 bg-white text-sm">Constants</div>
              <div className="border border-purple-300 rounded p-2 bg-white text-sm">Models</div>
              <div className="border border-purple-300 rounded p-2 bg-white text-sm">Protocol Handler</div>
              <div className="border border-purple-300 rounded p-2 bg-white text-sm">Validation</div>
            </div>
          </div>

          {/* Future Protocol (placeholder) */}
          <div className="border-2 border-yellow-500 rounded-lg p-3 bg-yellow-50">
            <div className="font-semibold text-yellow-700 mb-2">Future Protocol (protocol/xxxxx/)</div>
            <div className="grid grid-cols-2 gap-2">
              <div className="border border-yellow-300 rounded p-2 bg-white text-sm">Constants</div>
              <div className="border border-yellow-300 rounded p-2 bg-white text-sm">Models</div>
              <div className="border border-yellow-300 rounded p-2 bg-white text-sm">Protocol Handler</div>
              <div className="border border-yellow-300 rounded p-2 bg-white text-sm">Validation</div>
            </div>
          </div>
        </div>
      </div>

      {/* Infrastructure Layer */}
      <div className="relative border-2 border-gray-500 rounded-lg p-4 w-full max-w-4xl bg-gray-50">
        <div className="absolute -top-3 left-4 bg-gray-50 px-2 text-gray-700 font-semibold">Shared Infrastructure</div>

        <div className="grid grid-cols-4 gap-2">
          <div className="border-2 border-red-300 rounded p-2 bg-white text-sm">Core Settings</div>
          <div className="border-2 border-red-300 rounded p-2 bg-white text-sm">Database</div>
          <div className="border-2 border-red-300 rounded p-2 bg-white text-sm">Redis</div>
          <div className="border-2 border-red-300 rounded p-2 bg-white text-sm">Logging</div>
        </div>
      </div>

      {/* Request flow arrows */}
      <div className="mt-8 w-full max-w-4xl">
        <h3 className="font-semibold mb-2">Request Flow Example</h3>
        <div className="border-2 border-gray-300 rounded-lg p-4 bg-white">
          <div className="grid grid-cols-6 gap-2 items-center">
            <div className="col-span-1 p-2 border border-blue-300 rounded bg-blue-50 text-center text-sm">
              UI
            </div>
            <div className="col-span-1 text-center">
              →
            </div>
            <div className="col-span-1 p-2 border border-green-300 rounded bg-green-50 text-center text-sm">
              API
            </div>
            <div className="col-span-1 text-center">
              →
            </div>
            <div className="col-span-1 p-2 border border-purple-300 rounded bg-purple-50 text-center text-sm">
              OGx API
            </div>
            <div className="col-span-1 text-center">
              →
            </div>
          </div>
          <div className="grid grid-cols-4 gap-2 items-center mt-2">
            <div className="col-span-3"></div>
            <div className="col-span-1 p-2 border border-purple-300 rounded bg-purple-50 text-center text-sm">
              OGx Protocol
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArchitectureDiagram;
