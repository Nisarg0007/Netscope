import React, { useState, useEffect } from 'react';
import { fetchHealth } from './services/apiService';
import InterfaceSelector from './components/InterfaceSelector';
import BandwidthDisplay from './components/BandwidthDisplay';
import ProtocolAnalysis from './components/ProtocolAnalysis';
import IPAnalysis from './components/IPAnalysis';
import PortAnalysis from './components/PortAnalysis';
import './index.css';

function App() {
  const [backendStatus, setBackendStatus] = useState('Checking...');
  const [isConnected, setIsConnected] = useState(false);
  const [selectedInterface, setSelectedInterface] = useState(null);

  useEffect(() => {
    const checkBackend = async () => {
      console.log('Checking backend health...');
      try {
        const data = await fetchHealth();
        console.log('Backend health check successful:', data);
        setBackendStatus(`Backend Status: ${data.status}`);
        setIsConnected(true);
      } catch (error) {
        console.error('Backend health check failed:', error);
        setBackendStatus('Backend Error: Connection failed');
        setIsConnected(false);
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 5000);
    return () => clearInterval(interval);
  }, []);

  // Auto-select the first available interface that is up (for testing)
  useEffect(() => {
    console.log('Auto-select effect running');
    if (!selectedInterface) {
      const autoSelect = async () => {
        try {
          console.log('Fetching interfaces');
          const interfacesData = await fetchInterfaces();
          console.log('Interfaces data:', interfacesData);
          const upInterface = interfacesData.interfaces.find(iface => iface.status === 'up');
          console.log('Up interface:', upInterface);
          if (upInterface) {
            console.log('Setting selected interface to:', upInterface.name);
            setSelectedInterface(upInterface.name);
          }
        } catch (err) {
          console.error('Failed to auto-select interface:', err);
        }
      };
      autoSelect();
    }
  }, [selectedInterface]);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            NetScope - Network Bandwidth Analyzer
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Real-time network traffic monitoring
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Network Interface Discovery & Bandwidth Monitoring
          </h2>
          <div className="space-y-4">
            <div className={`p-3 rounded-lg ${isConnected ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <p className="font-medium">{backendStatus}</p>
              <p className="text-sm text-gray-500">
                {isConnected ? 'Connected to NetScope API' : 'Unable to connect to backend'}
              </p>
            </div>
            <InterfaceSelector onInterfaceSelect={setSelectedInterface} onInterfaceDeselect={() => setSelectedInterface(null)} />
            {selectedInterface && (
              <>
                <BandwidthDisplay selectedInterface={selectedInterface} />
                <ProtocolAnalysis />
                <IPAnalysis />
                <PortAnalysis />
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;