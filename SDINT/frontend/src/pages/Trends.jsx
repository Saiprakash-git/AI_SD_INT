import React, { useState, useEffect } from 'react';
import { Activity, TrendingUp } from 'lucide-react';
import EchoChamberDashboard from '../components/EchoChamberDashboard';
import { useDataCache } from '../DataCacheContext';

export default function Trends() {
  const { fetchWithCache, getCached, API_BASE } = useDataCache();
  const [trending, setTrending] = useState(() => getCached('trending') || []);
  const [loading, setLoading] = useState(() => !getCached('trending'));

  useEffect(() => {
    fetchTrending();
  }, []);

  const fetchTrending = async () => {
    try {
      const data = await fetchWithCache('trending', `${API_BASE}/topics/trending`);
      setTrending(data);
      setLoading(false);
    } catch(e) { setLoading(false); }
  };

  const getTopicSentimentColor = (topic) => {
    const s = topic.sentiment?.compound || 0;
    if (s > 0.05) return 'var(--positive)';
    if (s < -0.05) return 'var(--negative)';
    return 'var(--neutral)';
  };

  return (
    <div className="fade-in">
      <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <TrendingUp color="var(--accent-primary)" /> Macro Trends & Platform Health
      </h2>

      {/* Horizontal Trending Strip */}
      <div className="card" style={{ marginBottom: '2rem', display: 'flex', flexWrap: 'nowrap', overflowX: 'auto', gap: '1rem', paddingBottom: '1.5rem' }}>
         <h4 className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '8px', minWidth: 'fit-content' }}>
           <Activity size={14}/> LIVE VELOCITY
         </h4>
         
         {loading && <div className="skeleton" style={{ width: '100%', height: '40px' }} />}
         
         {!loading && trending.map(topic => {
            const sColor = getTopicSentimentColor(topic);
            return (
              <div key={topic.topic_id} style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--bg-color)', padding: '0.5rem 1rem', borderRadius: '50px', border: '1px solid var(--panel-border)', cursor: 'pointer', whiteSpace: 'nowrap' }} className="nav-item">
                 <div style={{ width: 8, height: 8, borderRadius: '50%', background: sColor }} />
                 <span style={{ fontSize: '0.9rem', color: 'var(--text-bright)' }}>{topic.label || (topic.top_words ? topic.top_words.slice(0, 2).join(' / ') : `Topic ${topic.topic_id}`)}</span>
                 <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--accent-secondary)' }}>
                    ↑ {(topic.frequency || topic.post_count || 0)} posts
                 </span>
              </div>
            );
         })}
      </div>

      <div className="card fade-in" style={{ padding: '0' }}>
         <EchoChamberDashboard />
      </div>

    </div>
  );
}
