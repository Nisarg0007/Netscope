import React, { useEffect, useState } from 'react';
import { getTopSourceIPs, getTopDestinationIPs } from '../services/apiService';

const IPAnalysis = () => {
  const [sourceData, setSourceData] = useState(null);
  const [destData, setDestData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('bytes'); // 'bytes' or 'packet_count'
  const [limit, setLimit] = useState(10); // default 10

  useEffect(() => {
    const fetchIPData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch both source and destination data in parallel
        const [sourceRes, destRes] = await Promise.all([
          getTopSourceIPs(limit, sortBy),
          getTopDestinationIPs(limit, sortBy)
        ]);
        setSourceData(sourceRes?.source_ips ?? []);
        setDestData(destRes?.destination_ips ?? []);
      } catch (err) {
        setError('Failed to load IP traffic statistics');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchIPData();
    const interval = setInterval(fetchIPData, 2000); // Refresh every 2 seconds
    return () => clearInterval(interval);
  }, [limit, sortBy]);

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading && (!sourceData && !destData)) {
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold text-textPrimary mb-4">
          IP Traffic Analysis
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
          IP Traffic Analysis
        </h2>
        <div className="p-4 bg-statusError/10 border border-statusError rounded">
          <p className="text-statusError">{error}</p>
        </div>
      </div>
    );
  }

  // If no IP data available yet
  const hasSourceData = sourceData && sourceData.length > 0;
  const hasDestData = destData && destData.length > 0;
  if (!hasSourceData && !hasDestData) {
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold text-textPrimary mb-4">
          IP Traffic Analysis
        </h2>
        <div className="p-6 bg-accentPrimary/10 border border-accentPrimary rounded text-center">
          <p className="text-textSecondary">
            No IP traffic data available yet. Start packet capture and generate network traffic.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-textPrimary mb-4">
        IP Traffic Analysis
      </h2>

      {/* Controls */}
      <div className="mb-6 flex flex-wrap items-center gap-4">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-textSecondary">Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-bgCard border border-border rounded px-3 py-1 text-textPrimary focus:outline-none focus:ring-2 focus-ring-accentPrimary"
          >
            <option value="bytes">Total Bytes</option>
            <option value="packet_count">Packet Count</option>
          </select>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-textSecondary">Show:</span>
          <select
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value))}
            className="bg-bgCard border border-border rounded px-3 py-1 text-textPrimary focus:outline-none focus:ring-2 focus-ring-accentPrimary"
          >
            <option value="5">5</option>
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
          </select>
        </div>
      </div>

      {/* Source and Destination Sections */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Source IPs */}
        <div className="bg-bgCard rounded-lg shadow-md p-4">
          <h3 className="text-lg font-semibold text-textPrimary mb-4">
            Top Source IPs
          </h3>
          {hasSourceData ? (
            <div className="space-y-2">
              {sourceData.map((ip, index) => (
                <div key={ip.ip_address} className="border-b pb-2 last:border-b-0">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">#{index + 1} {ip.ip_address}</span>
                    <span className="text-textSecondary">
                      {ip.packet_percentage?.toFixed(1)}% packets
                    </span>
                  </div>
                  <div className="flex justify-between text-xs text-textSecondary mt-1">
                    <span>Packets: {ip.packet_count?.toLocaleString() || '0'}</span>
                    <span>Bytes: {formatBytes(ip.total_bytes || 0)}</span>
                  </div>
                  <div className="flex justify-between text-xs text-textSecondary mt-1">
                    <span>Packet %: {ip.packet_percentage?.toFixed(1)}%</span>
                    <span>Byte %: {ip.byte_percentage?.toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-textSecondary text-center py-4">No source IP data</p>
          )}
        </div>

        {/* Destination IPs */}
        <div className="bg-bgCard rounded-lg shadow-md p-4">
          <h3 className="text-lg font-semibold text-textPrimary mb-4">
            Top Destination IPs
          </h3>
          {hasDestData ? (
            <div className="space-y-2">
              {destData.map((ip, index) => (
                <div key={ip.ip_address} className="border-b pb-2 last:border-b-0">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">#{index + 1} {ip.ip_address}</span>
                    <span className="text-textSecondary">
                      {ip.packet_percentage?.toFixed(1)}% packets
                    </span>
                  </div>
                  <div className="flex justify-between text-xs text-textSecondary mt-1">
                    <span>Packets: {ip.packet_count?.toLocaleString() || '0'}</span>
                    <span>Bytes: {formatBytes(ip.total_bytes || 0)}</span>
                  </div>
                  <div className="flex justify-between text-xs text-textSecondary mt-1">
                    <span>Packet %: {ip.packet_percentage?.toFixed(1)}%</span>
                    <span>Byte %: {ip.byte_percentage?.toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-textSecondary text-center py-4">No destination IP data</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default IPAnalysis;