import React, { useEffect, useState } from 'react';
import { fetchStats } from '../services/apiService';
import { wsService } from '../services/wsService';
import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { formatIstDateTime, formatIstTime, parseUtcTimestamp } from '../utils/timeZone';

const BandwidthDisplay = ({ selectedInterface, captureActive }) => {
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
    if (!selectedInterface || !captureActive) {
      setIsMonitoring(false);
      wsService.disconnect();
      return undefined;
    }

    let effectActive = true;
    setIsMonitoring(true);
    setError(null);
    wsService.resetReconnect();

    const applySample = (data) => {
      if (!effectActive || !data || !data.timestamp) return;
      setStats(data);
      const sampleId = data.timestamp;
      setChartData((previous) => {
        if (previous[previous.length - 1]?.sampleId === sampleId) return previous;
        return [...previous, {
          sampleId,
          timeMs: parseUtcTimestamp(data.timestamp).getTime(),
          download: (Number(data.download_mbps) || 0) * 8,
          upload: (Number(data.upload_mbps) || 0) * 8,
        }].slice(-30);
      });
    };

    const unsubscribe = wsService.subscribe(applySample);
    wsService.connect();

    // Keep the display populated when a browser or local proxy drops WebSocket frames.
    const pollStats = async () => {
      try {
        const data = await fetchStats();
        applySample(data);
      } catch (pollError) {
        console.warn('Bandwidth REST fallback failed:', pollError);
      }
    };
    pollStats();
    const pollInterval = window.setInterval(pollStats, 1000);

    return () => {
      effectActive = false;
      window.clearInterval(pollInterval);
      unsubscribe();
      wsService.disconnect();
    };
  }, [selectedInterface, captureActive]);

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatBitsPerSec = (bytesPerSecond) => {
    const bps = (Number(bytesPerSecond) || 0) * 8;
    if (bps === 0) return '0 bps';
    const kbps = bps / 1000;
    const mbps = kbps / 1000;
    const gbps = mbps / 1000;
    if (gbps >= 1) return `${gbps.toFixed(2)} Gbps`;
    if (mbps >= 1) return `${mbps.toFixed(2)} Mbps`;
    if (kbps >= 1) return `${kbps.toFixed(2)} Kbps`;
    return `${bps.toFixed(0)} bps`;
  };

  if (error) {
    return <div className="p-4 text-statusError">{error}</div>;
  }

  if (!selectedInterface) {
    return <div className="p-4 text-textSecondary">Select an interface to monitor bandwidth</div>;
  }

  return (
    <div className="p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-textPrimary mb-2">Bandwidth Monitoring: {selectedInterface}</h3>
        <p className={`text-sm ${isMonitoring ? 'text-statusSuccess' : 'text-textSecondary'}`}>
          {isMonitoring ? 'Monitoring active' : 'Monitoring stopped'}
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div className="bg-bgCard rounded-lg shadow-md p-4">
          <p className="text-sm font-medium text-textSecondary">Download Speed</p>
          <p className="text-2xl font-bold text-accentPrimary">{formatBitsPerSec(stats.download_bps)}</p>
        </div>
        <div className="bg-bgCard rounded-lg shadow-md p-4">
          <p className="text-sm font-medium text-textSecondary">Upload Speed</p>
          <p className="text-2xl font-bold text-statusSuccess">{formatBitsPerSec(stats.upload_bps)}</p>
        </div>
        <div className="bg-bgCard rounded-lg shadow-md p-4">
          <p className="text-sm font-medium text-textSecondary">Packets/sec</p>
          <p className="text-2xl font-bold text-accentSecondary">
            {Math.round(stats.packet_download_pps + stats.packet_upload_pps)}
          </p>
          <p className="text-xs text-textSecondary/50">
            ↓{Math.round(stats.packet_download_pps)} ↑{Math.round(stats.packet_upload_pps)}
          </p>
        </div>
        <div className="bg-bgCard rounded-lg shadow-md p-4">
          <p className="text-sm font-medium text-textSecondary">Total Received</p>
          <p className="text-2xl font-bold text-accentPrimary">
            {formatBytes(stats.total_bytes_recv)}
          </p>
        </div>
        <div className="bg-bgCard rounded-lg shadow-md p-4">
          <p className="text-sm font-medium text-textSecondary">Total Sent</p>
          <p className="text-2xl font-bold text-accentPrimary">
            {formatBytes(stats.total_bytes_sent)}
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="bg-bgCard rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold text-textPrimary mb-4">Bandwidth Usage (Mbps) - Last 30 Seconds</h3>
        {chartData.length > 0 ? (<div className="bandwidth-chart-container">
          <div className="plot-axis-caption"><span>Y · Throughput (Mbps)</span><span>X · Sample time</span></div><ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <defs><linearGradient id="liveDownloadFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#38c3cd" stopOpacity={0.36} /><stop offset="95%" stopColor="#38c3cd" stopOpacity={0.015} /></linearGradient><linearGradient id="liveUploadFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#8877e8" stopOpacity={0.28} /><stop offset="95%" stopColor="#8877e8" stopOpacity={0.015} /></linearGradient></defs><CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" vertical={false} />
              <XAxis dataKey="timeMs" type="number" scale="time" domain={['dataMin', 'dataMax']} tickFormatter={(value) => formatIstTime(value, { minute: '2-digit', second: '2-digit' })} tick={{ fill: 'var(--chart-muted)', fontSize: 11 }} axisLine={false} tickLine={false} minTickGap={24} />
              <YAxis unit=" Mbps" tick={{ fill: 'var(--chart-muted)', fontSize: 11 }} axisLine={false} tickLine={false} width={70} />
              <Tooltip labelFormatter={(value) => formatIstDateTime(value)} formatter={(value, name) => [`${Number(value).toFixed(3)} Mbps`, name === 'download' ? 'Download' : 'Upload']} contentStyle={{ background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: 10, color: 'var(--ink)' }} />
              <Legend verticalAlign="top" height={36} />
              <Area type="monotone" dataKey="download" name="Download" stroke="#38c3cd" strokeWidth={2.5} fill="url(#liveDownloadFill)" dot={false} activeDot={{ r: 4 }} />
              <Area type="monotone" dataKey="upload" name="Upload" stroke="#8877e8" strokeWidth={2.5} fill="url(#liveUploadFill)" dot={false} activeDot={{ r: 4 }} />
            </AreaChart>
          </ResponsiveContainer></div>
        ) : (
          <p className="text-textSecondary">Collecting data for chart...</p>
        )}
      </div>

      {/* Detailed Statistics */}
      <div className="mt-6 p-4 bg-accentPrimary/10 rounded-lg">
        <h4 className="font-semibold text-textPrimary mb-2">Detailed Statistics</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span>Download Rate:</span>
            <span className="font-mono text-textPrimary">{formatBitsPerSec(stats.download_bps)}</span>
          </div>
          <div className="flex justify-between">
            <span>Upload Rate:</span>
            <span className="font-mono text-textPrimary">{formatBitsPerSec(stats.upload_bps)}</span>
          </div>
          <div className="flex justify-between">
            <span>Packet Download Rate:</span>
            <span className="font-mono text-textPrimary">{stats.packet_download_pps.toFixed(1)} pps</span>
          </div>
          <div className="flex justify-between">
            <span>Packet Upload Rate:</span>
            <span className="font-mono text-textPrimary">{stats.packet_upload_pps.toFixed(1)} pps</span>
          </div>
          <div className="flex justify-between">
            <span>Total Received:</span>
            <span className="font-mono text-textPrimary">{formatBytes(stats.total_bytes_recv)}</span>
          </div>
          <div className="flex justify-between">
            <span>Total Sent:</span>
            <span className="font-mono text-textPrimary">{formatBytes(stats.total_bytes_sent)}</span>
          </div>
          <div className="flex justify-between">
            <span>Packets Received:</span>
            <span className="font-mono text-textPrimary">{stats.total_packets_recv.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span>Packets Sent:</span>
            <span className="font-mono text-textPrimary">{stats.total_packets_sent.toLocaleString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BandwidthDisplay;











