import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { MessageSquare, AlertTriangle, ThumbsUp, Camera, User, Zap, Clock } from 'lucide-react';
import NarrativeArcChart from '../components/NarrativeArcChart';
import OpinionDivergencePanel from '../components/OpinionDivergencePanel';
import { useDataCache } from '../DataCacheContext';

export default function Feed() {
  const { fetchWithCache, getCached, API_BASE } = useDataCache();
  const [posts, setPosts] = useState(() => getCached('posts') || []);
  const [selectedPost, setSelectedPost] = useState(null);
  const [loading, setLoading] = useState(() => !getCached('posts'));
  const [echoStatus, setEchoStatus] = useState(null);
  const [comments, setComments] = useState([]);
  const [commentsLoading, setCommentsLoading] = useState(false);

  const fetchPosts = useCallback(async () => {
    try {
      const data = await fetchWithCache('posts', `${API_BASE}/posts`);
      setPosts(data);
      setLoading(false);
    } catch {
      setLoading(false);
    }
  }, [API_BASE, fetchWithCache]);

  useEffect(() => {
    if (selectedPost) {
       axios.get(`${API_BASE}/subreddits/${selectedPost.subreddit}/echo-chamber`)
         .then(res => setEchoStatus(res.data?.classification || 'unknown'))
         .catch(() => setEchoStatus('unknown'));

       // Fetch comments for this post
       setCommentsLoading(true);
       axios.get(`${API_BASE}/posts/${selectedPost.post_id}/comments`)
         .then(res => { setComments(res.data || []); setCommentsLoading(false); })
         .catch(() => { setComments([]); setCommentsLoading(false); });
    } else {
       setEchoStatus(null);
       setComments([]);
    }
  }, [API_BASE, selectedPost]);

  useEffect(() => {
    fetchPosts();
    const interval = setInterval(fetchPosts, 30000);
    return () => clearInterval(interval);
  }, [fetchPosts]);

  const getSentimentColor = (post) => {
    const s = post.sentiment?.compound || 0;
    if (s >= 0.05) return '#10b981';  // green
    if (s <= -0.05) return '#ef4444';  // red
    return '#f59e0b';  // amber
  };

  const getSentimentLabel = (post) => {
    const s = post.sentiment?.compound || 0;
    if (s >= 0.05) return 'POSITIVE';
    if (s <= -0.05) return 'NEGATIVE';
    return 'NEUTRAL';
  };

  const getCommentSentColor = (label) => {
    if (label === 'positive') return '#10b981';
    if (label === 'negative') return '#ef4444';
    return '#f59e0b';
  };

  if (loading && posts.length === 0) return <div className="skeleton" style={{height: '200px'}}></div>;

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', height: '100%', gap: '1.5rem' }}>
      
      {/* Page Header */}
      <div className="card" style={{ borderTop: '3px solid var(--accent-primary)' }}>
        <h1 style={{ margin: 0, fontSize: '1.8rem', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Zap size={28} style={{ color: 'var(--accent-primary)' }} />
          Live Discussion Stream
        </h1>
        <p style={{ margin: '0.5rem 0 0 0', color: 'var(--text-muted)', fontSize: '0.95rem' }}>
          Real-time social media posts with sentiment analysis and discussion tracking
        </p>
      </div>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedPost ? '1fr 380px' : '1fr', gap: '1.5rem', flex: 1 }}>
        
        {/* Feed Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', overflowY: 'auto' }}>
          {posts.length === 0 && !loading && (
            <div className="glass-panel" style={{ padding: '3rem 2rem', textAlign: 'center' }}>
              <MessageSquare size={48} style={{ color: 'var(--text-muted)', opacity: 0.5, margin: '0 auto 1rem' }} />
              <h3 style={{ color: 'var(--text-muted)', marginTop: 0 }}>No posts available</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Posts will appear here when social feeds are updated</p>
            </div>
          )}

          {posts.map(post => {
            const sColor = getSentimentColor(post);
            const sLabel = getSentimentLabel(post);
            return (
              <div 
                key={post.post_id} 
                onClick={() => setSelectedPost(post)}
                className="card"
                style={{ 
                  cursor: 'pointer', 
                  borderLeft: `4px solid ${sColor}`,
                  background: selectedPost?.post_id === post.post_id ? 'var(--panel-hover)' : 'var(--panel-bg)',
                  transition: 'all var(--transition-fast)'
                }}
                onMouseEnter={(e) => {
                  if (selectedPost?.post_id !== post.post_id) {
                    e.currentTarget.style.borderLeftColor = 'var(--accent-primary)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedPost?.post_id !== post.post_id) {
                    e.currentTarget.style.borderLeftColor = sColor;
                  }
                }}
              >
                {/* Post Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 'bold' }}>r/{post.subreddit}</span>
                    <span className="badge" style={{ fontSize: '0.7rem', background: sColor + '20', color: sColor, border: `1px solid ${sColor}40` }}>
                      {sLabel}
                    </span>
                  </div>
                  
                  {post.is_toxic && (
                    <span className="badge" style={{ fontSize: '0.7rem', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.3)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <AlertTriangle size={12} /> TOXIC
                    </span>
                  )}
                </div>

                {/* Post Title */}
                <h3 style={{ fontSize: '1.05rem', margin: '0 0 0.75rem 0', color: 'var(--text-bright)', lineHeight: '1.4' }}>
                  {post.title}
                </h3>

                {/* Post Content Preview */}
                <p style={{ color: 'var(--text-main)', fontSize: '0.9rem', marginBottom: '1rem', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', lineHeight: '1.5' }}>
                  {post.content}
                </p>

                {/* Post Metadata */}
                <div style={{ display: 'flex', gap: '1.5rem', color: 'var(--text-muted)', fontSize: '0.85rem', padding: '0.75rem 0', borderTop: '1px solid var(--panel-border)', paddingTop: '0.75rem' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <MessageSquare size={14} style={{ color: 'var(--accent-secondary)' }} /> 
                    {post.number_of_comments} comments
                  </span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <ThumbsUp size={14} style={{ color: 'var(--accent-primary)' }} /> 
                    {post.score} upvotes
                  </span>
                  {(post.image_metadata || post.url?.match(/\.(jpg|png|gif|webp)$/i)) && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-secondary)' }}>
                      <Camera size={14} /> Image attached
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Detail Panel */}
        {selectedPost && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', maxHeight: 'calc(100vh - 10rem)', overflowY: 'auto' }} className="fade-in">
            
            {/* Post Analysis Card */}
            <div className="card" style={{ borderTop: '3px solid var(--accent-secondary)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <div>
                  <h3 style={{ fontSize: '0.9rem', margin: 0, color: 'var(--accent-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 'bold' }}>
                    Post Analysis
                  </h3>
                  {echoStatus && echoStatus !== 'unknown' && (
                    <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Community: <span style={{ color: 'var(--accent-primary)', fontWeight: 'bold' }}>{echoStatus.toUpperCase()}</span>
                    </p>
                  )}
                </div>
                <button 
                  onClick={() => setSelectedPost(null)} 
                  style={{ 
                    background: 'var(--panel-hover)', 
                    border: '1px solid var(--panel-border)', 
                    borderRadius: '4px', 
                    color: 'var(--text-main)', 
                    cursor: 'pointer', 
                    padding: '0.4rem 0.8rem', 
                    fontSize: '0.8rem',
                    transition: 'all var(--transition-fast)'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--accent-primary)'}
                  onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--panel-border)'}
                >
                  Close
                </button>
              </div>
              
              {/* Image if present */}
              {(selectedPost.url?.match(/\.(jpg|png|gif|webp)$/i) || selectedPost.image_metadata) && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <img 
                    src={selectedPost.url} 
                    alt="Post content" 
                    style={{ width: '100%', borderRadius: '6px', border: '1px solid var(--panel-border)', display: 'block' }} 
                    onError={(e) => e.target.style.display = 'none'}
                  />
                  {selectedPost.image_metadata && (
                    <div style={{ background: 'rgba(124, 58, 237, 0.05)', padding: '0.75rem', borderRadius: '6px', marginTop: '0.75rem', borderLeft: '2px solid var(--accent-secondary)' }}>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0, marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '0.5px' }}>Visual Analysis</p>
                      <p style={{ fontSize: '0.85rem', margin: 0, color: 'var(--text-main)' }}>{selectedPost.image_metadata.caption}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Summary */}
              <div style={{ background: 'rgba(0, 217, 255, 0.05)', padding: '0.75rem', borderRadius: '6px', borderLeft: '2px solid var(--accent-primary)' }}>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0, marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 'bold', letterSpacing: '0.5px' }}>TextRank Summary</p>
                <p style={{ fontSize: '0.85rem', margin: 0, color: 'var(--text-main)', lineHeight: '1.5' }}>
                  {selectedPost.summary || 'Summary generation in progress...'}
                </p>
              </div>
            </div>

            {/* Charts */}
            <NarrativeArcChart postId={selectedPost.post_id} />
            <OpinionDivergencePanel postId={selectedPost.post_id} />

            {/* Comments Section */}
            <div className="card" style={{ borderTop: '3px solid var(--accent-secondary)', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <h3 style={{ fontSize: '0.9rem', margin: 0, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 'bold' }}>
                <MessageSquare size={14} /> 
                Comments
              </h3>

              {commentsLoading && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: '60px' }} />)}
                </div>
              )}

              {!commentsLoading && comments.length === 0 && (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '1.5rem 0', margin: 0 }}>
                  No comments available
                </p>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '400px', overflowY: 'auto' }}>
                {comments.slice(0, 10).map(c => {
                  const sentColor = getCommentSentColor(c.sentiment_label);
                  return (
                    <div 
                      key={c.comment_id} 
                      style={{ 
                        padding: '0.75rem', 
                        background: 'var(--panel-hover)', 
                        borderRadius: '4px', 
                        border: '1px solid var(--panel-border)',
                        borderLeft: `3px solid ${sentColor}`
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem', gap: '0.5rem' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-bright)' }}>
                          <User size={12} style={{ color: 'var(--accent-secondary)' }} /> 
                          {c.author?.substring(0, 12) || 'anon'}
                        </span>
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                          {c.sentiment_label && (
                            <span className="badge" style={{ fontSize: '0.65rem', background: sentColor + '20', color: sentColor, border: `1px solid ${sentColor}40` }}>
                              {c.sentiment_label.toUpperCase()}
                            </span>
                          )}
                          {c.is_toxic && (
                            <span className="badge" style={{ fontSize: '0.65rem', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.3)', display: 'flex', alignItems: 'center', gap: '2px' }}>
                              <AlertTriangle size={10} /> TOXIC
                            </span>
                          )}
                        </div>
                      </div>
                      <p style={{ fontSize: '0.8rem', lineHeight: 1.5, color: 'var(--text-main)', margin: 0, marginBottom: '0.4rem' }}>
                        {c.text?.substring(0, 150)}
                        {c.text && c.text.length > 150 ? '...' : ''}
                      </p>
                      {c.score !== undefined && (
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>↑ {c.score}</span>
                      )}
                    </div>
                  );
                })}
              </div>

              {comments.length > 10 && (
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center', margin: '0.5rem 0 0 0' }}>
                  +{comments.length - 10} more comments
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
