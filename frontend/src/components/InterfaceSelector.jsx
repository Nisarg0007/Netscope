import React, { useEffect, useState } from 'react';
import { fetchInterfaces } from '../services/apiService';

const formatBytes = (value = 0) => {
  const bytes = Number(value) || 0;
  if (bytes < 1024) return `${bytes} B`;
  const units = ['KB', 'MB', 'GB', 'TB'];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)) - 1, units.length - 1);
  return `${(bytes / (1024 ** (index + 1))).toFixed(1)} ${units[index]}`;
};

const InterfaceSelector = ({ onInterfaceSelect, analysisActive = false, starting = false }) => {
  const [interfaces, setInterfaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedInterface, setSelectedInterface] = useState(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [startingLocal, setStartingLocal] = useState(false);
  const [inactiveInterface, setInactiveInterface] = useState(null);

  useEffect(() => {
    const loadInterfaces = async () => {
      try {
        setLoading(true);
        const data = await fetchInterfaces();
        setInterfaces(data.interfaces || []);
      } catch (err) {
        setError('Failed to load network interfaces. Check that the NetScope API is running.');
        console.error(err);
      } finally { setLoading(false); }
    };
    loadInterfaces();
  }, []);

  const selectedIsActive = interfaces.some((iface) => iface.name === selectedInterface && String(iface.status).toLowerCase() === 'up');

  const dismissInactiveWarning = () => {
    setInactiveInterface(null);
    setSelectedInterface(null);
  };
  const confirmAnalysis = async () => {
    if (!selectedInterface || !selectedIsActive || starting || startingLocal) return;
    setStartingLocal(true);
    try {
      await onInterfaceSelect(selectedInterface);
      setConfirmOpen(false);
    } catch (err) {
      // Parent displays the API error; keep the confirmation available for retry.
      console.error(err);
    } finally { setStartingLocal(false); }
  };

  if (loading) return <div className="interface-loading"><span className="loading-orbit" /> Loading available interfaces…</div>;
  if (error) return <div className="interface-error" role="alert"><b>Could not load adapters</b><span>{error}</span><button onClick={() => window.location.reload()}>Retry</button></div>;

  return <div className="interface-selector">
    <div className="interface-list-heading"><span>AVAILABLE ADAPTERS <b>{interfaces.length}</b></span><span>SELECT ONE TO CONTINUE</span></div>
    {interfaces.length === 0 ? <div className="no-interfaces"><span>⌘</span><b>No network interfaces found</b><p>Check that your computer has an enabled network adapter, then reload this page.</p></div> : <div className="interface-list">
      {interfaces.map((iface) => {
        const selected = selectedInterface === iface.name;
        const up = String(iface.status).toLowerCase() === 'up';
        return <button type="button" key={iface.name} className={`interface-option ${selected ? 'selected' : ''}`} onClick={() => { setSelectedInterface(selected ? null : iface.name); if (!selected && !up) setInactiveInterface(iface.name); else setInactiveInterface(null); }} aria-pressed={selected}>
          <span className={`adapter-glyph ${up ? 'adapter-up' : ''}`}>⌘</span>
          <span className="adapter-main"><span className="adapter-title"><b>{iface.name}</b><span className={`adapter-status ${up ? 'is-up' : 'is-down'}`}><i />{up ? 'ACTIVE' : 'DOWN'}</span></span><span className="adapter-meta">IPv4 <b>{iface.ipv4 || '—'}</b><span className="meta-divider">·</span> MAC <b>{iface.mac || '—'}</b></span><span className="adapter-meta adapter-ipv6">IPv6 <b>{iface.ipv6 || '—'}</b></span></span>
          <span className="adapter-counters"><span><small>↑ SENT</small><b>{formatBytes(iface.bytes_sent)}</b></span><span><small>↓ RECEIVED</small><b>{formatBytes(iface.bytes_received)}</b></span></span>
          <span className={`adapter-radio ${selected ? 'checked' : ''}`}>{selected ? '✓' : ''}</span>
        </button>;
      })}
    </div>}
    <div className="selection-footer"><span><i /> Traffic analysis starts only after confirmation.</span><button className="confirm-analysis-button" disabled={!selectedInterface || !selectedIsActive || starting || startingLocal || analysisActive} onClick={() => setConfirmOpen(true)}>{starting || startingLocal ? 'Starting…' : 'Choose'}</button></div>
    {confirmOpen && <div className="confirm-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !startingLocal) setConfirmOpen(false); }}><section className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-title"><button className="confirm-close" onClick={() => setConfirmOpen(false)} aria-label="Close" disabled={startingLocal}>×</button><div className="confirm-symbol">⌁</div><div className="section-overline">START CAPTURE</div><h2 id="confirm-title">Analyze this interface?</h2><p>NetScope will begin monitoring traffic on the selected adapter and open the analysis workspace.</p><div className="confirm-adapter"><span className="status-dot online" /><span><small>SELECTED INTERFACE</small><b>{selectedInterface}</b></span></div><div className="confirm-actions"><button className="cancel-confirm" onClick={() => setConfirmOpen(false)} disabled={startingLocal}>Go back</button><button className="confirm-start" onClick={confirmAnalysis} disabled={starting || startingLocal}>{starting || startingLocal ? 'Starting analysis…' : 'Start analysis'} <span>→</span></button></div></section></div>}
  {inactiveInterface && <div className="confirm-backdrop inactive-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) dismissInactiveWarning(); }}><section className="confirm-dialog inactive-dialog" role="alertdialog" aria-modal="true" aria-labelledby="inactive-title"><button className="confirm-close" onClick={dismissInactiveWarning} aria-label="Close">×</button><div className="inactive-symbol">!</div><div className="section-overline">INTERFACE UNAVAILABLE</div><h2 id="inactive-title">This interface is not active</h2><p><b>{inactiveInterface}</b> is currently not active. Select an interface marked <strong>ACTIVE</strong> to begin network analysis.</p><button className="inactive-choose-button" onClick={dismissInactiveWarning}>Choose an active interface</button></section></div>}
  </div>;
};

export default InterfaceSelector;




