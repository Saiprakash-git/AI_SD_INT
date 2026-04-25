import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Globe, ChevronRight, Zap, Clock, TrendingUp } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:5000/api' : 'https://sd-int.onrender.com/api');
const PLACEHOLDERS = ["AI Safety...", "OpenAI Board...", "Cyberpunk 2077 Release...", "SVB Collapse..."];

export default function NarrativeSearch() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  
  const [phIdx, setPhIdx] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setPhIdx((p) => (p + 1) % PLACEHOLDERS.length), 3000);
    return () => clearInterval(t);
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query) return;
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/search/narrative?q=${encodeURIComponent(query)}`);
      setData(res.data);
    } catch {
      setData(null);
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', height: '100%', gap: '1.5rem' }} className="fade-in">
      
      {/* Search Section */}
      <div className="card" style={{ borderTop: '3px solid var(--accent-primary)', textAlign: 'center' }}>
        <h1 style={{ fontSize: '1.8rem', margin: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
          <Search size={28} style={{ color: 'var(--accent-primary)' }} />
          Narrative Search
        </h1>
        <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
          Explore narratives and topics across platforms over time
        </p>

        <form onSubmit={handleSearch} style={{ position: 'relative', maxWidth: '600px', margin: '1.5rem auto 0' }}>
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`e.g. ${PLACEHOLDERS[phIdx]}`}
            style={{ 
              width: '100%', 
              padding: '0.9rem 1.2rem', 
              fontSize: '0.95rem', 
              borderRadius: '6px',
              background: 'var(--panel-bg)', 
              border: '1px solid var(--panel-border)',
              color: 'var(--text-bright)'
            }}
          />
          <button 
            type="submit" 
            disabled={loading} 
            className="btn-primary"
            style={{ 
              position: 'absolute', 
              right: '6px', 
              top: '6px', 
              bottom: '6px', 
              padding: '0 1.5rem',
              minWidth: 'auto'
            }}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 2rem' }}>
          <TrendingUp size={48} style={{ animation: 'spin 2s linear infinite', color: 'var(--accent-secondary)', marginBottom: '1rem' }} />
          <h3 style={{ color: 'var(--text-bright)', marginTop: 0 }}>Analyzing narrative timeline</h3>
          <p style={{ color: 'var(--text-muted)', margin: 0 }}>Processing posts and external signals...</p>
        </div>
      )}

      {/* No Results Yet */}
      {!data && !loading && (
        <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 2rem', textAlign: 'center' }}>
          <Search size={48} style={{ color: 'var(--text-muted)', opacity: 0.5, marginBottom: '1rem' }} />
          <h3 style={{ color: 'var(--text-muted)', marginTop: 0 }}>No narrative analyzed yet</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>Enter a topic to explore how narratives evolve</p>
        </div>
      )}

      {/* Results */}
      {data && !loading && (
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }} className="fade-in">
          
          {/* Summary Card */}
          <div className="card" style={{ borderLeft: '4px solid var(--accent-secondary)', background: 'rgba(124, 58, 237, 0.05)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
              <div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0, textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '0.5px' }}>Topic</p>
                <p style={{ fontSize: '1.1rem', color: 'var(--accent-secondary)', fontWeight: 'bold', margin: '0.3rem 0 0 0' }}>"{data.query}"</p>
              </div>
              <div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0, textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '0.5px' }}>First Appeared</p>
                <p style={{ fontSize: '1.1rem', color: 'var(--text-bright)', fontWeight: 'bold', margin: '0.3rem 0 0 0' }}>{data.first_appeared_days_ago} days ago</p>
              </div>
              <div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0, textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '0.5px' }}>Current Status</p>
                <p style={{ fontSize: '1.1rem', fontWeight: 'bold', margin: '0.3rem 0 0 0', color: data.current_sentiment === 'positive' ? '#10b981' : data.current_sentiment === 'negative' ? '#ef4444' : '#f59e0b' }}>
                  {data.current_sentiment?.toUpperCase()}
                </p>
              </div>
              <div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0, textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '0.5px' }}>Conversations</p>
                <p style={{ fontSize: '1.1rem', color: 'var(--accent-primary)', fontWeight: 'bold', margin: '0.3rem 0 0 0' }}>{data.total_posts}</p>
              </div>
            </div>
          </div>

          {/* Timeline */}
          <div>
            <h3 style={{ fontSize: '1rem', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-primary)', textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '0.5px' }}>
              <Clock size={16} /> Event Timeline
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', position: 'relative', paddingLeft: '2rem' }}>
              {/* Timeline line */}
              <div style={{ position: 'absolute', left: '7px', top: 0, bottom: 0, width: '2px', background: 'linear-gradient(to bottom, var(--accent-primary), var(--accent-secondary))' }} />
              
              {data.timeline && data.timeline.map((node, i) => {
                const size = Math.min(Math.max(node.activity_score * 3, 14), 28);
                return (
                  <div key={i} style={{ position: 'relative', display: 'flex', gap: '1rem' }}>
                    {/* Dynamic node */}
                    <div style={{ 
                      position: 'absolute', 
                      left: `${9 - (size/2)}px`, 
                      top: '2px',
                      width: `${size}px`, 
                      height: `${size}px`, 
                      borderRadius: '50%', 
                      background: 'var(--panel-bg)', 
                      border: '2px solid var(--accent-secondary)',
                      boxShadow: `0 0 ${size}px rgba(124, 58, 237, 0.3)`
                    }} />
                    
                    {/* Content */}
                    <div className="card" style={{ flex: 1, padding: '0.75rem 1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', gap: '0.5rem' }}>
                        <span className="badge" style={{ fontSize: '0.7rem', background: 'rgba(124, 58, 237, 0.1)', color: 'var(--accent-secondary)', border: '1px solid rgba(124, 58, 237, 0.3)' }}>
                          Post #{node.post_id}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>{node.date}</span>
                      </div>
                      <p style={{ fontSize: '0.9rem', margin: 0, color: 'var(--text-main)', lineHeight: '1.4' }}>
                        {node.summary}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* External News */}
          {data.external_news && data.external_news.length > 0 && (
            <div>
              <h3 style={{ fontSize: '1rem', margin: '1.5rem 0 1rem 0', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-secondary)', textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '0.5px' }}>
                <Globe size={16} /> External Coverage
              </h3>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem' }}>
                {data.external_news.map((news, i) => (
                  <a 
                    key={i} 
                    href={news.url} 
                    target="_blank" 
                    rel="noreferrer" 
                    className="card" 
                    style={{ 
                      display: 'flex', 
                      flexDirection: 'column', 
                      textDecoration: 'none',
                      borderTop: '2px solid var(--accent-secondary)',
                      transition: 'all var(--transition-fast)'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderTopColor = 'var(--accent-primary)';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderTopColor = 'var(--accent-secondary)';
                      e.currentTarget.style.transform = 'translateY(0)';
                    }}
                  >
                    <h4 style={{ fontSize: '0.9rem', margin: '0 0 1rem 0', color: 'var(--text-bright)', lineHeight: '1.3', flex: 1 }}>
                      {news.headline}
                    </h4>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        {news.source}
                      </span>
                      <ChevronRight size={14} style={{ color: 'var(--text-muted)' }} />
                    </div>
                  </a>
                ))}
              </div>
            </div>
          )}

          {!data.external_news || data.external_news.length === 0 && (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center', padding: '1rem' }}>
              No external news coverage found for this narrative
            </p>
          )}

        </div>
      )}

    </div>
  );
}
