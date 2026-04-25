import React, { useState, useEffect, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';
import { Shield, TrendingDown } from 'lucide-react';
import { useDataCache } from '../DataCacheContext';

const EchoChamberDashboard = () => {
  const { fetchWithCache, getCached, API_BASE } = useDataCache();
  const [data, setData] = useState(() => getCached('echoChamber') || []);
  const [loading, setLoading] = useState(() => !getCached('echoChamber'));

  const fetchData = useCallback(async () => {
    try {
      const result = await fetchWithCache('echoChamber', `${API_BASE}/subreddits/echo-chamber`);
      setData(result);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  }, [API_BASE, fetchWithCache]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) {
    return (
      <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center' }}>
        <div className="skeleton" style={{ height: '300px', borderRadius: '6px' }} />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        <Shield size={48} style={{ opacity: 0.5, margin: '0 auto 1rem' }} />
        <p style={{ margin: 0 }}>No echo chamber metrics available yet</p>
      </div>
    );
  }

  const getClassificationConfig = (cls) => {
    const configs = {
      "strong echo chamber": { color: '#dc2626', label: 'STRONG', bg: 'rgba(220, 38, 38, 0.1)' },
      "moderate echo chamber": { color: '#f97316', label: 'MODERATE', bg: 'rgba(249, 115, 22, 0.1)' },
      "mixed": { color: '#f59e0b', label: 'MIXED', bg: 'rgba(245, 158, 11, 0.1)' },
      "diverse": { color: '#10b981', label: 'DIVERSE', bg: 'rgba(16, 185, 129, 0.1)' }
    };
    return configs[cls] || { color: '#8b5cf6', label: 'UNKNOWN', bg: 'rgba(139, 92, 246, 0.1)' };
  };

  const chartData = data.map(d => ({
    name: d.subreddit,
    Score: d.echo_chamber_score,
    FillColor: getClassificationConfig(d.classification).color
  }));

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '1.5rem' }}>
      
      {/* Chart Section */}
      <div className="card" style={{ borderTop: '3px solid var(--accent-secondary)' }}>
        <h3 style={{ 
          margin: '0 0 1rem 0', 
          display: 'flex', 
          alignItems: 'center', 
          gap: '8px',
          fontSize: '1rem',
          color: 'var(--accent-secondary)',
          textTransform: 'uppercase',
          fontWeight: 'bold',
          letterSpacing: '0.5px'
        }}>
          <Shield size={16} /> Community Polarization Index
        </h3>
        <p style={{ margin: '0 0 1.5rem 0', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          Echo chamber score across subreddits (higher = more homogeneous viewpoints)
        </p>
        
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: -10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 217, 255, 0.05)" vertical={false} />
            <XAxis 
              dataKey="name" 
              stroke="rgba(180, 184, 212, 0.4)"
              tick={{ fontSize: 12, fill: 'var(--text-muted)' }}
            />
            <YAxis 
              domain={[0, 1]} 
              stroke="rgba(180, 184, 212, 0.4)"
              tick={{ fontSize: 12, fill: 'var(--text-muted)' }}
            />
            <Tooltip 
              cursor={{ fill: 'rgba(0, 217, 255, 0.05)' }} 
              contentStyle={{ 
                backgroundColor: 'var(--panel-bg)', 
                border: '1px solid var(--panel-border)', 
                borderRadius: '6px',
                color: 'var(--text-bright)'
              }}
              formatter={(value) => value.toFixed(2)}
            />
            <Bar dataKey="Score" radius={[4, 4, 0, 0]} isAnimationActive={false}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.FillColor} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Metrics Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem', flex: 1, minHeight: 0, overflowY: 'auto' }}>
        {data.map(sub => {
          const cfg = getClassificationConfig(sub.classification);
          return (
            <div key={sub.subreddit} className="card" style={{ 
              borderTop: `3px solid ${cfg.color}`,
              display: 'flex',
              flexDirection: 'column'
            }}>
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', paddingBottom: '1rem', borderBottom: '1px solid var(--panel-border)' }}>
                <h4 style={{ margin: 0, fontSize: '1rem', color: 'var(--text-bright)' }}>
                  r/{sub.subreddit}
                </h4>
                <span className="badge" style={{ 
                  fontSize: '0.7rem',
                  background: cfg.bg,
                  color: cfg.color, 
                  border: `1px solid ${cfg.color}40`
                }}>
                  {cfg.label}
                </span>
              </div>
              
              {/* Metrics */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {/* Sentiment Homogeneity */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '0.5px' }}>
                      Sentiment Homogeneity
                    </span>
                    <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>
                      {(sub.sub_scores.sentiment_homogeneity * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '6px', background: 'rgba(0, 217, 255, 0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ 
                      width: `${sub.sub_scores.sentiment_homogeneity * 100}%`, 
                      height: '100%', 
                      background: 'linear-gradient(to right, #00d9ff, #7c3aed)',
                      transition: 'width 0.3s'
                    }} />
                  </div>
                </div>

                {/* Topic Concentration */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '0.5px' }}>
                      Topic Concentration
                    </span>
                    <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--accent-secondary)' }}>
                      {(sub.sub_scores.topic_concentration * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '6px', background: 'rgba(124, 58, 237, 0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ 
                      width: `${sub.sub_scores.topic_concentration * 100}%`, 
                      height: '100%', 
                      background: 'linear-gradient(to right, #7c3aed, #06b6d4)',
                      transition: 'width 0.3s'
                    }} />
                  </div>
                </div>

                {/* Vocabulary Insularity */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '0.5px' }}>
                      Vocabulary Insularity
                    </span>
                    <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: '#06b6d4' }}>
                      {(sub.sub_scores.vocabulary_insularity * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div style={{ width: '100%', height: '6px', background: 'rgba(6, 182, 212, 0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ 
                      width: `${sub.sub_scores.vocabulary_insularity * 100}%`, 
                      height: '100%', 
                      background: 'linear-gradient(to right, #06b6d4, #00d9ff)',
                      transition: 'width 0.3s'
                    }} />
                  </div>
                </div>
              </div>

              {/* Overall Score */}
              <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--panel-border)', textAlign: 'center' }}>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0, marginBottom: '0.3rem', textTransform: 'uppercase', fontWeight: 'bold' }}>
                  Overall Echo Score
                </p>
                <p style={{ fontSize: '1.3rem', fontWeight: 'bold', margin: 0, color: cfg.color }}>
                  {(sub.echo_chamber_score * 100).toFixed(0)}/100
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default EchoChamberDashboard;
