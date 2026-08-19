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
    return <div className="p-4 text-textPrimary">Loading network interfaces...</div>;
  }

  if (error) {
    return <div className="p-4 text-statusError">{error}</div>;
  }

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold text-textPrimary mb-4">Network Interfaces</h2>
      {interfaces.length === 0 ? (
        <p className="text-textSecondary">No network interfaces found.</p>
      ) : (
        <div className="space-y-2">
          {interfaces.map((iface) => (
            <div
              key={iface.name}
              className="border border-border rounded-lg p-3 hover:bg-bgCard/50 transition-colors cursor-pointer"
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
                    className="h-4 w-4 text-accentSecondary"
                  />
                  <span className="ml-2 font-mono">{iface.name}</span>
                </div>
                {selectedInterface === iface.name && (
                  <span className="bg-statusSuccess/20 text-statusSuccess text-xs px-2 py-1 rounded">
                    Selected
                  </span>
                )}
              </div>
              <div className="mt-2 space-y-1 text-sm text-textSecondary">
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
                  <span className={`font-medium ${iface.status === 'up' ? 'text-statusSuccess' : 'text-statusError'}`}>
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
        <div className="mt-6 p-4 bg-accentPrimary/10 rounded-lg">
          <h3 className="font-semibold text-textPrimary mb-2">Selected Interface</h3>
          <p className="font-mono text-textPrimary">{selectedInterface}</p>
          <button
            onClick={handleDeselect}
            className="mt-2 px-4 py-2 bg-statusError text-textPrimary rounded hover:bg-statusError/80 transition-colors"
          >
            Stop Monitoring
          </button>
        </div>
      )}
    </div>
  );
};

export default InterfaceSelector;