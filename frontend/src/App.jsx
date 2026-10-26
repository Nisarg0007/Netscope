import React, { useState, useEffect, useRef } from 'react';
import { fetchHealth, selectInterface, deselectInterface } from './services/apiService';
import InterfaceSelector from './components/InterfaceSelector';
import BandwidthDisplay from './components/BandwidthDisplay';
import ProtocolAnalysis from './components/ProtocolAnalysis';
import IPAnalysis from './components/IPAnalysis';
import PortAnalysis from './components/PortAnalysis';
import HistoricalTraffic from './components/HistoricalTraffic';
import './index.css';

const analysisPages = [
  { id: 'bandwidth', label: 'Live bandwidth', icon: '⌁', title: 'Bandwidth monitor', overline: 'LIVE TELEMETRY', description: 'Real-time throughput and packet activity for the selected adapter.' },
  { id: 'protocols', label: 'Protocols', icon: '◈', title: 'Protocol analysis', overline: 'TRAFFIC COMPOSITION', description: 'Breakdown of observed network protocols.' },
  { id: 'ip-analysis', label: 'IP analytics', icon: '◎', title: 'IP analytics', overline: 'ADDRESS INTELLIGENCE', description: 'Source and destination address activity.' },
  { id: 'port-analysis', label: 'Port activity', icon: '⇄', title: 'Port activity', overline: 'SERVICE ACTIVITY', description: 'Source and destination ports observed in traffic.' },
  { id: 'history', label: 'Traffic history', icon: '◷', title: 'Traffic history', overline: 'HISTORICAL REVIEW', description: 'Explore recorded network snapshots over time.' },
];

function App() {
  const [backendStatus, setBackendStatus] = useState('Checking API');
  const [isConnected, setIsConnected] = useState(false);
  const [selectedInterface, setSelectedInterface] = useState(null);
  const [analysisActive, setAnalysisActive] = useState(false);
  const [captureActive, setCaptureActive] = useState(false);
  const [resuming, setResuming] = useState(false);
  const [resumeError, setResumeError] = useState('');
  const [activePage, setActivePage] = useState('bandwidth');
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState('');
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') === 'light' ? 'light' : 'dark');
  const analysisContentRef = useRef(null);
  const sidebarRef = useRef(null);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const data = await fetchHealth();
        setBackendStatus(data.status === 'healthy' ? 'Systems operational' : `API ${data.status}`);
        setIsConnected(true);
      } catch {
        setBackendStatus('API unavailable');
        setIsConnected(false);
      }
    };
    checkBackend();
    const interval = setInterval(checkBackend, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const syncTheme = () => setTheme(document.documentElement.classList.contains('dark') ? 'dark' : 'light');
    const observer = new MutationObserver(syncTheme);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    syncTheme();
    return () => observer.disconnect();
  }, []);

  const startAnalysis = async (interfaceName) => {
    setStarting(true);
    setStartError('');
    try {
      await selectInterface(interfaceName);
      setSelectedInterface(interfaceName);
      setAnalysisActive(true);
      setCaptureActive(true);
      setActivePage('bandwidth');
    } catch (error) {
      setStartError(error.message || 'Could not start analysis. Check the backend connection and try again.');
      throw error;
    } finally {
      setStarting(false);
    }
  };

  const stopAnalysis = async () => {
    try {
      await deselectInterface();
    } catch (error) {
      console.error('Failed to stop backend monitoring:', error);
    } finally {
      setCaptureActive(false);
    }
  };

  const continueAnalysis = async () => {
    if (!selectedInterface || captureActive || resuming) return;
    setResuming(true);
    setResumeError('');
    try {
      await selectInterface(selectedInterface);
      setCaptureActive(true);
    } catch (error) {
      setResumeError(error.message || 'Could not resume capture. Check that the interface is still active.');
    } finally {
      setResuming(false);
    }
  };
  const goHome = () => {
    setAnalysisActive(false);
    setSelectedInterface(null);
    setActivePage('bandwidth');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const navigateToPage = (pageId) => {
    setActivePage(pageId);
    const section = document.getElementById(pageId);
    if (!section) return;
    const headerHeight = document.querySelector('.topbar')?.getBoundingClientRect().height || 0;
    const targetTop = Math.max(0, window.scrollY + section.getBoundingClientRect().top - headerHeight - 8);
    window.scrollTo({ top: targetTop, behavior: 'smooth' });
  };

  useEffect(() => {
    if (!analysisActive || !analysisContentRef.current) return undefined;
    const sections = analysisContentRef.current.querySelectorAll('.analysis-page-content');
    const observer = new IntersectionObserver((entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible) setActivePage(visible.target.id);
    }, { rootMargin: '-18% 0px -48% 0px', threshold: [0, 0.15, 0.3, 0.5, 0.7] });
    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, [analysisActive]);

  useEffect(() => {
    if (analysisActive) requestAnimationFrame(() => document.getElementById('bandwidth')?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
  }, [analysisActive]);


  useEffect(() => {
    const sidebar = sidebarRef.current;
    if (!analysisActive || !sidebar) return undefined;
    const preventPageWheel = (event) => event.preventDefault();
    sidebar.addEventListener('wheel', preventPageWheel, { passive: false, capture: true });
    return () => sidebar.removeEventListener('wheel', preventPageWheel, { capture: true });
  }, [analysisActive]);

  const toggleTheme = () => window.toggleTheme?.();
  const now = new Intl.DateTimeFormat(undefined, { weekday: 'short', month: 'short', day: 'numeric' }).format(new Date());
  const page = analysisPages.find((item) => item.id === activePage) || analysisPages[0];

  return (
    <div className={`app-shell ${analysisActive ? 'analysis-mode' : 'selection-mode'}`}>
      {analysisActive && <aside className="sidebar" ref={sidebarRef}>
        <a className="brand" href="#overview" aria-label="NetScope home" onClick={(event) => { event.preventDefault(); navigateToPage('bandwidth'); }}>
          <span className="brand-mark"><span /><span /><span /></span>
          <span className="brand-name">net<span>scope</span><small>NETWORK INTELLIGENCE</small></span>
        </a>
        <div className="nav-label">ANALYSIS</div>
        <div className="active-adapter"><span className="status-dot online" /><span><small>CAPTURING ON</small><b title={selectedInterface}>{selectedInterface}</b></span></div>
        <div className="nav-label nav-label-spaced">INSPECTION PAGES</div>
        {analysisPages.map((item) => <button key={item.id} className={`nav-link ${activePage === item.id ? 'active' : ''}`} onClick={() => navigateToPage(item.id)}><span className="nav-icon">{item.icon}</span>{item.label}{activePage === item.id && <span className="nav-indicator" />}</button>)}
        <div className="sidebar-bottom">
          <div className="sidebar-status"><span className={`status-dot ${isConnected ? 'online' : 'offline'}`} /><span><b>{isConnected ? 'API connected' : 'API disconnected'}</b><small>{isConnected ? 'Monitoring services ready' : 'Check backend on port 8004'}</small></span></div>
        </div>
      </aside>}

      <main className="main-panel" id="overview">
        <header className="topbar"><div className="topbar-right">
          {analysisActive && <button className="stop-analysis-button topbar-stop-button" onClick={stopAnalysis} disabled={!captureActive} title={captureActive ? 'Stop packet capture and keep this analysis open' : 'Capture has stopped'}><span className="stop-square">■</span> Stop analysis</button>}{analysisActive && !captureActive && <><span className="review-mode-pill"><i /> REVIEW MODE</span><button className="continue-analysis-button" onClick={continueAnalysis} disabled={resuming}>▶ <span>{resuming ? 'Resuming…' : 'Continue analysis'}</span></button><button className="home-analysis-button" onClick={goHome}>⌂ <span>Back to interfaces</span></button></>}
          <span className={`connection-pill ${isConnected ? 'connected' : 'disconnected'}`}><i />{backendStatus}</span>
          <button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle theme">{theme === 'dark' ? '☼' : '☾'}</button>
          <span className="date-label">{now}</span>
        </div></header>
        <div className="page-content">
          {!analysisActive ? <>
            <section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-line" /> NETWORK OPERATIONS CENTER</div><h1>Select an interface</h1><p className="page-subtitle">Choose a network adapter to inspect its live traffic and activity.</p></div><div className="live-indicator setup-indicator"><span className={`status-dot ${isConnected ? 'online' : 'offline'}`} /> API {isConnected ? 'READY' : 'OFFLINE'}</div></section>
            <section className="selection-intro"><div className="selection-step">01</div><div><b>Choose your capture source</b><p>Select an active interface. NetScope will ask you to confirm before analysis begins.</p></div></section>
            {startError && <div className="start-error" role="alert">{startError}</div>}
            <div className="module-card interface-card selection-page"><InterfaceSelector onInterfaceSelect={startAnalysis} onInterfaceDeselect={() => {}} analysisActive={false} starting={starting} /></div>
          </> : <>
            <section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-line" /> NETWORK OPERATIONS CENTER</div><h1>Network analysis</h1><p className="page-subtitle">{captureActive ? 'Live network telemetry from' : 'Reviewing captured results from'} <span className="active-interface-inline">{selectedInterface}</span>.</p></div><div className={`live-indicator ${captureActive ? '' : 'review-indicator'}`}>{captureActive ? <><span className="live-pulse" /> ANALYSIS ACTIVE</> : <><span className="review-dot" /> REVIEW MODE</>}</div></section>
            <section className="analysis-context"><span className="summary-icon cyan">{page.icon}</span><span><small>CURRENT CAPTURE INTERFACE</small><b>{selectedInterface}</b></span><span className="context-active-factor">{page.label}</span></section>
            {resumeError && <div className="start-error resume-error" role="alert">{resumeError}</div>}
            <div ref={analysisContentRef} className="analysis-sections">
              <section id="bandwidth" className="analysis-page-content" aria-label="Bandwidth monitor"><div className="section-heading"><div><div className="section-overline">{analysisPages[0].overline}</div><h2>{analysisPages[0].title}</h2><p>{analysisPages[0].description}</p></div><span className={`section-tag ${captureActive ? 'live-tag' : 'review-tag'}`}>{captureActive && <i />}{captureActive ? 'STREAMING' : 'CAPTURE STOPPED'}</span></div><div className="module-card bandwidth-card"><BandwidthDisplay selectedInterface={selectedInterface} captureActive={captureActive} /></div></section>
              <section id="protocols" className="analysis-page-content" aria-label="Protocol analysis"><div className="section-heading"><div><div className="section-overline">{analysisPages[1].overline}</div><h2>{analysisPages[1].title}</h2><p>{analysisPages[1].description}</p></div><span className="section-tag">LAYER 4</span></div><div className="module-card"><ProtocolAnalysis /></div></section>
              <section id="ip-analysis" className="analysis-page-content" aria-label="IP analytics"><div className="section-heading"><div><div className="section-overline">{analysisPages[2].overline}</div><h2>{analysisPages[2].title}</h2><p>{analysisPages[2].description}</p></div><span className="section-tag">IP</span></div><div className="module-card"><IPAnalysis /></div></section>
              <section id="port-analysis" className="analysis-page-content" aria-label="Port activity"><div className="section-heading"><div><div className="section-overline">{analysisPages[3].overline}</div><h2>{analysisPages[3].title}</h2><p>{analysisPages[3].description}</p></div><span className="section-tag">PORTS</span></div><div className="module-card"><PortAnalysis /></div></section>
              <section id="history" className="analysis-page-content" aria-label="Traffic history"><div className="section-heading"><div><div className="section-overline">{analysisPages[4].overline}</div><h2>{analysisPages[4].title}</h2><p>{analysisPages[4].description}</p></div><span className="section-tag">ARCHIVE</span></div><div className="module-card"><HistoricalTraffic /></div></section>
            </div>
          </>}
          <footer className="page-footer"><span>NETSCOPE <span className="footer-dot">·</span> LOCAL NETWORK ANALYTICS</span><span>{isConnected ? 'API LINK ACTIVE' : 'WAITING FOR API'} <i className={`status-dot ${isConnected ? 'online' : 'offline'}`} /></span></footer>
        </div>
      </main>
    </div>
  );
}

export default App;








