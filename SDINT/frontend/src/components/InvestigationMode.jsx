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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [person, setPerson] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [platformSummary, setPlatformSummary] = useState([]);
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
    setPollingStatus('pending');

    try {
      const response = await fetch(`${API_BASE}/api/osint/investigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim() })
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
      const taskResponse = await fetch(`${API_BASE}/api/osint/tasks/${tId}`);
      const taskData = await taskResponse.json();
      setPollingStatus(taskData.status);

      if (taskData.status === 'complete' || taskData.status === 'success') {
        const sessionResponse = await fetch(`${API_BASE}/api/osint/session/${sId}`);
        const sessionData = await sessionResponse.json();

        if (sessionData.session) {
          setPerson(sessionData.person);
          setTimeline(sessionData.artifacts?.timeline || []);
          setPlatformSummary(sessionData.artifacts?.platform_summary || []);
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

          <form onSubmit={handleStartInvestigation} style={{ marginTop: '1.5rem', display: 'flex', gap: '10px' }}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter email, username, domain, phone, or name..."
              disabled
              style={{ flex: 1, padding: '0.9rem 1.2rem', fontSize: '0.95rem' }}
            />
            <button type="submit" disabled style={{ padding: '0.9rem 2rem', opacity: 0.5 }}>Start</button>
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

        <form onSubmit={handleStartInvestigation} style={{ marginTop: '1.5rem', display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter email, username, domain, phone, or name..."
            disabled={loading}
            style={{ flex: 1, padding: '0.9rem 1.2rem', fontSize: '0.95rem' }}
          />
          <button className="btn-primary" type="submit" disabled={loading} style={{ padding: '0.9rem 2rem' }}>
            {loading ? 'Investigating...' : 'Start Investigation'}
          </button>
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
              </div>
            </div>

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
                <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  {(person.summary || person.intelligence_summary) && (
                    <div>
                      <h4 style={{ margin: 0, marginBottom: '0.75rem', color: 'var(--accent-primary)' }}>Summary</h4>
                      <p style={{ margin: 0, lineHeight: '1.6', color: 'var(--text-main)' }}>{person.summary || person.intelligence_summary}</p>
                    </div>
                  )}
                  
                  {person.breach_findings && person.breach_findings.length > 0 && (
                    <div>
                      <h4 style={{ margin: 0, marginBottom: '0.75rem', color: 'var(--negative)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <AlertTriangle size={16} /> Breach Exposure
                      </h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        {person.breach_findings.map((b, i) => (
                          <div key={i} style={{ background: 'rgba(239, 68, 68, 0.05)', padding: '0.75rem', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.2)', fontSize: '0.9rem' }}>
                            <strong style={{ color: 'var(--negative)' }}>{displayValue(b.source || b.connector_name, 'Unknown source')}</strong>
                            <p style={{ margin: '0.3rem 0 0 0', color: 'var(--text-muted)' }}>
                              {displayValue(b.email || b.details?.email || b.details?.breach_type, 'Exposure detected')} | {displayValue(b.date || b.timestamp, 'Date unknown')}
                            </p>
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
                    platformSummary.map((plat, i) => {
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
                                {plat.usernames.map((u, j) => {
                                  const username = displayValue(u);
                                  const confidence = getConfidence(u);
                                  return (
                                    <code key={`${username}-${j}`} style={{ display: 'block', fontSize: '0.75rem', color: 'var(--accent-primary)', marginTop: '0.2rem' }}>
                                      {username}{confidence ? ` (${Math.round(confidence * 100)}%)` : ''}
                                    </code>
                                  );
                                })}
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
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
