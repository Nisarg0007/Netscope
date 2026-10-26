import React, { useEffect, useMemo, useState } from 'react';
import { getHistory, clearHistory } from '../services/apiService';
import { Area, AreaChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const RANGE_MS = { '1h': 60 * 60 * 1000, '6h': 6 * 60 * 60 * 1000, '24h': 24 * 60 * 60 * 1000, '7d': 7 * 24 * 60 * 60 * 1000 };

const HistoricalTraffic = () => {
  const [snapshots, setSnapshots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [limit, setLimit] = useState(500);
  const [range, setRange] = useState('24h');

  const formatBytes = (bytes = 0) => {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    return `${(bytes / (1024 ** index)).toFixed(index ? 1 : 0)} ${units[index]}`;
  };

  // Stored history rates are bytes/s; convert to bits/s before assigning network units.
  const formatBandwidth = (bytesPerSecond = 0) => {
    const bps = (Number(bytesPerSecond) || 0) * 8;
    if (bps >= 1e9) return `${(bps / 1e9).toFixed(2)} Gbps`;
    if (bps >= 1e6) return `${(bps / 1e6).toFixed(2)} Mbps`;
    if (bps >= 1e3) return `${(bps / 1e3).toFixed(2)} Kbps`;
    return `${bps.toFixed(0)} bps`;
  };

  const formatTimestamp = (isoString) => {
    if (!isoString) return '';
    return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const formatAxisTime = (value) => new Date(value).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  const formatPacketTick = (value) => {
    const count = Number(value) || 0;
    if (count >= 1_000_000) return `${(count / 1_000_000).toFixed(1).replace(/\.0$/, '')}M`;
    if (count >= 1_000) return `${(count / 1_000).toFixed(0)}k`;
    return count.toLocaleString();
  };

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const startTime = range === 'all' ? null : new Date(Date.now() - RANGE_MS[range]).toISOString();
        const data = await getHistory(limit, startTime);
        if (active) { setSnapshots(data.snapshots || []); setError(null); }
      } catch (err) { if (active) setError('Failed to load historical traffic data'); console.error(err); }
      finally { if (active) setLoading(false); }
    };
    setLoading(true);
    load();
    const interval = setInterval(load, 5000);
    return () => { active = false; clearInterval(interval); };
  }, [limit, range]);

  const sortedSnapshots = useMemo(() => [...snapshots].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp)), [snapshots]);
  const latest = sortedSnapshots[sortedSnapshots.length - 1];
  const chartData = useMemo(() => sortedSnapshots.map((row) => ({
    ...row,
    timeMs: new Date(row.timestamp).getTime(),
    download_mbps: (Number(row.download_rate) || 0) * 8 / 1e6,
    upload_mbps: (Number(row.upload_rate) || 0) * 8 / 1e6,
  })), [sortedSnapshots]);

  const handleClearHistory = async () => {
    if (!window.confirm('Are you sure you want to clear all historical traffic data? This cannot be undone.')) return;
    try { await clearHistory(); setSnapshots([]); }
    catch (err) { setError('Failed to clear history'); console.error(err); }
  };

  if (loading && snapshots.length === 0) return <div className="chart-state">Loading historical traffic…</div>;
  if (error && snapshots.length === 0) return <div className="chart-state chart-error">{error}</div>;

  return <div className="analytics-chart-panel">
    <div className="chart-controls">
      <label>Time range <select value={range} onChange={(event) => setRange(event.target.value)}><option value="1h">Last hour</option><option value="6h">Last 6 hours</option><option value="24h">Last 24 hours</option><option value="7d">Last 7 days</option><option value="all">All history</option></select></label>
      <label>Max samples <select value={limit} onChange={(event) => setLimit(Number(event.target.value))}><option value="50">50</option><option value="100">100</option><option value="500">500</option><option value="1000">1000</option></select></label>
      <span className="chart-unit-chip">{snapshots.length} SAMPLES</span>
      <button onClick={handleClearHistory} className="history-clear-button">Clear history</button>
    </div>
    <div className="chart-summary-strip">
      <div><span>SNAPSHOTS</span><b>{snapshots.length.toLocaleString()}</b></div>
      <div><span>LATEST DOWNLOAD</span><b>{latest ? formatBandwidth(latest.download_rate) : '—'}</b></div>
      <div><span>LATEST UPLOAD</span><b>{latest ? formatBandwidth(latest.upload_rate) : '—'}</b></div>
      <div><span>LAST SAMPLE</span><b>{latest ? new Date(latest.timestamp).toLocaleString() : '—'}</b></div>
    </div>
    {!chartData.length ? <div className="chart-state">No samples in this time range. Choose a wider range or continue capturing traffic.</div> : <>
      <div className="history-chart-card">
        <div className="chart-title-row"><div><h3>Throughput over time</h3><p>Download and upload rate · Mbps</p></div><span className="chart-unit-chip">BITS / SEC</span></div>
        <div className="plot-axis-caption"><span>Y · Throughput (Mbps)</span><span>X · Sample time</span></div><div className="history-graph"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chartData} margin={{ top: 12, right: 18, bottom: 4, left: 8 }}>
          <defs><linearGradient id="historyDownloadFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#38c3cd" stopOpacity={0.34} /><stop offset="95%" stopColor="#38c3cd" stopOpacity={0.015} /></linearGradient><linearGradient id="historyUploadFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#8877e8" stopOpacity={0.28} /><stop offset="95%" stopColor="#8877e8" stopOpacity={0.015} /></linearGradient></defs>
          <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 5" vertical={false} />
          <XAxis dataKey="timeMs" type="number" scale="time" domain={['dataMin', 'dataMax']} tickFormatter={formatTimestamp} tick={{ fill: 'var(--chart-muted)', fontSize: 11 }} axisLine={false} tickLine={false} minTickGap={30} />
          <YAxis unit=" Mbps" domain={[0, 'auto']} tick={{ fill: 'var(--chart-muted)', fontSize: 11 }} axisLine={false} tickLine={false} width={75} />
          <Tooltip labelFormatter={(value) => new Date(value).toLocaleString()} formatter={(value, name) => [`${Number(value).toFixed(3)} Mbps`, name === 'download_mbps' ? 'Download' : 'Upload']} contentStyle={{ background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: 10, color: 'var(--ink)' }} />
          <Legend />
          <Area type="monotone" dataKey="download_mbps" name="Download" stroke="#38c3cd" strokeWidth={2.5} fill="url(#historyDownloadFill)" dot={false} activeDot={{ r: 4 }} />
          <Area type="monotone" dataKey="upload_mbps" name="Upload" stroke="#8877e8" strokeWidth={2.5} fill="url(#historyUploadFill)" dot={false} activeDot={{ r: 4 }} />
        </AreaChart></ResponsiveContainer></div>
      </div>
      <div className="history-chart-card">
        <div className="chart-title-row"><div><h3>Packet activity over time</h3><p>Captured packet totals by protocol</p></div><span className="chart-unit-chip">PACKETS</span></div>
        <div className="plot-axis-caption"><span>Y · Packet count</span><span>X · Sample time</span></div><div className="history-graph packet-history-graph"><ResponsiveContainer width="100%" height="100%"><LineChart data={chartData} margin={{ top: 10, right: 16, bottom: 2, left: 4 }}>
          <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 5" vertical={false} />
          <XAxis dataKey="timeMs" type="number" scale="time" domain={['dataMin', 'dataMax']} tickFormatter={formatAxisTime} tick={{ fill: 'var(--chart-muted)', fontSize: 11 }} axisLine={false} tickLine={false} tickCount={5} interval="preserveStartEnd" minTickGap={72} height={30} />
          <YAxis allowDecimals={false} tickFormatter={formatPacketTick} tick={{ fill: 'var(--chart-muted)', fontSize: 11 }} axisLine={false} tickLine={false} width={54} />
          <Tooltip labelFormatter={(value) => new Date(value).toLocaleString()} formatter={(value, name) => [Number(value).toLocaleString(), name]} contentStyle={{ background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: 10, color: 'var(--ink)' }} />
          <Legend content={() => <div className="tidy-chart-legend">{[{ name: 'Total', color: '#8877e8' }, { name: 'TCP', color: '#f1a34a' }, { name: 'UDP', color: '#e56ba5' }, { name: 'ICMP', color: '#39bd8a' }, { name: 'ARP', color: '#38c3cd' }].map((item) => <span key={item.name}><i style={{ backgroundColor: item.color }} />{item.name}</span>)}</div>} />
          <Line type="monotone" dataKey="total_packets" name="Total" stroke="#8877e8" strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
          <Line type="monotone" dataKey="tcp_packets" name="TCP" stroke="#f1a34a" strokeWidth={2} dot={false} activeDot={{ r: 3 }} />
          <Line type="monotone" dataKey="udp_packets" name="UDP" stroke="#e56ba5" strokeWidth={2} dot={false} activeDot={{ r: 3 }} />
          <Line type="monotone" dataKey="icmp_packets" name="ICMP" stroke="#39bd8a" strokeWidth={2} dot={false} activeDot={{ r: 3 }} />
          <Line type="monotone" dataKey="arp_packets" name="ARP" stroke="#38c3cd" strokeWidth={2} dot={false} activeDot={{ r: 3 }} />
        </LineChart></ResponsiveContainer></div>
      </div>
    </>}
  </div>;
};

export default HistoricalTraffic;


