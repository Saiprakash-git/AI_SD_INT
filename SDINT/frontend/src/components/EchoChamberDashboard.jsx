import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';

const EchoChamberDashboard = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5 * 60 * 1000); // Every 5 minutes
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const API_BASE = import.meta.env.VITE_API_URL || 'https://sd-int.onrender.com/api';
      const res = await axios.get(`${API_BASE}/subreddits/echo-chamber`);
      setData(res.data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  if (loading) return <div className="glass-panel">Loading Community Health...</div>;
  if (!data || data.length === 0) return <div className="glass-panel text-muted">No Echo Chamber metrics analyzed yet. Waiting for scheduler...</div>;

  const getColor = (cls) => {
    if (cls === "strong echo chamber") return "#ef4444";
    if (cls === "moderate echo chamber") return "#f97316";
    if (cls === "mixed") return "#eab308";
    if (cls === "diverse") return "#10b981";
    return "#8b5cf6";
  };

  const chartData = data.map(d => ({
    name: d.subreddit,
    Score: d.echo_chamber_score,
    FillColor: getColor(d.classification)
  }));

  return (
    <div className="fade-in">
      <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>Community Health & Echo Chambers</h2>
        <p style={{ color: 'var(--text-muted)' }}>Measuring viewpoint homogeneity, topic concentration, and lexical insularity across subreddits.</p>
        
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: -10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="name" stroke="rgba(255,255,255,0.3)" />
            <YAxis domain={[0, 1]} stroke="rgba(255,255,255,0.3)" />
            <Tooltip cursor={{ fill: 'rgba(255,255,255,0.02)' }} contentStyle={{ backgroundColor: 'rgba(25, 28, 41, 0.95)', border: 'none', color: '#fff' }} />
            <Bar dataKey="Score" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.FillColor} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1.5rem' }}>
        {data.map(sub => (
          <div key={sub.subreddit} className="glass-panel" style={{ borderTop: `4px solid ${getColor(sub.classification)}`, padding: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0 }}>r/{sub.subreddit}</h3>
              <span className={`pill`} style={{ 
                backgroundColor: getColor(sub.classification) + '22', 
                color: getColor(sub.classification), border: `1px solid ${getColor(sub.classification)}` 
              }}>
                {sub.classification}
              </span>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Sentiment Homogeneity</span>
                <span>{sub.sub_scores.sentiment_homogeneity}</span>
              </div>
              <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', marginBottom: '5px' }}>
                <div style={{ width: `${sub.sub_scores.sentiment_homogeneity * 100}%`, height: '100%', background: 'rgba(255,255,255,0.8)' }} />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Topic Concentration</span>
                <span>{sub.sub_scores.topic_concentration}</span>
              </div>
              <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', marginBottom: '5px' }}>
                <div style={{ width: `${sub.sub_scores.topic_concentration * 100}%`, height: '100%', background: 'rgba(255,255,255,0.6)' }} />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Vocabulary Insularity</span>
                <span>{sub.sub_scores.vocabulary_insularity}</span>
              </div>
              <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px' }}>
                <div style={{ width: `${sub.sub_scores.vocabulary_insularity * 100}%`, height: '100%', background: 'rgba(255,255,255,0.4)' }} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EchoChamberDashboard;
