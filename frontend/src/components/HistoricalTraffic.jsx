import React, { useEffect, useState } from 'react';
import { getHistory, clearHistory } from '../services/apiService';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const HistoricalTraffic = () => {
  const [snapshots, setSnapshots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [limit, setLimit] = useState(100); // default 100 snapshots

  // Format bytes to B/KB/MB/GB
  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Format bandwidth (bps) to appropriate unit
  const formatBandwidth = (bps) => {
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

  // Format timestamp to local time string
  const formatTimestamp = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  useEffect(() => {
    const fetchHistoryData = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getHistory(limit);
        setSnapshots(data.snapshots || []);
      } catch (err) {
        setError('Failed to load historical traffic data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchHistoryData();
    const interval = setInterval(fetchHistoryData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [limit]);

  const handleClearHistory = async () => {
    if (!window.confirm('Are you sure you want to clear all historical traffic data? This cannot be undone.')) {
      return;
    }
    try {
      await clearHistory();
      setSnapshots([]);
    } catch (err) {
      setError('Failed to clear history');
      console.error(err);
    }
  };

  if (loading && snapshots.length === 0) {
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold text-textPrimary mb-4">
          Historical Network Traffic
        </h2>
        <div className="animate-pulse">
          <div className="h-4 bg-textSecondary/20 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold text-textPrimary mb-4">
          Historical Network Traffic
        </h2>
        <div className="p-4 bg-statusError/10 border border-statusError rounded">
          <p className="text-statusError">{error}</p>
        </div>
      </div>
    );
  }

  if (snapshots.length === 0) {
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold text-textPrimary mb-4">
          Historical Network Traffic
        </h2>
        <div className="p-6 bg-accentPrimary/10 border border-accentPrimary rounded text-center">
          <p className="text-textSecondary">
            No historical traffic data available yet. Select an interface and allow monitoring to collect snapshots.
          </p>
        </div>
      </div>
    );
  }

  // Sort snapshots by timestamp ascending for charting (oldest first)
  const sortedSnapshots = [...snapshots].sort(
    (a, b) => new Date(a.timestamp) - new Date(b.timestamp)
  );

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-textPrimary mb-4">
        Historical Network Traffic
      </h2>

      {/* Controls */}
      <div className="mb-6 flex flex-wrap items-center gap-4">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-textSecondary">Snapshots:</span>
          <select
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value))}
            className="bg-bgCard border border-border rounded px-3 py-1 text-textPrimary focus:outline-none focus:ring-2 focus-ring-accentPrimary"
          >
            <option value="10">10</option>
            <option value="50">50</option>
            <option value="100">100</option>
            <option value="500">500</option>
          </select>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={handleClearHistory}
            className="px-4 py-2 bg-statusError text-textPrimary rounded hover:bg-statusError/80 transition-colors text-sm"
          >
            Clear History
          </button>
        </div>
      </div>

      {/* Summary */}
      <div className="mb-6 bg-bgCard rounded-lg shadow-md p-4">
        <h3 className="text-lg font-semibold text-textPrimary mb-4">
          Summary
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-textSecondary">Snapshots</p>
            <p className="font-medium text-textPrimary">{snapshots.length}</p>
          </div>
          {sortedSnapshots.length > 0 && (
            <>
              <div>
                <p className="text-textSecondary">Latest Download Rate</p>
                <p className="font-medium text-textPrimary">
                  {formatBandwidth(sortedSnapshots[sortedSnapshots.length - 1].download_rate)}
                </p>
              </div>
              <div>
                <p className="text-textSecondary">Latest Upload Rate</p>
                <p className="font-medium text-textPrimary">
                  {formatBandwidth(sortedSnapshots[sortedSnapshots.length - 1].upload_rate)}
                </p>
              </div>
              <div>
                <p className="text-textSecondary">Latest Timestamp</p>
                <p className="font-medium text-textPrimary">
                  {formatTimestamp(sortedSnapshots[sortedSnapshots.length - 1].timestamp)}
                </p>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6">
        {/* Bandwidth Chart */}
        <div className="bg-bgCard rounded-lg shadow-md p-4">
          <h3 className="text-lg font-semibold text-textPrimary mb-4">
            Bandwidth Trend (Download vs Upload)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={sortedSnapshots}>
              <CartesianGrid strokeDasharray="3 3" stroke="text-textSecondary/20" />
              <XAxis dataKey="timestamp" tickFormatter={formatTimestamp} text="text-textPrimary" />
              <YAxis label={{ value: 'Rate', angle: -90, position: 'insideLeft' }} text="text-textPrimary" />
              <Tooltip formatter={(value, name) => {
                if (name === 'download_rate' || name === 'upload_rate') {
                  return `${name === 'download_rate' ? 'Download' : 'Upload'}: ${formatBandwidth(value)}`;
                }
                return `${name}: ${value}`;
              }} />
              <Legend verticalAlign="top" height={36} />
              <Line type="monotone" dataKey="download_rate" stroke="#4299e1" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="upload_rate" stroke="#48bb78" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Packet Activity Chart */}
        <div className="bg-bgCard rounded-lg shadow-md p-4">
          <h3 className="text-lg font-semibold text-textPrimary mb-4">
            Packet Activity Over Time
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={sortedSnapshots}>
              <CartesianGrid strokeDasharray="3 3" stroke="text-textSecondary/20" />
              <XAxis dataKey="timestamp" tickFormatter={formatTimestamp} text="text-textPrimary" />
              <YAxis label={{ value: 'Packets', angle: -90, position: 'insideLeft' }} text="text-textPrimary" />
              <Tooltip formatter={(value, name) => {
                return `${name}: ${value.toLocaleString()}`;
              }} />
              <Legend verticalAlign="top" height={36} />
              <Line type="monotone" dataKey="total_packets" stroke="#9f7aea" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="tcp_packets" stroke="#ed8936" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="udp_packets" stroke="#ec4899" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="icmp_packets" stroke="#10b981" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="arp_packets" stroke="#f6ad55" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default HistoricalTraffic;