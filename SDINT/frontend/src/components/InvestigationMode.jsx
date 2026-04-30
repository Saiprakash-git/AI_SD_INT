import React, { useState, useEffect, useRef } from 'react';
import {
  Search, Loader, AlertCircle, CheckCircle, Shield, Users, Globe, 
  Clock, Zap, TrendingUp, Link2, AlertTriangle, Download, Copy, Info
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const isRecord = (value) => value && typeof value === 'object' && !Array.isArray(value);

const displayValue = (value, fallback = 'N/A') => {
  if (value === null || value === undefined || value === '') return fallback;
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (isRecord(value)) return value.username || value.email || value.value || value.name || value.title || fallback;
  return fallback;
};

const getConfidence = (value) => {
  const raw = isRecord(value) ? value.confidence : value;
  const confidence = Number(raw || 0);
  return Number.isFinite(confidence) ? confidence : 0;
};

const getProfileUrl = (value) => {
  if (!isRecord(value)) return '';
  return value.url || value.profile_url || value.source_url || '';
};

export default function InvestigationMode() {
  const [query, setQuery] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [person, setPerson] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [platformSummary, setPlatformSummary] = useState([]);
  const [networkGraph, setNetworkGraph] = useState({ nodes: [], edges: [] });
  const [externalLinks, setExternalLinks] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const pollingInterval = useRef(null);
  const [pollingStatus, setPollingStatus] = useState('pending');

  // Start investigation
  async function handleStartInvestigation(e) {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please enter a query (email, username, domain, phone, or name)');
      return;
    }

    setLoading(true);
    setError(null);
    setPerson(null);
    setTimeline([]);
    setPlatformSummary([]);
    setNetworkGraph({ nodes: [], edges: [] });
    setExternalLinks([]);
    setPollingStatus('pending');

    try {
      let imagePath = '';
      let analysis = null;
      if (selectedImage) {
        const formData = new FormData();
        formData.append('image', selectedImage);
        try {
          const uploadRes = await fetch(`${API_BASE}/osint/upload`, {
            method: 'POST',
            body: formData
          });
          const uploadData = await uploadRes.json();
          if (uploadData.url) {
            imagePath = uploadData.url;
            analysis = uploadData.analysis;
          }
        } catch (err) {
          console.error("Image upload failed", err);
        }
      }

      const response = await fetch(`${API_BASE}/osint/investigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query.trim(),
          image_path: imagePath,
          image_analysis: analysis
        })
      });

      if (!response.ok) throw new Error(`Failed to start investigation: ${response.statusText}`);

      const data = await response.json();
      // Start polling
      const interval = setInterval(async () => {
        await pollResults(data.session_id, data.task_id);
      }, 2000);

      pollingInterval.current = interval;
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  // Poll for results
  async function pollResults(sId, tId) {
    try {
      const taskResponse = await fetch(`${API_BASE}/osint/tasks/${tId}`);
      const taskData = await taskResponse.json();
      setPollingStatus(taskData.status);

      if (taskData.status === 'complete' || taskData.status === 'success') {
        const sessionResponse = await fetch(`${API_BASE}/osint/session/${sId}`);
        const sessionData = await sessionResponse.json();

        if (sessionData.session) {
          setPerson(sessionData.person);
          setTimeline(sessionData.artifacts?.timeline || []);
          setPlatformSummary(sessionData.artifacts?.platform_summary || []);
          setNetworkGraph(sessionData.artifacts?.network_graph || { nodes: [], edges: [] });
          setExternalLinks(sessionData.artifacts?.external_links || []);
          setLoading(false);

          if (pollingInterval.current) {
            clearInterval(pollingInterval.current);
            pollingInterval.current = null;
          }
        }
      } else if (taskData.status === 'failed' || taskData.status === 'error') {
        setError(`Investigation failed: ${taskData.error || 'Unknown error'}`);
        setLoading(false);
        if (pollingInterval.current) {
          clearInterval(pollingInterval.current);
          pollingInterval.current = null;
        }
      }
    } catch (err) {
      console.error('Polling error:', err);
    }
  }

  useEffect(() => {
    return () => {
      if (pollingInterval.current) clearInterval(pollingInterval.current);
    };
  }, []);

  // Risk badge
  const getRiskBadge = (level) => {
    const config = {
      'CRITICAL': { color: '#dc2626', bg: 'rgba(220, 38, 38, 0.1)', icon: '⛔' },
      'HIGH': { color: '#f97316', bg: 'rgba(249, 115, 22, 0.1)', icon: '⚠️' },
      'MEDIUM': { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)', icon: '⚡' },
      'LOW': { color: '#10b981', bg: 'rgba(16, 185, 129, 0.1)', icon: '✓' }
    };
    const cfg = config[level] || config['LOW'];
    return { ...cfg };
  };

  const ConfidenceMeter = ({ confidence }) => {
    const pct = Math.round((confidence || 0) * 100);
    const color = pct > 75 ? '#10b981' : pct > 50 ? '#f59e0b' : '#ef4444';
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ flex: 1, height: '6px', backgroundColor: 'rgba(0, 217, 255, 0.1)', borderRadius: '3px', overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${pct}%`, backgroundColor: color, transition: 'width 0.3s' }} />
        </div>
        <span style={{ fontSize: '13px', fontWeight: 'bold', color, minWidth: '45px' }}>{pct}%</span>
      </div>
    );
  };

  const NetworkPreview = ({ graph }) => {
    const nodes = graph?.nodes || [];
    const edges = graph?.edges || [];
    if (!nodes.length) {
      return <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No network graph data</div>;
    }
    const center = { x: 300, y: 220 };
    const radius = 160;
    const positioned = nodes.slice(0, 40).map((node, idx) => {
      if (node.type === 'person' || idx === 0) return { ...node, x: center.x, y: center.y, r: 25, color: '#f59e0b' };
      const angle = ((idx - 1) / Math.max(nodes.length - 1, 1)) * Math.PI * 2;
      return { ...node, x: center.x + Math.cos(angle) * radius, y: center.y + Math.sin(angle) * radius, r: 15, color: 'var(--accent-secondary)' };
    });
    const byId = Object.fromEntries(positioned.map(node => [node.id, node]));

    return (
      <div className="card" style={{ overflowX: 'auto', display: 'flex', justifyContent: 'center' }}>
        <svg width="600" height="440" role="img" aria-label="Entity network preview">
          {edges.slice(0, 100).map((edge, idx) => {
            const from = byId[edge.from];
            const to = byId[edge.to];
            if (!from || !to) return null;
            return <line key={idx} x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke="rgba(0, 217, 255, 0.3)" strokeWidth="2" />;
          })}
          {positioned.map((node) => (
            <g key={node.id}>
              <circle cx={node.x} cy={node.y} r={node.r} fill={node.color} opacity="0.95" style={{ filter: 'drop-shadow(0 0 5px rgba(0, 217, 255, 0.4))' }}/>
              <text x={node.x} y={node.y + node.r + 15} textAnchor="middle" fill="var(--text-main)" fontSize="11" fontWeight="600">
                {displayValue(node.label, node.id).slice(0, 20)}
              </text>
            </g>
          ))}
        </svg>
      </div>
    );
  };

  // Loading state
  if (loading && !person) {
    return (
      <div style={{ padding: '2rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Search Header */}
        <div className="card" style={{ marginBottom: '2rem', borderTop: '3px solid var(--accent-primary)' }}>
          <h1 style={{ margin: 0, fontSize: '1.8rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Zap size={28} style={{ color: 'var(--accent-primary)' }} />
            OSINT Identity Discovery
          </h1>
          <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            Correlating evidence across 10+ data sources...
          </p>

          <form onSubmit={handleStartInvestigation} style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Provide a descriptive prompt to search (e.g., 'Find John Doe. He is from New York, born in 1990. Associated image: http://...') "
                disabled
                style={{ flex: 1, padding: '0.9rem 1.2rem', fontSize: '0.95rem', minHeight: '80px', borderRadius: '8px', resize: 'vertical' }}
              />
              <button type="submit" disabled style={{ padding: '0.9rem 2rem', opacity: 0.5, height: '80px' }}>Start</button>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'var(--panel-bg)', padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid var(--panel-border)' }}>
              <label style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Optional Target Image:</label>
              <input type="file" accept="image/*" disabled style={{ fontSize: '0.85rem' }} />
            </div>
          </form>
        </div>

        {/* Loading animation */}
        <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '2rem' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ marginBottom: '2rem' }}>
              <Loader size={48} style={{ animation: 'spin 1s linear infinite', color: 'var(--accent-primary)' }} />
            </div>
            <h3 style={{ marginTop: 0, color: 'var(--text-bright)', fontSize: '1.3rem' }}>Investigation in Progress</h3>
            <p style={{ color: 'var(--text-muted)', margin: '1rem 0' }}>
              Status: <span style={{ color: 'var(--accent-primary)', fontFamily: 'var(--font-mono)', fontWeight: 'bold' }}>{pollingStatus}</span>
            </p>
            
            {/* Progress steps */}
            <div style={{ display: 'flex', gap: '2rem', justifyContent: 'center', marginTop: '2rem', fontSize: '0.9rem' }}>
              {['Parse', 'Connectors', 'Resolve', 'Narrate'].map((step, i) => (
                <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{
                    width: '32px', height: '32px', borderRadius: '50%',
                    background: i === 0 ? 'var(--accent-primary)' : 'rgba(0, 217, 255, 0.1)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: i === 0 ? '#000' : 'var(--text-muted)', fontWeight: 'bold'
                  }}>
                    {i + 1}
                  </div>
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', height: '100%', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header Section */}
      <div className="card" style={{ borderTop: '3px solid var(--accent-primary)' }}>
        <h1 style={{ margin: 0, fontSize: '1.8rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Zap size={28} style={{ color: 'var(--accent-primary)' }} />
          OSINT Identity Discovery
        </h1>
        <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
          Discover and correlate online identities across 10+ platforms
        </p>

        <form onSubmit={handleStartInvestigation} style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Provide a descriptive prompt to search (e.g., 'Find John Doe. He is from New York, born in 1990. Associated image: http://...') "
              disabled={loading}
              style={{ flex: 1, padding: '0.9rem 1.2rem', fontSize: '0.95rem', minHeight: '80px', borderRadius: '8px', resize: 'vertical' }}
            />
            <button className="btn-primary" type="submit" disabled={loading} style={{ padding: '0.9rem 2rem', height: '80px' }}>
              {loading ? 'Investigating...' : 'Start Investigation'}
            </button>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'var(--panel-bg)', padding: '0.5rem 1rem', borderRadius: '8px', border: '1px solid var(--panel-border)' }}>
            <label style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Upload Target Image (for EXIF, Reverse Search & Facial matching):</label>
            <input 
              type="file" 
              accept="image/*" 
              disabled={loading}
              onChange={(e) => setSelectedImage(e.target.files[0])}
              style={{ fontSize: '0.85rem' }} 
            />
          </div>
        </form>
      </div>

      {/* Error State */}
      {error && (
        <div className="card" style={{ borderLeft: '3px solid var(--negative)', background: 'rgba(239, 68, 68, 0.05)' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
            <AlertCircle size={20} style={{ color: 'var(--negative)', flexShrink: 0, marginTop: '2px' }} />
            <div style={{ flex: 1 }}>
              <h4 style={{ margin: 0, color: 'var(--negative)', fontSize: '1rem' }}>Investigation Error</h4>
              <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-main)', fontSize: '0.9rem' }}>{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* No results yet */}
      {!person && !loading && (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem 2rem', flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
          <Search size={48} style={{ color: 'var(--text-muted)', marginBottom: '1rem', opacity: 0.5 }} />
          <h3 style={{ color: 'var(--text-muted)', marginTop: 0 }}>No Active Investigation</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Enter a query above to start discovering identities</p>
        </div>
      )}

      {/* Results Grid */}
      {person && !loading && (
        <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '1.5rem', flex: 1 }}>
          {/* Dossier Sidebar */}
          <div className="card" style={{ borderTop: '3px solid var(--accent-secondary)', height: 'fit-content' }}>
            <h3 style={{ margin: '0 0 1.5rem 0', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-secondary)' }}>
              <Shield size={18} /> DOSSIER
            </h3>

            {/* Canonical Name */}
            <div style={{ marginBottom: '1.5rem', paddingBottom: '1.5rem', borderBottom: '1px solid var(--panel-border)' }}>
              <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 'bold' }}>Subject</p>
              <h4 style={{ margin: '0.5rem 0 0 0', fontSize: '1.4rem', color: 'var(--text-bright)' }}>{person.canonical_name || 'Unknown'}</h4>
            </div>

            {/* Risk Assessment */}
            <div style={{ marginBottom: '1.5rem', paddingBottom: '1.5rem', borderBottom: '1px solid var(--panel-border)' }}>
              <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 'bold' }}>Risk Level</p>
              {(() => {
                const cfg = getRiskBadge(person.risk_level);
                return (
                  <div style={{ background: cfg.bg, padding: '0.75rem', borderRadius: '6px', marginTop: '0.5rem', border: `1px solid ${cfg.color}22`, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '1.2rem' }}>{cfg.icon}</span>
                    <span style={{ color: cfg.color, fontWeight: 'bold', fontSize: '0.95rem' }}>{person.risk_level}</span>
                  </div>
                );
              })()}
            </div>

            {/* Confidence */}
            <div style={{ marginBottom: '1.5rem', paddingBottom: '1.5rem', borderBottom: '1px solid var(--panel-border)' }}>
              <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 'bold' }}>Match Confidence</p>
              <div style={{ marginTop: '0.75rem' }}>
                <ConfidenceMeter confidence={person.match_confidence} />
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                  {person.match_confidence >= 0.9 ? '90%+ confidence: High corroboration, exact match across 3+ sources.' :
                   person.match_confidence >= 0.7 ? '70–90% confidence: Consistent username and partial context match.' :
                   person.match_confidence >= 0.5 ? '50–70% confidence: Name match only, unverified context.' :
                   'Below 50% confidence: Possible match, low corroboration.'}
                </p>
              </div>
            </div>

            {/* Corroboration */}
            {person.corroborations && person.corroborations.length > 0 && (
              <div style={{ marginBottom: '1.5rem', paddingBottom: '1.5rem', borderBottom: '1px solid var(--panel-border)' }}>
                <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 'bold' }}>Corroboration Signals</p>
                <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {person.corroborations.map((reason, idx) => (
                    <div key={idx} style={{ 
                      fontSize: '0.85rem', 
                      color: reason.startsWith('✓') ? '#10b981' : (reason.startsWith('⚠') ? '#f59e0b' : 'var(--text-bright)'),
                      background: 'var(--panel-hover)',
                      padding: '0.6rem',
                      borderRadius: '4px',
                      borderLeft: reason.startsWith('✓') ? '3px solid #10b981' : (reason.startsWith('⚠') ? '3px solid #f59e0b' : 'none')
                    }}>
                      {reason}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Evidence Count */}
            <div style={{ marginBottom: '1.5rem', paddingBottom: '1.5rem', borderBottom: '1px solid var(--panel-border)' }}>
              <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 'bold' }}>Evidence Items</p>
              <p style={{ margin: '0.5rem 0 0 0', fontSize: '1.6rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>{timeline.length}</p>
            </div>

            {/* Identifiers */}
            {person.emails && person.emails.length > 0 && (
              <div style={{ marginBottom: '1.5rem', paddingBottom: '1.5rem', borderBottom: '1px solid var(--panel-border)' }}>
                <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 'bold' }}>Emails</p>
                <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {person.emails.map((email, i) => (
                    <code key={i} style={{ fontSize: '0.8rem', padding: '0.5rem', background: 'var(--panel-hover)', borderRadius: '4px', color: 'var(--accent-primary)', wordBreak: 'break-all' }}>{displayValue(email)}</code>
                  ))}
                </div>
              </div>
            )}

            {person.usernames && person.usernames.length > 0 && (
              <div>
                <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 'bold' }}>Usernames</p>
                <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {person.usernames.map((u, i) => {
                    const username = displayValue(u);
                    const platform = isRecord(u) ? u.platform : '';
                    const profileUrl = getProfileUrl(u);

                    return (
                      <span key={profileUrl || `${username}-${i}`} className="badge" title={platform ? `${username} on ${platform}` : username}>
                        {profileUrl ? (
                          <a href={profileUrl} target="_blank" rel="noreferrer" style={{ color: 'inherit', textDecoration: 'none' }}>
                            {username}{platform ? ` (${platform})` : ''}
                          </a>
                        ) : (
                          <>{username}{platform ? ` (${platform})` : ''}</>
                        )}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Main Content */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '2px solid var(--panel-border)', paddingBottom: '0' }}>
              {[
                { id: 'overview', label: '📋 Overview', icon: Info },
                { id: 'timeline', label: '📅 Timeline', icon: Clock },
                { id: 'platforms', label: '🌐 Platforms', icon: Globe },
                { id: 'network', label: 'Network', icon: Users },
                { id: 'links', label: 'Links', icon: Link2 },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  style={{
                    padding: '0.75rem 1.5rem',
                    background: activeTab === tab.id ? 'transparent' : 'transparent',
                    border: 'none',
                    borderBottom: activeTab === tab.id ? '2px solid var(--accent-primary)' : '2px solid transparent',
                    color: activeTab === tab.id ? 'var(--accent-primary)' : 'var(--text-muted)',
                    cursor: 'pointer',
                    fontSize: '0.95rem',
                    fontWeight: activeTab === tab.id ? '600' : '500',
                    transition: 'all var(--transition-fast)'
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div style={{ flex: 1 }}>
              {activeTab === 'overview' && (
                <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '2rem', padding: '1.5rem' }}>
                  {(person.summary || person.intelligence_summary) && (
                    <div className="card" style={{ borderLeft: '4px solid var(--accent-primary)' }}>
                      <h4 style={{ margin: 0, marginBottom: '0.75rem', color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Info size={18} /> Executive Summary
                      </h4>
                      <p style={{ margin: 0, lineHeight: '1.6', color: 'var(--text-main)' }}>{person.summary || person.intelligence_summary}</p>
                    </div>
                  )}

                  {/* Organised Categorized Section */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
                    {/* Photos */}
                    <div className="card" style={{ borderTop: '3px solid #8b5cf6' }}>
                      <h4 style={{ margin: 0, marginBottom: '0.75rem', color: '#8b5cf6', display: 'flex', alignItems: 'center', gap: '8px' }}>📸 Photos & Media</h4>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                        {externalLinks.filter(l => l.url.match(/\.(jpeg|jpg|gif|png)$/i) || l.connector === 'image_intelligence').length > 0 ? (
                          externalLinks.filter(l => l.url.match(/\.(jpeg|jpg|gif|png)$/i) || l.connector === 'image_intelligence').map((l, i) => (
                             <a key={i} href={l.url} target="_blank" rel="noreferrer" style={{ display: 'inline-block', width: '80px', height: '80px', borderRadius: '8px', background: `url(${l.url}) center/cover no-repeat`, border: '1px solid var(--panel-border)' }} title={l.title}></a>
                          ))
                        ) : <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No media found</span>}
                      </div>
                      
                      {/* Reverse Search Links inside Photos tab */}
                      {externalLinks.filter(l => l.connector === 'saucenao_reverse_search').length > 0 && (
                        <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--panel-border)' }}>
                          <h5 style={{ margin: 0, marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Reverse Image Matches:</h5>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                            {externalLinks.filter(l => l.connector === 'saucenao_reverse_search').slice(0,4).map((l, i) => (
                              <a key={i} href={l.url} target="_blank" rel="noreferrer" style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', textDecoration: 'none' }}>
                                🔗 {l.platform || l.title} Match
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Social Profiles */}
                    <div className="card" style={{ borderTop: '3px solid #3b82f6' }}>
                      <h4 style={{ margin: 0, marginBottom: '0.75rem', color: '#3b82f6', display: 'flex', alignItems: 'center', gap: '8px' }}>👥 Top Social Profiles</h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {platformSummary.filter(p => ['Instagram', 'X', 'Twitter', 'Telegram', 'Reddit', 'GitHub'].includes(p.platform)).slice(0,5).length > 0 ? (
                          platformSummary.filter(p => ['Instagram', 'X', 'Twitter', 'Telegram', 'Reddit', 'GitHub'].includes(p.platform)).slice(0,5).map((p, i) => (
                            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem', background: 'var(--panel-hover)', borderRadius: '6px' }}>
                              <span style={{ fontWeight: 'bold' }}>{p.platform}</span>
                              <a href={p.urls?.[0]} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-primary)', fontSize: '0.85rem' }}>{p.usernames?.[0] || 'View'}</a>
                            </div>
                          ))
                        ) : <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No prominent social profiles discovered</span>}
                      </div>
                    </div>

                    {/* News Articles */}
                    <div className="card" style={{ borderTop: '3px solid #10b981' }}>
                      <h4 style={{ margin: 0, marginBottom: '0.75rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '8px' }}>📰 News & Articles</h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                         {externalLinks.filter(l => l.connector === 'gdelt_news' || l.connector === 'news_article').length > 0 ? (
                            externalLinks.filter(l => l.connector === 'gdelt_news' || l.connector === 'news_article').slice(0,4).map((l, i) => (
                              <a key={i} href={l.url} target="_blank" rel="noreferrer" style={{ fontSize: '0.85rem', color: 'var(--text-main)', textDecoration: 'none', borderLeft: '2px solid #10b981', paddingLeft: '8px' }}>
                                {displayValue(l.title).slice(0, 60)}...
                              </a>
                            ))
                         ) : <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No direct news mentions found</span>}
                      </div>
                    </div>
                  </div>
                  
                  {person.breach_findings && person.breach_findings.length > 0 && (
                    <div className="card" style={{ borderTop: '3px solid var(--negative)' }}>
                      <h4 style={{ margin: 0, marginBottom: '0.75rem', color: 'var(--negative)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <AlertTriangle size={18} /> Breach Exposure ({person.breach_findings.length})
                      </h4>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
                        {person.breach_findings.map((b, i) => (
                          <div key={i} style={{ background: 'rgba(239, 68, 68, 0.05)', padding: '0.75rem 1rem', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.9rem', flex: '1 1 calc(50% - 0.75rem)' }}>
                            <strong style={{ color: 'var(--negative)', display: 'block', marginBottom: '4px' }}>{displayValue(b.source || b.connector_name, 'Unknown source')}</strong>
                            <span style={{ color: 'var(--text-muted)' }}>
                              {displayValue(b.email || b.details?.email || b.details?.breach_type, 'Exposure detected')} | {displayValue(b.date || b.timestamp, 'Date unknown')}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'timeline' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {timeline.length > 0 ? (
                    timeline.map((event, i) => (
                      <div key={event.id || i} className="card" style={{ borderLeft: '3px solid var(--accent-primary)', padding: '1rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            {event.timestamp ? new Date(event.timestamp).toLocaleString() : 'Time unknown'}
                          </span>
                          <span className="badge" style={{ fontSize: '0.75rem' }}>{displayValue(event.type, 'event')}</span>
                        </div>
                        <h5 style={{ margin: '0.5rem 0', color: 'var(--text-bright)' }}>{displayValue(event.title, 'Untitled event')}</h5>
                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                          {displayValue(event.platform, 'Unknown platform')} | Severity: {displayValue(event.severity, 'LOW')}
                        </p>
                      </div>
                    ))
                  ) : (
                    <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No timeline events</div>
                  )}
                </div>
              )}

              {activeTab === 'platforms' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                  {platformSummary.length > 0 ? (
                    [...platformSummary].sort((a, b) => {
                      const order = ['Instagram', 'X', 'Twitter', 'Telegram', 'Reddit', 'GitHub', 'HackerNews'];
                      const indexA = order.indexOf(a.platform);
                      const indexB = order.indexOf(b.platform);
                      if (indexA !== -1 && indexB !== -1) return indexA - indexB;
                      if (indexA !== -1) return -1;
                      if (indexB !== -1) return 1;
                      return (b.evidence_count || b.count || 0) - (a.evidence_count || a.count || 0);
                    }).map((plat, i) => {
                      const profileUrls = plat.urls || plat.profile_urls || [];

                      return (
                      <div key={`${displayValue(plat.platform, 'platform')}-${i}`} className="card" style={{ borderTop: '3px solid var(--accent-secondary)' }}>
                        <h5 style={{ margin: 0, marginBottom: '0.75rem', color: 'var(--text-bright)' }}>{displayValue(plat.platform, 'Unknown platform')}</h5>
                        <div style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                          <div>
                            <span style={{ color: 'var(--text-muted)' }}>Evidence:</span>
                            <span style={{ color: 'var(--accent-primary)', fontWeight: 'bold', marginLeft: '0.5rem' }}>{displayValue(plat.evidence_count || plat.count, '0')}</span>
                          </div>
                          {plat.usernames && plat.usernames.length > 0 && (
                            <div>
                              <span style={{ color: 'var(--text-muted)' }}>Users:</span>
                              <div style={{ marginTop: '0.3rem' }}>
                                {plat.usernames.slice(0, 5).map((u, j) => {
                                  const username = displayValue(u);
                                  const confidence = getConfidence(u);
                                  return (
                                    <code key={`${username}-${j}`} style={{ display: 'block', fontSize: '0.75rem', color: 'var(--accent-primary)', marginTop: '0.2rem' }}>
                                      {username}{confidence ? ` (${Math.round(confidence * 100)}%)` : ''}
                                    </code>
                                  );
                                })}
                                {plat.usernames.length > 5 && <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>+{plat.usernames.length - 5} more variants</span>}
                              </div>
                            </div>
                          )}
                          {profileUrls.length > 0 && (
                            <a href={profileUrls[0]} target="_blank" rel="noreferrer" style={{ color: 'var(--accent-secondary)', fontSize: '0.8rem', marginTop: '0.5rem' }}>
                              View Profile
                            </a>
                          )}
                        </div>
                      </div>
                    );
                    })
                  ) : (
                    <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No platform data</div>
                  )}
                </div>
              )}

              {activeTab === 'network' && (
                <NetworkPreview graph={networkGraph} />
              )}

              {activeTab === 'links' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {externalLinks.length > 0 ? (
                    externalLinks.map((link, i) => (
                      <a
                        key={`${link.url}-${i}`}
                        href={link.url}
                        target="_blank"
                        rel="noreferrer"
                        className="card"
                        style={{ textDecoration: 'none', borderLeft: '3px solid var(--accent-secondary)', padding: '1rem' }}
                      >
                        <div style={{ color: 'var(--text-bright)', fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.35rem' }}>
                          {displayValue(link.title, 'External link')}
                        </div>
                        <div style={{ color: 'var(--accent-secondary)', fontSize: '0.8rem', wordBreak: 'break-all' }}>{link.url}</div>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: '0.35rem' }}>
                          {displayValue(link.connector, 'source')} {link.platform ? `| ${link.platform}` : ''}
                        </div>
                      </a>
                    ))
                  ) : (
                    <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No external links found</div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
