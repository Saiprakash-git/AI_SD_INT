import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MessageSquare, AlertTriangle, ThumbsUp, Camera, User } from 'lucide-react';
import NarrativeArcChart from '../components/NarrativeArcChart';
import OpinionDivergencePanel from '../components/OpinionDivergencePanel';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:5000/api' : 'https://sd-int.onrender.com/api');

export default function Feed() {
  const [posts, setPosts] = useState([]);
  const [selectedPost, setSelectedPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [echoStatus, setEchoStatus] = useState(null);
  const [comments, setComments] = useState([]);
  const [commentsLoading, setCommentsLoading] = useState(false);

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
  }, [selectedPost]);

  useEffect(() => {
    fetchPosts();
    const interval = setInterval(fetchPosts, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchPosts = async () => {
    try {
      const res = await axios.get(`${API_BASE}/posts`);
      setPosts(res.data);
      setLoading(false);
    } catch(e) { setLoading(false); }
  };

  const getSentimentColor = (post) => {
    const s = post.sentiment?.compound || 0;
    if (s >= 0.05) return 'var(--positive)';
    if (s <= -0.05) return 'var(--negative)';
    return 'var(--neutral)';
  };

  const getCommentSentColor = (label) => {
    if (label === 'positive') return 'var(--positive)';
    if (label === 'negative') return 'var(--negative)';
    return 'var(--neutral)';
  };

  if (loading && posts.length === 0) return <div className="skeleton" style={{height: '200px'}}></div>;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: selectedPost ? '1fr 440px' : '1fr', gap: '2rem' }}>
      
      {/* Feed Column */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem', borderBottom: '1px solid var(--panel-border)', paddingBottom: '0.5rem' }}>Live Discussion Stream</h2>
        {posts.map(post => {
           const sColor = getSentimentColor(post);
           return (
             <div 
               key={post.post_id} 
               onClick={() => setSelectedPost(post)}
               className="card"
               style={{ 
                 cursor: 'pointer', 
                 borderLeft: `4px solid ${sColor}`,
                 background: selectedPost?.post_id === post.post_id ? 'var(--panel-hover)' : 'var(--panel-bg)'
               }}
             >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span className="mono" style={{ fontSize: '0.8rem', color: sColor }}>r/{post.subreddit}</span>
                  {post.is_toxic && <span className="mono text-toxic" style={{ fontSize: '0.75rem', padding: '2px 6px', background: 'rgba(255, 90, 90, 0.1)', borderRadius: '4px' }}><AlertTriangle size={12}/> TOXIC</span>}
                </div>
                
                <h3 style={{ fontSize: '1.1rem', margin: '0 0 0.5rem 0' }}>{post.title}</h3>
                
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1rem', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {post.content}
                </p>

                <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }} className="mono">
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><MessageSquare size={14} /> {post.number_of_comments}</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><ThumbsUp size={14} /> {post.score}</span>
                  {(post.image_metadata || post.url?.endsWith('.jpg')) && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--accent-secondary)' }}><Camera size={14}/> VISUAL</span>
                  )}
                </div>
             </div>
           );
        })}
      </div>

      {/* Right Detail Panel */}
      {selectedPost && (
        <div style={{ position: 'sticky', top: '2rem', height: 'calc(100vh - 4rem)', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }} className="fade-in">
          
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1rem', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                Subject Analysis
                {echoStatus && echoStatus !== 'unknown' && (
                  <span className="mono" style={{ fontSize: '0.65rem', padding: '2px 6px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', border: '1px solid var(--panel-border)', color: 'var(--text-muted)' }}>
                    SUBREDDIT: {echoStatus.toUpperCase()}
                  </span>
                )}
              </h3>
              <button 
                onClick={() => setSelectedPost(null)} 
                style={{ background: 'var(--panel-hover)', border: '1px solid var(--panel-border)', borderRadius: '4px', color: 'var(--text-main)', cursor: 'pointer', padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
              >
                Close
              </button>
            </div>
            
            {(selectedPost.url?.endsWith('.jpg') || selectedPost.url?.endsWith('.png') || selectedPost.image_metadata) && (
              <div style={{ marginBottom: '1.5rem' }}>
                <img src={selectedPost.url} style={{ width: '100%', borderRadius: '4px', border: '1px solid var(--panel-border)' }} />
                {selectedPost.image_metadata && (
                  <div style={{ background: '#0D1117', padding: '0.75rem', borderRadius: '4px', marginTop: '0.5rem' }}>
                    <p className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0 0 4px 0' }}>AI SCENE CAPTION</p>
                    <p style={{ fontSize: '0.85rem', margin: 0 }}>{selectedPost.image_metadata.caption}</p>
                  </div>
                )}
              </div>
            )}

            <div style={{ background: 'rgba(0, 194, 255, 0.05)', padding: '1rem', borderRadius: '4px', borderLeft: '2px solid var(--accent-primary)', marginBottom: '1.5rem' }}>
              <p className="mono" style={{ fontSize: '0.75rem', color: 'var(--accent-secondary)', marginBottom: '0.5rem' }}>TEXTRANK SUMMARY</p>
              <p style={{ fontSize: '0.9rem', margin: 0 }}>{selectedPost.summary || "Summary generation in progress..."}</p>
            </div>
          </div>

          <NarrativeArcChart postId={selectedPost.post_id} />
          <OpinionDivergencePanel postId={selectedPost.post_id} />

          {/* Comment Thread */}
          <div className="card">
            <h3 style={{ fontSize: '1rem', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--panel-border)', paddingBottom: '0.75rem' }}>
              <MessageSquare size={16} color="var(--accent-secondary)" /> 
              Comment Thread
              <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: 'auto' }}>
                {comments.length} loaded
              </span>
            </h3>

            {commentsLoading && <div className="skeleton" style={{ height: '100px' }} />}

            {!commentsLoading && comments.length === 0 && (
              <p className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', padding: '2rem 0' }}>
                No comments available for this post.
              </p>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {comments.map(c => {
                const sentColor = getCommentSentColor(c.sentiment_label);
                return (
                  <div key={c.comment_id} style={{ 
                    padding: '0.75rem', 
                    background: 'var(--bg-color)', 
                    borderRadius: '4px', 
                    border: '1px solid var(--panel-border)',
                    borderLeft: `3px solid ${sentColor}`
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', fontWeight: 500, color: 'var(--accent-secondary)' }}>
                        <User size={14} /> {c.author || 'anonymous'}
                      </span>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        {c.sentiment_label && (
                          <span className="mono" style={{ fontSize: '0.65rem', padding: '1px 6px', borderRadius: '4px', background: `${sentColor}15`, color: sentColor, border: `1px solid ${sentColor}40` }}>
                            {c.sentiment_label.toUpperCase()}
                          </span>
                        )}
                        {c.is_toxic && (
                          <span className="mono" style={{ fontSize: '0.65rem', padding: '1px 6px', borderRadius: '4px', background: 'rgba(255,90,90,0.1)', color: 'var(--toxic)', border: '1px solid rgba(255,90,90,0.3)' }}>
                            <AlertTriangle size={10} style={{ verticalAlign: 'middle' }} /> TOXIC
                          </span>
                        )}
                      </div>
                    </div>
                    <p style={{ fontSize: '0.85rem', lineHeight: 1.6, color: 'var(--text-main)', margin: 0 }}>{c.text}</p>
                    {c.score !== undefined && (
                      <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.5rem', display: 'inline-block' }}>
                        ↑ {c.score}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
          
        </div>
      )}

    </div>
  );
}
