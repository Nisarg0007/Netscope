import React, { useEffect, useMemo, useState } from 'react';
import { getProtocolStats } from '../services/apiService';
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const ProtocolAnalysis = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const data = await getProtocolStats();
        if (active) { setStats(data); setError(null); }
      } catch (err) {
        if (active) setError('Failed to load protocol statistics');
        console.error(err);
      } finally { if (active) setLoading(false); }
    };
    load();
    const interval = setInterval(load, 2000);
    return () => { active = false; clearInterval(interval); };
  }, []);

  const rows = useMemo(() => Object.entries(stats?.protocols || {}).map(([name, value]) => ({
    name: name.toUpperCase(),
    packets: Number(value.packet_count) || 0,
    bytes: Number(value.byte_count) || 0,
    packetShare: Number(value.packet_percentage) || 0,
    byteShare: Number(value.byte_percentage) || 0,
  })).filter((item) => item.packets || item.bytes).sort((a, b) => b.packets - a.packets), [stats]);

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    return `${(bytes / (1024 ** index)).toFixed(index ? 1 : 0)} ${units[index]}`;
  };

  if (loading) return <div className="chart-state">Loading protocol distribution…</div>;
  if (error) return <div className="chart-state chart-error">{error}</div>;
  if (!rows.length) return <div className="chart-state">No packet data yet. Generate traffic while capture is active.</div>;

  const overall = stats?.overall || {};
  return <div className="analytics-chart-panel">
    <div className="chart-summary-strip">
      <div><span>TOTAL PACKETS</span><b>{(overall.total_packets || 0).toLocaleString()}</b></div>
      <div><span>CAPTURED DATA</span><b>{formatBytes(overall.total_bytes || 0)}</b></div>
      <div><span>PACKETS / SEC</span><b>{Number(overall.packets_per_second || 0).toFixed(1)}</b></div>
      <div><span>AVG. PACKET</span><b>{Math.round(overall.average_packet_size || 0)} B</b></div>
    </div>
    <div className="chart-title-row"><div><h3>Protocol share</h3><p>Packet share and byte share, ranked by packet volume</p></div><span className="chart-unit-chip">SHARE (%)</span></div>
    <div className="plot-axis-caption"><span>Y · Protocol</span><span>X · Share of packets or bytes (%)</span></div>
    <div className="bar-chart-wrap" style={{ height: Math.max(245, rows.length * 54) }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} layout="vertical" margin={{ top: 6, right: 24, bottom: 4, left: 0 }} barCategoryGap="24%">
          <CartesianGrid horizontal={false} stroke="var(--chart-grid)" />
          <XAxis type="number" domain={[0, 100]} tickFormatter={(value) => `${value}%`} tick={{ fill: 'var(--chart-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis type="category" dataKey="name" width={70} tick={{ fill: 'var(--chart-text)', fontSize: 12, fontWeight: 600 }} axisLine={false} tickLine={false} />
          <Tooltip formatter={(value, name, context) => [`${Number(value).toFixed(1)}% · ${name === 'Packets' ? context.payload.packets.toLocaleString() + ' packets' : formatBytes(context.payload.bytes)}`, name]} contentStyle={{ background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: 10, color: 'var(--ink)' }} />
          <Legend />
          <Bar dataKey="packetShare" name="Packets" fill="#38c3cd" radius={[0, 5, 5, 0]} maxBarSize={14} />
          <Bar dataKey="byteShare" name="Bytes" fill="#8877e8" radius={[0, 5, 5, 0]} maxBarSize={14} />
        </BarChart>
      </ResponsiveContainer>
    </div>
    <div className="protocol-detail-grid">{rows.map((item) => <div className="protocol-detail" key={item.name}><b>{item.name}</b><span>{item.packets.toLocaleString()} packets · {formatBytes(item.bytes)}</span></div>)}</div>
  </div>;
};

export default ProtocolAnalysis;


