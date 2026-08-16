import React, { useEffect, useState } from 'react';
import { fetchInterfaces } from '../services/apiService';

const InterfaceSelector = ({ onInterfaceSelect, onInterfaceDeselect }) => {
  const [interfaces, setInterfaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedInterface, setSelectedInterface] = useState(null);

  useEffect(() => {
    const loadInterfaces = async () => {
      try {
        setLoading(true);
        const data = await fetchInterfaces();
        setInterfaces(data.interfaces || []);
        setLoading(false);
      } catch (err) {
        setError('Failed to load network interfaces');
        setLoading(false);
        console.error(err);
      }
    };

    loadInterfaces();
  }, []);

  const handleSelect = (interfaceName) => {
    setSelectedInterface(interfaceName);
    onInterfaceSelect(interfaceName);
  };

  const handleDeselect = () => {
    setSelectedInterface(null);
    onInterfaceDeselect();
  };

  if (loading) {
    return <div className="p-4">Loading network interfaces...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">{error}</div>;
  }

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Network Interfaces</h2>
      {interfaces.length === 0 ? (
        <p className="text-gray-500">No network interfaces found.</p>
      ) : (
        <div className="space-y-2">
          {interfaces.map((iface) => (
            <div
              key={iface.name}
              className="border rounded-lg p-3 hover:bg-gray-50 transition-colors cursor-pointer"
              onClick={() => {
                if (selectedInterface === iface.name) {
                  handleDeselect();
                } else {
                  handleSelect(iface.name);
                }
              }}
            >
              <div className="flex justify-between items-start">
                <div className="flex items-center">
                  <input
                    type="radio"
                    id={`iface-${iface.name}`}
                    name="interface-select"
                    checked={selectedInterface === iface.name}
                    readOnly
                    className="h-4 w-4 text-indigo-600"
                  />
                  <span className="ml-2 font-mono">{iface.name}</span>
                </div>
                {selectedInterface === iface.name && (
                  <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                    Selected
                  </span>
                )}
              </div>
              <div className="mt-2 space-y-1 text-sm text-gray-600">
                <div>
                  <span className="font-medium">IPv4:</span> {iface.ipv4 || 'None'}
                </div>
                <div>
                  <span className="font-medium">IPv6:</span> {iface.ipv6 || 'None'}
                </div>
                <div>
                  <span className="font-medium">MAC:</span> {iface.mac || 'None'}
                </div>
                <div>
                  <span className="font-medium">Status:</span>
                  <span className={`font-medium ${iface.status === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                    {iface.status}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="font-medium">Bytes:</span>
                    <span className="block">{iface.bytes_sent} sent / {iface.bytes_received} received</span>
                  </div>
                  <div>
                    <span className="font-medium">Packets:</span>
                    <span className="block">{iface.packets_sent} sent / {iface.packets_received} received</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {selectedInterface && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-semibold mb-2">Selected Interface</h3>
          <p className="font-mono">{selectedInterface}</p>
          <button
            onClick={handleDeselect}
            className="mt-2 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
          >
            Stop Monitoring
          </button>
        </div>
      )}
    </div>
  );
};

export default InterfaceSelector;