import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts';

const NarrativeArcChart = ({ postId }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (postId) {
      const API_BASE = import.meta.env.VITE_API_URL || 'https://sd-int.onrender.com/api';
      axios.get(`${API_BASE}/posts/${postId}/narrative-arc`)
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

  if (loading) return <div style={{ color: 'var(--text-muted)' }}>Loading Narrative Arc...</div>;
  if (!data || !data.timeline || data.timeline.length === 0) return null;

  const shapeColors = {
    "steady_positive": "#10b981",
    "steady_negative": "#ef4444",
    "deteriorating": "#ef4444",
    "recovering": "#10b981",
    "volatile": "#f59e0b",
    "neutral": "#8b5cf6"
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const point = payload[0].payload;
      const event = data.arc_events.find(e => e.index === point.comment_index);
      return (
        <div style={{ background: 'rgba(25, 28, 41, 0.95)', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '8px', color: '#fff' }}>
          <p>Comment Index: {point.comment_index}</p>
          <p style={{ color: point.rolling_avg > 0 ? '#10b981' : '#ef4444' }}>Rolling Avg: {point.rolling_avg}</p>
          <p style={{ color: 'var(--text-muted)' }}>Raw Score: {point.raw_score}</p>
          {event && <p style={{ color: '#f59e0b', fontWeight: 'bold', marginTop: '5px' }}>Event: {event.type.replace('_', ' ')}</p>}
        </div>
      );
    }
    return null;
  };

  // Custom line dot for events
  const CustomDot = (props) => {
    const { cx, cy, payload } = props;
    const hasEvent = data.arc_events.some(e => e.index === payload.comment_index);
    if (hasEvent) {
      return <circle cx={cx} cy={cy} r={4} stroke="#f59e0b" strokeWidth={2} fill="#1e1e2d" />;
    }
    return null;
  };

  return (
    <div className="glass-panel" style={{ marginTop: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Narrative Arc Tracking</h3>
        <span style={{
          padding: '4px 10px', borderRadius: '12px', fontSize: '0.85rem', fontWeight: 'bold',
          backgroundColor: shapeColors[data.arc_shape] + '22',
          color: shapeColors[data.arc_shape],
          border: `1px solid ${shapeColors[data.arc_shape]}55`,
          textTransform: 'capitalize'
        }}>
          {data.arc_shape.replace('_', ' ')}
        </span>
      </div>
      
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
        Analyzing the emotional journey across {data.summary.total_comments} comments.
      </p>

      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data.timeline} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <XAxis dataKey="comment_index" stroke="rgba(255,255,255,0.3)" fontSize={11} />
          <YAxis domain={[-1, 1]} stroke="rgba(255,255,255,0.3)" fontSize={11} ticks={[-1, -0.5, 0, 0.5, 1]} />
          <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" strokeDasharray="3 3" />
          <Tooltip content={<CustomTooltip />} />
          
          <Line 
            type="monotone" 
            dataKey="raw_score" 
            stroke="var(--text-muted)" 
            strokeWidth={1} 
            dot={false}
            opacity={0.3}
            isAnimationActive={false}
          />
          <Line 
            type="monotone" 
            dataKey="rolling_avg" 
            stroke="var(--accent-primary)" 
            strokeWidth={3} 
            dot={<CustomDot />}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default NarrativeArcChart;
