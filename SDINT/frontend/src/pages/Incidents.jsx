import React, { useState, useEffect, useCallback } from 'react';
import { AlertOctagon, TrendingUp, Clock, FileText, AlertTriangle, Zap, ExternalLink } from 'lucide-react';
import { useDataCache } from '../DataCacheContext';

export default function Incidents() {
  const { fetchWithCache, getCached, API_BASE } = useDataCache();
  const [incidents, setIncidents] = useState(() => getCached('incidents') || []);
  const [expanded, setExpanded] = useState(null);
  const [loading, setLoading] = useState(!getCached('incidents'));

  const fetchIncidents = useCallback(async () => {
    try {
      const data = await fetchWithCache('incidents', `${API_BASE}/incidents`);
      setIncidents(data);
      setLoading(false);
    } catch {
      setLoading(false);
    }
  }, [API_BASE, fetchWithCache]);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  const getSeverityConfig = (sev) => {
    if (sev > 75) return { color: '#dc2626', bg: 'rgba(220, 38, 38, 0.1)', label: 'CRITICAL', icon: '⛔' };
    if (sev > 50) return { color: '#f97316', bg: 'rgba(249, 115, 22, 0.1)', label: 'HIGH', icon: '⚠️' };
    if (sev > 25) return { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.1)', label: 'MEDIUM', icon: '⚡' };
    return { color: '#10b981', bg: 'rgba(16, 185, 129, 0.1)', label: 'LOW', icon: '✓' };
  };

  if (loading && incidents.length === 0) {
    return (
      <div style={{ padding: '2rem', height: '100%' }}>
        <div className="skeleton" style={{ height: '200px', marginBottom: '1rem' }} />
        <div className="skeleton" style={{ height: '200px' }} />
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', height: '100%', gap: '1.5rem' }} className="fade-in">
      
      {/* Page Header */}
      <div className="card" style={{ borderTop: '3px solid var(--negative)' }}>
        <h1 style={{ margin: 0, fontSize: '1.8rem', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AlertTriangle size={28} style={{ color: 'var(--negative)' }} />
          Detected Incidents
        </h1>
        <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
          Automatically detected clusters and coordinated narratives
        </p>
      </div>

      {/* Incidents List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', flex: 1, overflowY: 'auto' }}>
        
        {incidents.length === 0 && (
          <div className="glass-panel" style={{ padding: '3rem 2rem', textAlign: 'center', flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <AlertOctagon size={48} style={{ color: 'var(--text-muted)', opacity: 0.5, marginBottom: '1rem' }} />
            <h3 style={{ color: 'var(--text-muted)', marginTop: 0 }}>No incidents detected</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>Incidents are auto-generated from topic clusters with 3+ coordinated posts</p>
          </div>
        )}

        {incidents.map((inc, i) => {
          const sevCfg = getSeverityConfig(inc.severity);
          const isExpanded = expanded === i;

          return (
            <div 
              key={i} 
              className="card" 
              style={{ 
                borderLeft: `4px solid ${sevCfg.color}`,
                overflow: 'hidden',
                transition: 'all var(--transition-fast)'
              }}
            >
              
              {/* Header */}
              <div 
                onClick={() => setExpanded(isExpanded ? null : i)} 
                style={{ 
                  cursor: 'pointer',
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'flex-start', 
                  gap: '1rem',
                  paddingBottom: '1rem',
                  borderBottom: isExpanded ? '1px solid var(--panel-border)' : 'none'
                }}
              >
                <div style={{ flex: 1 }}>
                  <h3 style={{ fontSize: '1.2rem', margin: '0 0 0.75rem 0', color: 'var(--text-bright)' }}>
                    {inc.title}
                  </h3>
                  
                  {/* Metadata */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
                    {/* Severity Badge */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '0.5rem 1rem',
                        background: sevCfg.bg,
                        border: `1px solid ${sevCfg.color}40`,
                        borderRadius: '6px',
                        fontSize: '0.8rem',
                        fontWeight: 'bold',
                        color: sevCfg.color
                      }}>
                        <span>{sevCfg.icon}</span>
                        <span>{sevCfg.label}</span>
                        <span>/100: {inc.severity}</span>
                      </div>
                    </div>

                    {/* Post Count */}
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <FileText size={14} style={{ color: 'var(--accent-secondary)' }} />
                      {inc.posts?.length || 0} posts
                    </span>

                    {/* Timeline Duration */}
                    {inc.timeline && inc.timeline.length > 0 && (
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={14} style={{ color: 'var(--accent-primary)' }} />
                        {inc.timeline[0].date} to {inc.timeline[inc.timeline.length - 1].date}
                      </span>
                    )}
                  </div>
                </div>

                {/* Expand Button */}
                <button 
                  className="btn-secondary" 
                  style={{ padding: '0.6rem 1.2rem', whiteSpace: 'nowrap' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    setExpanded(isExpanded ? null : i);
                  }}
                >
                  {isExpanded ? 'Collapse' : 'Analyze'}
                </button>
              </div>

              {/* Collapsed Timeline Preview */}
              {!isExpanded && inc.timeline && inc.timeline.length > 0 && (
                <div style={{ 
                  display: 'flex', 
                  gap: '0.75rem', 
                  marginTop: '1rem', 
                  overflowX: 'auto', 
                  paddingBottom: '0.5rem',
                  scrollBehavior: 'smooth'
                }}>
                  {inc.timeline.slice(0, 4).map((node, nodeIdx) => (
                    <div 
                      key={nodeIdx} 
                      style={{ 
                        minWidth: '160px', 
                        background: 'var(--panel-hover)', 
                        padding: '0.75rem', 
                        borderRadius: '4px', 
                        border: '1px solid var(--panel-border)',
                        fontSize: '0.8rem'
                      }}
                    >
                      <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', margin: 0, marginBottom: '0.4rem', textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '0.5px' }}>
                        {node.phase}
                      </p>
                      <p style={{ fontSize: '0.8rem', margin: 0, marginBottom: '0.4rem', color: 'var(--text-main)', lineHeight: '1.3' }}>
                        {node.summary?.substring(0, 40)}...
                      </p>
                      <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', margin: 0 }}>{node.date}</p>
                    </div>
                  ))}
                  {inc.timeline.length > 4 && (
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      padding: '0.75rem', 
                      color: 'var(--text-muted)',
                      fontSize: '0.8rem'
                    }}>
                      +{inc.timeline.length - 4} more
                    </div>
                  )}
                </div>
              )}

              {/* Expanded View */}
              {isExpanded && (
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: '1fr 1fr', 
                  gap: '2rem', 
                  marginTop: '1.5rem'
                }} className="fade-in">
                  
                  {/* Left: Timeline */}
                  <div>
                    <h4 style={{ 
                      margin: '0 0 1.5rem 0',
                      color: 'var(--accent-primary)', 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px',
                      textTransform: 'uppercase',
                      fontSize: '0.9rem',
                      letterSpacing: '0.5px',
                      fontWeight: 'bold'
                    }}>
                      <TrendingUp size={16} /> Event Timeline
                    </h4>

                    {/* Timeline visualization */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', position: 'relative', paddingLeft: '2rem' }}>
                      {/* Vertical line */}
                      <div style={{ 
                        position: 'absolute', 
                        left: '7px', 
                        top: '10px', 
                        bottom: '10px', 
                        width: '2px', 
                        background: 'linear-gradient(to bottom, var(--accent-primary), var(--accent-secondary))'
                      }} />
                      
                      {inc.timeline.map((node, nodeIdx) => (
                        <div key={nodeIdx} style={{ position: 'relative' }}>
                          {/* Timeline dot */}
                          <div style={{ 
                            position: 'absolute', 
                            left: '-19px', 
                            top: '4px', 
                            width: '16px', 
                            height: '16px', 
                            borderRadius: '50%', 
                            background: 'var(--panel-bg)', 
                            border: '3px solid var(--accent-primary)',
                            boxShadow: '0 0 0 4px rgba(0, 217, 255, 0.1)'
                          }} />
                          
                          {/* Content */}
                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.3rem' }}>
                              <span style={{ 
                                fontSize: '0.75rem', 
                                color: 'var(--accent-primary)', 
                                fontWeight: 'bold',
                                textTransform: 'uppercase',
                                letterSpacing: '0.5px'
                              }}>
                                {node.phase}
                              </span>
                              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                                {node.date}
                              </span>
                            </div>
                            <p style={{ 
                              fontSize: '0.85rem', 
                              lineHeight: '1.5',
                              color: 'var(--text-main)',
                              margin: 0
                            }}>
                              {node.summary}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Right: External Coverage */}
                  <div>
                    <h4 style={{ 
                      margin: '0 0 1.5rem 0',
                      color: 'var(--accent-secondary)', 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px',
                      textTransform: 'uppercase',
                      fontSize: '0.9rem',
                      letterSpacing: '0.5px',
                      fontWeight: 'bold'
                    }}>
                      <FileText size={16} /> External Coverage
                    </h4>

                    {inc.news && inc.news.length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {inc.news.map((article, articleIdx) => (
                          <a 
                            href={article.url} 
                            target="_blank" 
                            rel="noreferrer" 
                            key={articleIdx}
                            style={{
                              display: 'block',
                              padding: '0.75rem',
                              background: 'var(--panel-hover)',
                              border: '1px solid var(--panel-border)',
                              borderRadius: '4px',
                              textDecoration: 'none',
                              transition: 'all var(--transition-fast)',
                              borderLeft: '2px solid var(--accent-secondary)'
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.borderLeftColor = 'var(--accent-primary)';
                              e.currentTarget.style.background = 'var(--panel-bg)';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.borderLeftColor = 'var(--accent-secondary)';
                              e.currentTarget.style.background = 'var(--panel-hover)';
                            }}
                          >
                            <h5 style={{ margin: '0 0 0.4rem 0', fontSize: '0.85rem', color: 'var(--text-bright)', display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                              <ExternalLink size={12} style={{ flexShrink: 0, marginTop: '2px', color: 'var(--accent-secondary)' }} />
                              {article.title?.substring(0, 60)}...
                            </h5>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem' }}>
                              <span style={{ color: 'var(--accent-secondary)', fontWeight: 'bold' }}>{article.source}</span>
                              <span style={{ color: 'var(--text-muted)' }}>{article.date}</span>
                            </div>
                          </a>
                        ))}
                      </div>
                    ) : (
                      <div style={{ 
                        padding: '1.5rem', 
                        textAlign: 'center', 
                        border: '1px dashed var(--panel-border)', 
                        borderRadius: '4px',
                        background: 'rgba(0, 0, 0, 0.2)'
                      }}>
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: 0 }}>
                          No external news coverage found
                        </p>
                      </div>
                    )}
                  </div>

                </div>
              )}

            </div>
          );
        })}

      </div>

    </div>
  );
}
