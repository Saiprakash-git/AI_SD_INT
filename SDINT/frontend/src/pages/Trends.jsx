import React, { useState, useEffect, useCallback } from 'react';
import { Activity, TrendingUp, Zap } from 'lucide-react';
import EchoChamberDashboard from '../components/EchoChamberDashboard';
import { useDataCache } from '../DataCacheContext';

export default function Trends() {
  const { fetchWithCache, getCached, API_BASE } = useDataCache();
  const [trending, setTrending] = useState(() => getCached('trending') || []);
  const [loading, setLoading] = useState(() => !getCached('trending'));

  const fetchTrending = useCallback(async () => {
    try {
      const data = await fetchWithCache('trending', `${API_BASE}/topics/trending`);
      setTrending(data);
      setLoading(false);
    } catch {
      setLoading(false);
    }
  }, [API_BASE, fetchWithCache]);

  useEffect(() => {
    fetchTrending();
  }, [fetchTrending]);

  const getTopicSentimentColor = (topic) => {
    const s = topic.sentiment?.compound || 0;
    if (s > 0.05) return '#10b981';
    if (s < -0.05) return '#ef4444';
    return '#f59e0b';
  };

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', height: '100%', gap: '1.5rem' }} className="fade-in">
      
      {/* Page Header */}
      <div className="card" style={{ borderTop: '3px solid var(--accent-primary)' }}>
        <h1 style={{ margin: 0, fontSize: '1.8rem', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <TrendingUp size={28} style={{ color: 'var(--accent-primary)' }} />
          Macro Trends & Platform Health
        </h1>
        <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
          Real-time topic velocity and echo chamber analysis across platforms
        </p>
      </div>

      {/* Trending Topics Strip */}
      <div className="card" style={{ borderTop: '2px solid var(--accent-secondary)' }}>
        <h3 style={{ 
          margin: '0 0 1rem 0', 
          display: 'flex', 
          alignItems: 'center', 
          gap: '8px',
          fontSize: '0.95rem',
          color: 'var(--accent-secondary)',
          textTransform: 'uppercase',
          fontWeight: 'bold',
          letterSpacing: '0.5px'
        }}>
          <Activity size={16} /> Live Velocity
        </h3>

        {loading && (
          <div style={{ display: 'flex', gap: '0.75rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
            {[1, 2, 3, 4].map(i => <div key={i} className="skeleton" style={{ width: '200px', height: '40px', borderRadius: '20px', flexShrink: 0 }} />)}
          </div>
        )}

        {!loading && trending.length > 0 && (
          <div style={{ display: 'flex', gap: '0.75rem', overflowX: 'auto', paddingBottom: '0.5rem', scrollBehavior: 'smooth' }}>
            {trending.map(topic => {
              const sColor = getTopicSentimentColor(topic);
              const topicLabel = topic.label || (topic.top_words ? topic.top_words.slice(0, 2).join(' / ') : `Topic ${topic.topic_id}`);
              const postCount = topic.frequency || topic.post_count || 0;

              return (
                <div 
                  key={topic.topic_id} 
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    background: 'var(--panel-hover)',
                    padding: '0.65rem 1rem',
                    borderRadius: '6px',
                    border: '1px solid var(--panel-border)',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    flexShrink: 0,
                    transition: 'all var(--transition-fast)'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = sColor;
                    e.currentTarget.style.background = 'var(--panel-bg)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--panel-border)';
                    e.currentTarget.style.background = 'var(--panel-hover)';
                  }}
                >
                  {/* Sentiment Dot */}
                  <div style={{ 
                    width: '8px', 
                    height: '8px', 
                    borderRadius: '50%', 
                    background: sColor,
                    flexShrink: 0
                  }} />
                  
                  {/* Topic Label */}
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-bright)', fontWeight: 500 }}>
                    {topicLabel.substring(0, 25)}
                    {topicLabel.length > 25 ? '...' : ''}
                  </span>
                  
                  {/* Post Count */}
                  <span style={{ 
                    fontSize: '0.75rem', 
                    color: 'var(--text-muted)',
                    fontWeight: 'bold',
                    fontFamily: 'var(--font-mono)'
                  }}>
                    ↑ {postCount}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        {!loading && trending.length === 0 && (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textAlign: 'center', padding: '1rem', margin: 0 }}>
            No trending topics available yet
          </p>
        )}
      </div>

      {/* Echo Chamber Dashboard */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <EchoChamberDashboard />
      </div>

    </div>
  );
}
