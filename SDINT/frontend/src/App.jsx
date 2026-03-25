import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, MessageSquare, AlertTriangle, TrendingUp, BarChart3, Clock, ThumbsUp, ArrowLeft, LayoutDashboard, HeartPulse, Search, Bell } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';

import NarrativeArcChart from './components/NarrativeArcChart';
import OpinionDivergencePanel from './components/OpinionDivergencePanel';
import EchoChamberDashboard from './components/EchoChamberDashboard';

const API_BASE = import.meta.env.VITE_API_URL || 'https://sd-int.onrender.com/api';

function App() {
  const [activeTopic, setActiveTopic] = useState(null);
  const [trending, setTrending] = useState([]);
  const [trendAnalytics, setTrendAnalytics] = useState(null);
  const [posts, setPosts] = useState([]);
  const [loadingPosts, setLoadingPosts] = useState(false);
  const [selectedPost, setSelectedPost] = useState(null);
  const [postDetails, setPostDetails] = useState(null);
  const [postComments, setPostComments] = useState([]);
  const [toxicComments, setToxicComments] = useState([]);
  const [viewMode, setViewMode] = useState('dashboard'); // 'dashboard', 'postDetails', 'health'
  const [rssStatus, setRssStatus] = useState(null);

  useEffect(() => {
    fetchTrending();
    fetchToxicComments();
    fetchRssStatus();
    const interval = setInterval(fetchRssStatus, 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchRssStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/status`);
      if (res.data && res.data.length > 0) {
        // Find most recently updated
        const sorted = res.data.sort((a,b) => new Date(b.last_poll_time) - new Date(a.last_poll_time));
        setRssStatus(sorted[0]);
      }
    } catch(e) {}
  };

  useEffect(() => {
    fetchPosts(activeTopic);
    if (activeTopic !== null) {
      fetchTrendAnalytics(activeTopic);
    } else {
      setTrendAnalytics(null);
    }
  }, [activeTopic]);

  const fetchTrending = async () => {
    try {
      const res = await axios.get(`${API_BASE}/topics/trending`);
      setTrending(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchTrendAnalytics = async (topicId) => {
    try {
      const res = await axios.get(`${API_BASE}/trends/${topicId}/analytics`);
      setTrendAnalytics(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchPosts = async (topicId) => {
    setLoadingPosts(true);
    try {
      const url = topicId !== null ? `${API_BASE}/posts?topic_id=${topicId}` : `${API_BASE}/posts`;
      const res = await axios.get(url);
      setPosts(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingPosts(false);
    }
  };

  const fetchToxicComments = async () => {
    try {
      const res = await axios.get(`${API_BASE}/comments/toxic`);
      setToxicComments(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handlePostClick = async (post) => {
    setViewMode('postDetails');
    setSelectedPost(post);
    try {
      // Fetch summary and sentiment parallelly
      const [summaryRes, sentimentRes, commentsRes] = await Promise.all([
        axios.get(`${API_BASE}/posts/${post.post_id}/summary`).catch(() => ({ data: { summary: null } })),
        axios.get(`${API_BASE}/posts/${post.post_id}/sentiment`).catch(() => ({ data: { sentiment: null } })),
        axios.get(`${API_BASE}/posts/${post.post_id}/comments`).catch(() => ({ data: [] }))
      ]);

      setPostDetails({
        summary: summaryRes.data.summary,
        sentiment: sentimentRes.data.sentiment
      });
      setPostComments(commentsRes.data);
      
    } catch (err) {
      console.error("Failed to load post details", err);
    }
  };

  const renderSentimentChart = (sentimentData) => {
    if (!sentimentData) return <div className="text-muted">No sentiment data</div>;
    const data = [
      { name: 'Positive', value: sentimentData.positive || 0, color: '#10b981' },
      { name: 'Neutral', value: sentimentData.neutral || 0, color: '#8b5cf6' },
      { name: 'Negative', value: sentimentData.negative || 0, color: '#ef4444' }
    ].filter(d => d.value > 0);

    return (
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} stroke="rgba(255,255,255,0.05)" />
            ))}
          </Pie>
          <RechartsTooltip 
            contentStyle={{ backgroundColor: 'rgba(25, 28, 41, 0.9)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }} 
            itemStyle={{ color: '#fff' }}
          />
        </PieChart>
      </ResponsiveContainer>
    );
  };

  const renderDashboard = () => (
    <div className="dashboard-grid fade-in">
      <div className="sidebar">
        <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
          <h2 className="flex items-center gap-2" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={20} color="var(--accent-primary)" />
            Trending Topics
          </h2>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', marginTop: '1rem' }}>
            <span 
              className={`pill topic ${activeTopic === null ? 'active' : ''}`}
              onClick={() => setActiveTopic(null)}
            >
              All Topics
            </span>
            {trending.map(t => (
              <span 
                key={t.topic_id} 
                className={`pill topic ${activeTopic === t.topic_id ? 'active' : ''}`}
                onClick={() => setActiveTopic(t.topic_id)}
                title={`Mentions: ${t.frequency}`}
              >
                {t.label} 
                <span style={{opacity: 0.6, marginLeft: '6px', fontSize: '0.75rem'}}>({t.frequency})</span>
              </span>
            ))}
          </div>
        </div>

        {trendAnalytics && (
          <div className="glass-panel" style={{ marginBottom: '1.5rem' }}>
            <h2 className="flex items-center gap-2" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.1rem' }}>
              <TrendingUp size={18} color="var(--accent-secondary)" />
              Trend Analytics
            </h2>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
              <strong>Origin Post:</strong> {trendAnalytics.origin?.title} <br/>
              <strong>Started:</strong> {trendAnalytics.origin?.date}
            </div>
            {trendAnalytics.timeline && trendAnalytics.timeline.length > 0 && (
              <ResponsiveContainer width="100%" height={150}>
                <LineChart data={trendAnalytics.timeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={10} tickFormatter={(t) => String(t).split(' ')[0]} />
                  <RechartsTooltip 
                    contentStyle={{ backgroundColor: 'rgba(25, 28, 41, 0.9)', borderColor: 'rgba(255,255,255,0.1)', color: '#fff' }} 
                  />
                  <Line type="monotone" dataKey="mentions" stroke="var(--accent-primary)" strokeWidth={3} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        )}

        <div className="glass-panel">
          <h2 className="flex items-center gap-2" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={20} color="var(--toxic)" />
            Toxic Comment Radar
          </h2>
          <div style={{ marginTop: '1rem', maxHeight: '400px', overflowY: 'auto' }}>
            {toxicComments.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>No toxic comments detected currently.</p>
            ) : (
              <div className="post-list">
                {toxicComments.map(c => (
                  <div key={c.comment_id} className="glass-panel toxic-comment-item" style={{ padding: '1rem', borderRadius: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span className="pill toxic">Toxic ({c.toxicity_score.toFixed(2)})</span>
                      <small style={{ color: 'var(--text-muted)' }}>{c.author}</small>
                    </div>
                    <p style={{ fontSize: '0.9rem', wordBreak: 'break-word', color: 'rgba(255,17,0,0.8)' }}>"{c.text}"</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="main-content">
        <div className="glass-panel">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1.5rem' }}>
            <Activity size={20} color="var(--accent-secondary)" />
            Recent Discussions {activeTopic !== null && `- Filtered`}
          </h2>
          
          {loadingPosts ? (
            <div className="loader-container">
              <div className="spinner"></div>
            </div>
          ) : (
            <div className="post-list">
              {posts.map(post => (
                <div key={post.post_id} className="glass-panel post-card" onClick={() => handlePostClick(post)}>
                  <h3>{post.title}</h3>
                  <div className="post-meta">
                    <span><MessageSquare size={16} /> {post.number_of_comments} Comments</span>
                    <span><ThumbsUp size={16} /> {post.score} Score</span>
                    <span><Clock size={16} /> {new Date(post.created_utc * 1000).toLocaleDateString()}</span>
                  </div>
                  <p style={{ color: 'var(--text-muted)', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {post.content || "No text content for this post link."}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderPostDetails = () => (
    <div className="fade-in">
      <button 
        onClick={() => setViewMode('dashboard')}
        className="glass-panel"
        style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '0.5rem 1rem', marginBottom: '1.5rem', cursor: 'pointer', background: 'transparent' }}
      >
        <ArrowLeft size={16} /> Back to Dashboard
      </button>

      {selectedPost && (
        <div className="dashboard-grid" style={{ gridTemplateColumns: 'minmax(0, 1fr) 350px' }}>
          <div className="glass-panel" style={{ height: 'fit-content' }}>
            <h1 style={{ fontSize: '1.8rem', marginBottom: '1rem', color: '#fff' }}>{selectedPost.title}</h1>
            <div className="post-meta" style={{ borderBottom: '1px solid var(--panel-border)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
               <span><MessageSquare size={16} /> {selectedPost.number_of_comments}</span>
               <span><ThumbsUp size={16} /> {selectedPost.score}</span>
               <span>r/{selectedPost.subreddit}</span>
            </div>

            {postDetails?.summary && (
              <>
                <h3 className="gradient-text" style={{ fontSize: '1.1rem' }}>AI Extracted Summary</h3>
                <div className="summary-box">
                  "{postDetails.summary}"
                </div>
              </>
            )}

            <NarrativeArcChart postId={selectedPost.post_id} />
            <OpinionDivergencePanel postId={selectedPost.post_id} />

            <h3 style={{ marginTop: '2rem', marginBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
              Comment Thread Analysis
            </h3>

            <div className="post-list" style={{ marginTop: '1rem' }}>
              {postComments.length === 0 && <p className="text-muted">Gathering comments or none available...</p>}
              {postComments.map(c => (
                <div key={c.comment_id} style={{ padding: '1rem', borderRadius: '12px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--panel-border)', marginBottom: '0.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 500, color: 'var(--accent-primary)' }}>{c.author}</span>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <span className={`pill ${c.sentiment_label}`}>{c.sentiment_label}</span>
                      {c.is_toxic && <span className="pill toxic">Toxic</span>}
                    </div>
                  </div>
                  <p style={{ fontSize: '0.95rem', lineHeight: 1.6 }}>{c.text}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="sidebar" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div className="glass-panel text-center">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center' }}>
                <BarChart3 size={20} color="var(--accent-secondary)" />
                Sentiment Breakdown
              </h3>
              {postDetails ? renderSentimentChart(postDetails.sentiment) : (
                <div className="loader-container"><div className="spinner"></div></div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const getStatusColor = () => {
    if (!rssStatus) return 'red';
    const minDiff = (new Date() - new Date(rssStatus.last_poll_time)) / 60000;
    if (minDiff < 5) return '#10b981';
    if (minDiff < 15) return '#eab308';
    return '#ef4444';
  };

  return (
    <div className="platform-layout">
      <aside className="side-nav">
        <div className="brand">
          <h1 className="gradient-text">SocialPulse AI</h1>
          <p>Intelligence Platform</p>
        </div>
        
        <div className="nav-menu">
          <div 
            className={`nav-item ${viewMode === 'dashboard' ? 'active' : ''}`} 
            onClick={() => { setViewMode('dashboard'); setActiveTopic(null); }}
          >
            <LayoutDashboard size={20} />
            Overview Dashboard
          </div>
          <div 
            className={`nav-item ${viewMode === 'health' ? 'active' : ''}`} 
            onClick={() => setViewMode('health')}
          >
            <HeartPulse size={20} />
            Community Health
          </div>
        </div>
      </aside>

      <main className="main-area">
        <div className="top-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(255,255,255,0.03)', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--panel-border)', width: '300px' }}>
             <Search size={18} color="var(--text-muted)" />
             <input type="text" placeholder="Search discussions..." style={{ background: 'transparent', border: 'none', color: '#fff', outline: 'none', width: '100%', fontSize: '0.9rem' }} />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
             <div style={{ position: 'relative' }}>
                <Bell size={20} color="var(--text-muted)" />
                <div style={{ position: 'absolute', top: -2, right: -2, width: 8, height: 8, background: 'var(--accent-secondary)', borderRadius: '50%' }} />
             </div>
             <div style={{ background: 'rgba(255,255,255,0.05)', padding: '0.5rem 1rem', borderRadius: '20px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
               <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: getStatusColor(), boxShadow: `0 0 8px ${getStatusColor()}` }} />
               <span>Live &bull; {rssStatus ? `Sync'd ${Math.floor((new Date() - new Date(rssStatus.last_poll_time))/60000)}m ago` : 'Syncing...'}</span>
             </div>
          </div>
        </div>
        
        <div className="content">
          {viewMode === 'dashboard' && renderDashboard()}
          {viewMode === 'postDetails' && renderPostDetails()}
          {viewMode === 'health' && <EchoChamberDashboard />}
        </div>
      </main>
    </div>
  );
}

export default App;
