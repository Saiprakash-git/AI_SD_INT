import React, { useState } from 'react';
import axios from 'axios';
import { Link2, Zap, Cpu, Database, Globe, AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:5000/api' : 'https://sd-int.onrender.com/api');

export default function LinkAnalyzer() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!url) return;
    setLoading(true);
    setError('');
    setData(null);
    try {
      const res = await axios.post(`${API_BASE}/analyze-link`, { url });
      if (res.data.error) setError(res.data.error);
      else setData(res.data);
    } catch {
      setError('Failed to analyze the provided URL. Ensure it is publicly accessible.');
    }
    setLoading(false);
  };

  const getSentimentColor = (sent) => {
    if (!sent) return '#9ca3af';
    if (sent.compound >= 0.05) return '#10b981';
    if (sent.compound <= -0.05) return '#ef4444';
    return '#f59e0b';
  };

  const getSentimentLabel = (sent) => {
    if (!sent) return 'NEUTRAL';
    if (sent.compound >= 0.05) return 'POSITIVE';
    if (sent.compound <= -0.05) return 'NEGATIVE';
    return 'NEUTRAL';
  };

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', height: '100%', gap: '1.5rem' }} className="fade-in">
      
      {/* Page Header */}
      <div className="card" style={{ borderTop: '3px solid var(--accent-primary)' }}>
        <h1 style={{ margin: 0, fontSize: '1.8rem', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Link2 size={28} style={{ color: 'var(--accent-primary)' }} />
          Universal Link Analyzer
        </h1>
        <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
          Analyze URLs across platforms for sentiment, propagation, and internal correlations
        </p>

        {/* Input Section */}
        <form onSubmit={handleAnalyze} style={{ display: 'flex', gap: '10px', marginTop: '1.5rem' }}>
          <input 
            type="url" 
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste any URL (news, Reddit, YouTube...)"
            disabled={loading}
            style={{ 
              flex: 1, 
              padding: '0.9rem 1.2rem', 
              fontSize: '0.95rem',
              borderRadius: '6px'
            }}
            required
          />
          <button className="btn-primary" type="submit" disabled={loading} style={{ padding: '0.9rem 2rem', whiteSpace: 'nowrap' }}>
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </form>
      </div>

      {/* Error State */}
      {error && (
        <div className="card" style={{ 
          borderLeft: '3px solid var(--negative)', 
          background: 'rgba(239, 68, 68, 0.05)',
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-start'
        }}>
          <AlertCircle size={20} style={{ color: 'var(--negative)', flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h4 style={{ margin: 0, color: 'var(--negative)', fontSize: '1rem' }}>Analysis Failed</h4>
            <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-main)', fontSize: '0.9rem' }}>{error}</p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="glass-panel fade-in" style={{ 
          padding: '3rem 2rem', 
          textAlign: 'center',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{ marginBottom: '1.5rem' }}>
            <Cpu size={48} style={{ animation: 'spin 1s linear infinite', color: 'var(--accent-secondary)' }} />
          </div>
          <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-bright)', fontSize: '1.1rem' }}>Fingerprinting URL</h3>
          <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Extracting → Analyzing → Cross-referencing
          </p>
        </div>
      )}

      {/* No Results Yet */}
      {!data && !loading && !error && (
        <div className="glass-panel" style={{ 
          padding: '3rem 2rem', 
          textAlign: 'center',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <Link2 size={48} style={{ color: 'var(--text-muted)', opacity: 0.5, marginBottom: '1rem' }} />
          <h3 style={{ color: 'var(--text-muted)', marginTop: 0 }}>No URL analyzed yet</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>Enter a URL above to analyze propagation and sentiment</p>
        </div>
      )}

      {/* Results Grid */}
      {data && !loading && (
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
          gap: '1.5rem',
          flex: 1
        }} className="fade-in">
           
          {/* Column 1: Extracted Fingerprint */}
          <div className="card" style={{ borderTop: '3px solid var(--accent-primary)' }}>
            <h3 style={{ 
              fontSize: '1rem', 
              margin: '0 0 1rem 0', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              color: 'var(--accent-primary)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              fontWeight: 'bold'
            }}>
              <Cpu size={16} /> Fingerprint
            </h3>
            
            {/* Title and Preview */}
            <div style={{ marginBottom: '1.5rem', paddingBottom: '1.5rem', borderBottom: '1px solid var(--panel-border)' }}>
              <h4 style={{ fontSize: '1rem', margin: '0 0 0.5rem 0', color: 'var(--text-bright)', lineHeight: '1.3' }}>
                {data.content_summary?.title}
              </h4>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0, lineHeight: '1.4' }}>
                {data.content_summary?.preview}
              </p>
              <a 
                href={data.url} 
                target="_blank" 
                rel="noreferrer" 
                style={{ 
                  fontSize: '0.8rem', 
                  color: 'var(--accent-secondary)', 
                  textDecoration: 'none',
                  marginTop: '0.5rem',
                  display: 'inline-block'
                }}
              >
                View Source →
              </a>
            </div>

            {/* Sentiment and Toxicity */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {/* Sentiment */}
              <div style={{ background: 'var(--panel-hover)', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--panel-border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '0.5px' }}>Sentiment</span>
                  <span style={{ 
                    fontSize: '0.9rem', 
                    fontWeight: 'bold',
                    color: getSentimentColor(data.sentiment)
                  }}>
                    {getSentimentLabel(data.sentiment)}
                  </span>
                </div>
                <span style={{ 
                  fontSize: '0.75rem', 
                  color: 'var(--text-muted)',
                  fontFamily: 'var(--font-mono)'
                }}>
                  Score: {data.sentiment ? data.sentiment.compound.toFixed(2) : 'N/A'}
                </span>
              </div>

              {/* Toxicity */}
              {data.is_toxic && (
                <div style={{ 
                  background: 'rgba(239, 68, 68, 0.05)', 
                  padding: '0.75rem', 
                  borderRadius: '6px', 
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <AlertTriangle size={14} style={{ color: 'var(--negative)', flexShrink: 0 }} />
                  <span style={{ fontSize: '0.8rem', color: 'var(--negative)', fontWeight: 'bold' }}>
                    HIGH TOXICITY
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Column 2: Internal Heatmap */}
          <div className="card" style={{ borderTop: '3px solid var(--accent-secondary)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ 
                fontSize: '1rem', 
                margin: 0, 
                display: 'flex', 
                alignItems: 'center', 
                gap: '8px',
                color: 'var(--accent-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                fontWeight: 'bold'
              }}>
                <Database size={16} /> Internal Heatmap
              </h3>
              <span className="badge" style={{ 
                fontSize: '0.7rem',
                background: 'rgba(16, 185, 129, 0.1)',
                color: '#10b981',
                border: '1px solid rgba(16, 185, 129, 0.3)'
              }}>
                {data.confidence_score}% MATCH
              </span>
            </div>
            
            {data.internal_matches && data.internal_matches.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {data.internal_matches.map((match, i) => (
                  <div 
                    key={i} 
                    style={{ 
                      padding: '0.75rem', 
                      background: 'var(--panel-hover)', 
                      borderRadius: '4px', 
                      border: '1px solid var(--panel-border)',
                      borderLeft: '2px solid var(--accent-secondary)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem', marginBottom: '0.4rem' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 'bold' }}>
                        r/{match.subreddit}
                      </span>
                      <span className="badge" style={{ 
                        fontSize: '0.65rem',
                        background: 'rgba(124, 58, 237, 0.1)',
                        color: 'var(--accent-secondary)',
                        border: '1px solid rgba(124, 58, 237, 0.3)'
                      }}>
                        {match.similarity}% SIMILAR
                      </span>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-main)', lineHeight: '1.3' }}>
                      {match.title}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '1.5rem 0', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No internal matches found
              </div>
            )}
          </div>

          {/* Column 3: External Propagation */}
          <div className="card" style={{ borderTop: '3px solid #9ca3af' }}>
            <h3 style={{ 
              fontSize: '1rem', 
              margin: '0 0 1rem 0', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              color: '#9ca3af',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              fontWeight: 'bold'
            }}>
              <Globe size={16} /> External Propagation
            </h3>
            
            {data.external_web && data.external_web.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '400px', overflowY: 'auto' }}>
                {data.external_web.map((web, i) => (
                  <a 
                    key={i} 
                    href={web.href || web.url} 
                    target="_blank" 
                    rel="noreferrer" 
                    style={{ 
                      display: 'block', 
                      textDecoration: 'none',
                      padding: '0.75rem', 
                      background: 'var(--panel-hover)', 
                      borderRadius: '4px', 
                      border: '1px solid var(--panel-border)',
                      transition: 'all var(--transition-fast)'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderLeftColor = 'var(--accent-primary)';
                      e.currentTarget.style.borderLeftWidth = '2px';
                      e.currentTarget.style.background = 'var(--panel-bg)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderLeftColor = 'transparent';
                      e.currentTarget.style.borderLeftWidth = '1px';
                      e.currentTarget.style.background = 'var(--panel-hover)';
                    }}
                  >
                    <h4 style={{ margin: '0 0 0.4rem 0', fontSize: '0.8rem', color: 'var(--text-bright)' }}>
                      {web.title}
                    </h4>
                    <p style={{ 
                      margin: 0, 
                      fontSize: '0.75rem', 
                      color: 'var(--text-muted)', 
                      display: '-webkit-box', 
                      WebkitLineClamp: 2, 
                      WebkitBoxOrient: 'vertical', 
                      overflow: 'hidden',
                      lineHeight: '1.3'
                    }}>
                      {web.body || web.snippet}
                    </p>
                  </a>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '1.5rem 0', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No external references tracked
              </div>
            )}
          </div>

        </div>
      )}

    </div>
  );
}
