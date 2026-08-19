import React, { useEffect, useState } from 'react';
import { getProtocolStats } from '../services/apiService';

const ProtocolAnalysis = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProtocolData = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getProtocolStats();
        setStats(data);
      } catch (err) {
        setError('Failed to load protocol statistics');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchProtocolData();
    const interval = setInterval(fetchProtocolData, 2000); // Refresh every 2 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold text-textPrimary mb-4">
          Protocol Traffic Analysis
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
          Protocol Traffic Analysis
        </h2>
        <div className="p-4 bg-statusError/10 border border-statusError rounded">
          <p className="text-statusError">{error}</p>
        </div>
      </div>
    );
  }

  // If no packet data available yet
  if (!stats || !stats.overall || (stats.overall.total_packets === 0 && stats.overall.total_bytes === 0)) {
    return (
      <div className="p-6">
        <h2 className="text-xl font-semibold text-textPrimary mb-4">
          Protocol Traffic Analysis
        </h2>
        <div className="p-6 bg-accentPrimary/10 border border-accentPrimary rounded text-center">
          <p className="text-textSecondary">
            No packet data available yet. Start packet capture and generate network traffic.
          </p>
        </div>
      </div>
    );
  }

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold text-textPrimary mb-4">
        Protocol Traffic Analysis
      </h2>

      {/* Protocol Summary */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-textPrimary mb-4">
          Protocol Summary
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-bgCard rounded-lg shadow-md p-4">
            <p className="text-sm font-medium text-textSecondary">Total Packets</p>
            <p className="text-2xl font-bold text-textPrimary">
              {((stats?.overall ?? {}).total_packets ?? 0).toLocaleString()}
            </p>
          </div>
          <div className="bg-bgCard rounded-lg shadow-md p-4">
            <p className="text-sm font-medium text-textSecondary">Total Bytes</p>
            <p className="text-2xl font-bold text-textPrimary">
              {formatBytes(((stats?.overall ?? {}).total_bytes ?? 0))}
            </p>
          </div>
          <div className="bg-bgCard rounded-lg shadow-md p-4">
            <p className="text-sm font-medium text-textSecondary">Packets/sec</p>
            <p className="text-2xl font-bold text-textPrimary">
              {Math.round(((stats?.overall ?? {}).packets_per_second ?? 0))}
            </p>
          </div>
          <div className="bg-bgCard rounded-lg shadow-md p-4">
            <p className="text-sm font-medium text-textSecondary">Avg Packet Size</p>
            <p className="text-2xl font-bold text-textPrimary">
              {Math.round(((stats?.overall ?? {}).average_packet_size ?? 0))} B
            </p>
          </div>
        </div>
      </div>

      {/* Protocol Distribution */}
      <div className="">
        <h3 className="text-lg font-semibold text-textPrimary mb-4">
          Protocol Distribution
        </h3>
        <div className="space-y-4">
          {Object.entries(stats.protocols ?? {}).map(([name, protocol]) => (
            <div key={name} className="bg-bgCard rounded-lg shadow-md p-4">
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium text-textPrimary">{name}</h4>
                <span className="px-2 py-1 bg-textSecondary/20 text-xs rounded">
                  {((protocol?.packet_percentage) ?? 0).toFixed(1)}% packets
                </span>
              </div>

              {/* Packet Percentage Bar */}
              <div className="mb-2">
                <div className="flex justify-between text-xs text-textSecondary mb-1">
                  <span>Packet Percentage</span>
                  <span>{((protocol?.packet_percentage) ?? 0).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-textSecondary/20 rounded-full h-2.5">
                  <div
                    className="bg-accentPrimary h-2.5 rounded-full"
                    style={{ width: `${((protocol?.packet_percentage) ?? 0)}%` }}
                  ></div>
                </div>
              </div>

              {/* Byte Percentage Bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-textSecondary mb-1">
                  <span>Byte Percentage</span>
                  <span>{((protocol?.byte_percentage) ?? 0).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-textSecondary/20 rounded-full h-2.5">
                  <div
                    className="bg-statusSuccess h-2.5 rounded-full"
                    style={{ width: `${((protocol?.byte_percentage) ?? 0)}%` }}
                  ></div>
                </div>
              </div>

              {/* Details */}
              <div className="mt-2 text-sm text-textSecondary space-y-1">
                <div>
                  <span className="font-medium">Packets:</span> {((protocol?.packet_count) ?? 0).toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Bytes:</span> {formatBytes(protocol.byte_count ?? 0)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ProtocolAnalysis;