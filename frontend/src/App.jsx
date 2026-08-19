import React, { useState, useEffect } from 'react';
import { fetchHealth, fetchInterfaces } from './services/apiService';
import InterfaceSelector from './components/InterfaceSelector';
import BandwidthDisplay from './components/BandwidthDisplay';
import ProtocolAnalysis from './components/ProtocolAnalysis';
import IPAnalysis from './components/IPAnalysis';
import PortAnalysis from './components/PortAnalysis';
import HistoricalTraffic from './components/HistoricalTraffic';
import './index.css';

function App() {
  const [backendStatus, setBackendStatus] = useState('Checking...');
  const [isConnected, setIsConnected] = useState(false);
  const [selectedInterface, setSelectedInterface] = useState(null);
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme') || 'dark';
    return saved === 'light' ? 'light' : 'dark';
  });

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

  // Handle theme changes from localStorage (e.g., if changed in another tab)
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'theme') {
        setTheme(e.newValue === 'light' ? 'light' : 'dark');
      }
    };
    window.addEventListener('storage', handleStorageChange);
    // Set initial state based on current class (in case it was set by main.jsx)
    const isDark = document.documentElement.classList.contains('dark');
    setTheme(isDark ? 'dark' : 'light');
    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  const toggleTheme = () => {
    window.toggleTheme();
  };

  return (
    <div className="min-h-screen">
      <header className="bg-bgSurface shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-textPrimary">
              NetScope - Network Bandwidth Analyzer
            </h1>
            <p className="mt-2 text-sm text-textSecondary">
              Real-time network traffic monitoring
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={toggleTheme}
              className="p-2 rounded hover:bg-textPrimary/5 focus:outline-none focus:ring-2 focus:ring-accentPrimary"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-bgSurface rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-textPrimary mb-4">
            Network Interface Discovery & Bandwidth Monitoring
          </h2>
          <div className="space-y-4">
            <div className={`p-3 rounded-lg ${isConnected ? 'bg-statusSuccess/10 border border-statusSuccess' : 'bg-statusError/10 border border-statusError'}`}>
              <p className="font-medium text-textPrimary">{backendStatus}</p>
              <p className="text-sm text-textSecondary">
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
                <HistoricalTraffic />
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;