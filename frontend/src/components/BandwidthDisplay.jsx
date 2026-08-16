import React, { useEffect, useState } from 'react';
import { fetchStats, selectInterface, deselectInterface } from '../services/apiService';
import { wsService } from '../services/wsService';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const BandwidthDisplay = ({ selectedInterface }) => {
  const [stats, setStats] = useState({
    download_bps: 0,
    upload_bps: 0,
    download_mbps: 0,
    upload_mbps: 0,
    total_bytes_sent: 0,
    total_bytes_recv: 0,
    total_packets_sent: 0,
    total_packets_recv: 0,
    packet_download_pps: 0,
    packet_upload_pps: 0
  });
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [error, setError] = useState(null);
  // Chart data: last 30 seconds
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    console.log('BandwidthDisplay useEffect running with selectedInterface:', selectedInterface);
    // Start monitoring and connect WebSocket when interface is selected
    if (selectedInterface) {
      const startMonitoring = async () => {
        try {
          await selectInterface(selectedInterface);
          setIsMonitoring(true);
          setError(null);
          // Connect WebSocket when monitoring starts
          wsService.connect();
        } catch (err) {
          setError('Failed to start monitoring');
          console.error(err);
        }
      };
      startMonitoring();
    } else {
      // Disconnect WebSocket when interface is deselected
      console.log('No selected interface, disconnecting WebSocket');
      wsService.disconnect();
    }

    // Subscribe to WebSocket updates
    const unsubscribe = wsService.subscribe((data) => {
      console.log('Received WebSocket data:', data);
      setStats(data);
      // Update chart data
      const now = new Date();
      const timeString = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
      const newData = {
        time: timeString,
        download: data.download_mbps,
        upload: data.upload_mbps
      };
      setChartData(prev => {
        const updated = [...prev, newData];
        // Keep only last 30 points
        if (updated.length > 30) {
          updated.shift();
        }
        return updated;
      });
    });

    // Cleanup on unmount or when selectedInterface changes
    return () => {
      console.log('Cleaning up BandwidthDisplay useEffect');
      unsubscribe();
      wsService.disconnect();
      if (selectedInterface) {
        deselectInterface().catch(console.error);
      }
    };
  }, [selectedInterface]);

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatBitsPerSec = (bps) => {
    if (bps === 0) return '0 bps';
    const kbps = bps / 1000;
    const mbps = kbps / 1000;
    const gbps = mbps / 1000;

    if (gbps >= 1) {
      return gbps.toFixed(2) + ' Gbps';
    } else if (mbps >= 1) {
      return mbps.toFixed(2) + ' Mbps';
    } else if (kbps >= 1) {
      return kbps.toFixed(2) + ' Kbps';
    } else {
      return bps.toFixed(2) + ' bps';
    }
  };

  if (error) {
    return <div className="p-4 text-red-500">{error}</div>;
  }

  if (!selectedInterface) {
    return <div className="p-4 text-gray-500">Select an interface to monitor bandwidth</div>;
  }

  return (
    <div className="p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Bandwidth Monitoring: {selectedInterface}</h3>
        <p className={`text-sm ${isMonitoring ? 'text-green-600' : 'text-gray-500'}`}>
          {isMonitoring ? 'Monitoring active' : 'Monitoring stopped'}
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-md p-4">
          <p className="text-sm font-medium text-gray-500">Download Speed</p>
          <p className="text-2xl font-bold text-blue-600">{formatBitsPerSec(stats.download_bps)}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <p className="text-sm font-medium text-gray-500">Upload Speed</p>
          <p className="text-2xl font-bold text-green-600">{formatBitsPerSec(stats.upload_bps)}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <p className="text-sm font-medium text-gray-500">Packets/sec</p>
          <p className="text-2xl font-bold text-purple-600">
            {Math.round(stats.packet_download_pps + stats.packet_upload_pps)}
          </p>
          <p className="text-xs text-gray-400">
            ↓{Math.round(stats.packet_download_pps)} ↑{Math.round(stats.packet_upload_pps)}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <p className="text-sm font-medium text-gray-500">Total Received</p>
          <p className="text-2xl font-bold text-indigo-600">
            {formatBytes(stats.total_bytes_recv)}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <p className="text-sm font-medium text-gray-500">Total Sent</p>
          <p className="text-2xl font-bold text-indigo-600">
            {formatBytes(stats.total_bytes_sent)}
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold mb-4">Bandwidth Usage (Mbps) - Last 30 Seconds</h3>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" tick={{ fontSize: 12 }} />
              <YAxis label={{ value: 'Mbps', angle: -90, position: 'insideLeft' }} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(value) => `${value} Mbps`} />
              <Legend verticalAlign="top" height={36} />
              <Line type="monotone" dataKey="download" stroke="#4299e1" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="upload" stroke="#48bb78" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-500">Collecting data for chart...</p>
        )}
      </div>

      {/* Detailed Statistics */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="font-semibold mb-2">Detailed Statistics</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span>Download Rate:</span>
            <span className="font-mono">{formatBitsPerSec(stats.download_bps)}</span>
          </div>
          <div className="flex justify-between">
            <span>Upload Rate:</span>
            <span className="font-mono">{formatBitsPerSec(stats.upload_bps)}</span>
          </div>
          <div className="flex justify-between">
            <span>Packet Download Rate:</span>
            <span className="font-mono">{stats.packet_download_pps.toFixed(1)} pps</span>
          </div>
          <div className="flex justify-between">
            <span>Packet Upload Rate:</span>
            <span className="font-mono">{stats.packet_upload_pps.toFixed(1)} pps</span>
          </div>
          <div className="flex justify-between">
            <span>Total Received:</span>
            <span className="font-mono">{formatBytes(stats.total_bytes_recv)}</span>
          </div>
          <div className="flex justify-between">
            <span>Total Sent:</span>
            <span className="font-mono">{formatBytes(stats.total_bytes_sent)}</span>
          </div>
          <div className="flex justify-between">
            <span>Packets Received:</span>
            <span className="font-mono">{stats.total_packets_recv.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span>Packets Sent:</span>
            <span className="font-mono">{stats.total_packets_sent.toLocaleString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BandwidthDisplay;