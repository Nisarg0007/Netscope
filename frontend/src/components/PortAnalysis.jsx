import React, { useEffect, useState } from 'react';
import { getTopSourcePorts, getTopDestinationPorts } from '../services/apiService';

const formatBytes = (bytes = 0) => {
  if (!bytes) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / (1024 ** index)).toFixed(index ? 1 : 0)} ${units[index]}`;
};

const RankingPanel = ({ title, rows, sortBy }) => {
  const valueFor = (row) => sortBy === 'bytes' ? Number(row.total_bytes) || 0 : Number(row.packet_count) || 0;
  const maxValue = Math.max(1, ...rows.map(valueFor));
  return <div className="rank-panel"><div className="rank-panel-heading"><h3>{title}</h3><span>{rows.length} services</span></div><p className="rank-scale-label">Bar length is relative to the highest-ranked port.</p>
    {rows.length ? <div className="rank-list">{rows.map((row, index) => <div className="rank-item" key={`${row.port}-${row.protocol}`}>
      <div className="rank-line"><span className="rank-index">{String(index + 1).padStart(2, '0')}</span><span className="rank-name"><b>{row.common_service || 'Unknown'}</b><small>{row.port}/{String(row.protocol).toUpperCase()}</small></span><b>{sortBy === 'bytes' ? formatBytes(valueFor(row)) : `${valueFor(row).toLocaleString()} pkts`}</b></div>
      <div className="rank-track port-track"><span style={{ width: `${Math.max(2, (valueFor(row) / maxValue) * 100)}%` }} /></div>
      <div className="rank-details"><span>{(row.packet_percentage || 0).toFixed(1)}% packets</span><span>{(row.byte_percentage || 0).toFixed(1)}% bytes</span></div>
    </div>)}</div> : <p className="rank-empty">No {title.toLowerCase()} observed yet.</p>}
  </div>;
};

const PortAnalysis = () => {
  const [sourceData, setSourceData] = useState([]);
  const [destData, setDestData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortBy, setSortBy] = useState('bytes');
  const [limit, setLimit] = useState(10);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const [source, destination] = await Promise.all([getTopSourcePorts(limit, sortBy), getTopDestinationPorts(limit, sortBy)]);
        if (active) { setSourceData(source?.source_ports || []); setDestData(destination?.destination_ports || []); setError(null); }
      } catch (err) { if (active) setError('Failed to load port traffic statistics'); console.error(err); }
      finally { if (active) setLoading(false); }
    };
    load();
    const interval = setInterval(load, 2000);
    return () => { active = false; clearInterval(interval); };
  }, [limit, sortBy]);

  if (loading && !sourceData.length && !destData.length) return <div className="chart-state">Loading service rankings…</div>;
  if (error && !sourceData.length && !destData.length) return <div className="chart-state chart-error">{error}</div>;
  return <div className="analytics-chart-panel">
    <div className="chart-controls"><label>Rank by <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}><option value="bytes">Traffic volume</option><option value="packet_count">Packet count</option></select></label><label>Show <select value={limit} onChange={(event) => setLimit(Number(event.target.value))}><option value="5">5</option><option value="10">10</option><option value="20">20</option><option value="50">50</option></select></label><span className="chart-unit-chip">TCP / UDP</span></div>
    <div className="rank-grid"><RankingPanel title="Top source ports" rows={sourceData} sortBy={sortBy} /><RankingPanel title="Top destination ports" rows={destData} sortBy={sortBy} /></div>
    {error && <p className="chart-inline-error">Refresh failed; showing the latest available sample.</p>}
  </div>;
};

export default PortAnalysis;


