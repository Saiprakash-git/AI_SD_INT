import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';

const OpinionDivergencePanel = ({ postId }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (postId) {
      const API_BASE = import.meta.env.VITE_API_URL || 'https://sd-int.onrender.com/api';
      axios.get(`${API_BASE}/posts/${postId}/opinion-divergence`)
        .then(res => {
          setData(res.data);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    }
  }, [postId]);

  if (loading) return <div style={{ color: 'var(--text-muted)' }}>Loading Divergence Data...</div>;
  if (!data || data.cluster_count === 0) return null;

  // Radar chart expects unified variables per cluster
  // Rescale them roughly 0-1
  const maxComments = Math.max(...data.clusters.map(c => c.comment_count));
  const radarData = data.clusters.map(c => ({
    subject: `Cluster ${c.cluster_id}`,
    A_Sentiment: (c.avg_sentiment + 1) / 2, // -1 to 1 => 0 to 1
    B_Toxicity: c.toxicity_ratio,
    C_Count: maxComments > 0 ? c.comment_count / maxComments : 0,
    fullData: c
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const c = radarData.find(d => d.subject === label).fullData;
      return (
        <div style={{ background: 'rgba(25, 28, 41, 0.95)', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '8px', color: '#fff' }}>
          <h4>{label}: {c.viewpoint_label}</h4>
          <p>Sentiment: {c.avg_sentiment}</p>
          <p>Toxicity: {c.toxicity_ratio}</p>
          <p>Comments: {c.comment_count}</p>
        </div>
      );
    }
    return null;
  };

  const getDivergenceColor = (val) => {
    if (val < 0.5) return '#10b981';
    if (val < 1.0) return '#f59e0b';
    return '#ef4444';
  };

  const isOpposed = (id) => data.most_opposed_pair.includes(id);

  return (
    <div className="glass-panel" style={{ marginTop: '1.5rem' }}>
      <h3 style={{ margin: 0, fontSize: '1.1rem', marginBottom: '1.5rem' }}>Opinion Divergence Radar</h3>
      
      <div style={{ marginBottom: '2rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          <span>Low Divergence</span>
          <span>High Divergence</span>
        </div>
        <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden', position: 'relative', marginTop: '5px' }}>
          <div style={{ 
            height: '100%', 
            width: `${(data.overall_divergence / 2.0) * 100}%`, 
            background: getDivergenceColor(data.overall_divergence),
            transition: 'width 0.5s' 
          }}/>
        </div>
        <p style={{ textAlign: 'center', fontSize: '0.9rem', color: getDivergenceColor(data.overall_divergence), fontWeight: 'bold' }}>
          Score: {data.overall_divergence.toFixed(2)}
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        <ResponsiveContainer width="100%" height={250}>
          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
            <PolarGrid stroke="rgba(255,255,255,0.1)" />
            <PolarAngleAxis dataKey="subject" stroke="rgba(255,255,255,0.5)" fontSize={11} />
            <PolarRadiusAxis angle={30} domain={[0, 1]} tick={false} stroke="rgba(255,255,255,0.0)" />
            <Radar name="Sentiment (0=Neg, 1=Pos)" dataKey="A_Sentiment" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
            <Radar name="Toxicity Ratio" dataKey="B_Toxicity" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} />
            <Radar name="Volume" dataKey="C_Count" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
            <Tooltip content={<CustomTooltip />} />
          </RadarChart>
        </ResponsiveContainer>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: '300px', overflowY: 'auto' }}>
          {data.clusters.map(c => (
            <div key={c.cluster_id} style={{ 
              background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px',
              border: isOpposed(c.cluster_id) ? '1px solid #ef4444' : '1px solid rgba(255,255,255,0.05)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <h4 style={{ margin: 0, color: 'var(--text-main)', fontSize: '0.95rem' }}>"{c.viewpoint_label}"</h4>
                <span className={`pill ${c.sentiment_label}`}>{c.sentiment_label}</span>
              </div>
              <div style={{ display: 'block', marginTop: '10px' }}>
                {c.top_keywords.slice(0,5).map(kw => (
                  <span key={kw} style={{ display: 'inline-block', padding: '2px 6px', fontSize: '0.75rem', background: 'rgba(255,255,255,0.1)', marginRight: '5px', borderRadius: '4px', color: '#cbd5e1' }}>{kw}</span>
                ))}
              </div>
              <div style={{ marginTop: '10px', fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span>Toxicity: </span>
                <div style={{ flex: 1, height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px' }}>
                   <div style={{ width: `${c.toxicity_ratio * 100}%`, height: '100%', background: c.toxicity_ratio > 0.2 ? '#ef4444' : '#f59e0b' }}/>
                </div>
                <span>{(c.toxicity_ratio*100).toFixed(0)}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default OpinionDivergencePanel;
