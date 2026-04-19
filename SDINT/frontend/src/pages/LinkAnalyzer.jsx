import React, { useState } from 'react';
import axios from 'axios';
import { Link2, ShieldAlert, Cpu, Database, Globe } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:5000/api' : 'https://sd-int.onrender.com/api');

export default function LinkAnalyzer() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!url) return;
    setLoading(true);
    setError('');
    setData(null);
    try {
      const res = await axios.post(`${API_BASE}/analyze-link`, { url });
      if (res.data.error) setError(res.data.error);
      else setData(res.data);
    } catch(err) {
      setError('Failed to analyze the provided URL. Ensure it is publicly accessible.');
    }
    setLoading(false);
  };

  const getSentColor = (sent) => {
    if (!sent) return 'var(--neutral)';
    if (sent.compound >= 0.05) return 'var(--positive)';
    if (sent.compound <= -0.05) return 'var(--negative)';
    return 'var(--neutral)';
  };

  return (
    <div className="fade-in">
      <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Link2 color="var(--accent-primary)" /> Universal Link Analyzer
      </h2>

      <form onSubmit={handleAnalyze} style={{ display: 'flex', gap: '1rem', marginBottom: '3rem' }}>
         <input 
           type="url" 
           value={url}
           onChange={(e) => setUrl(e.target.value)}
           placeholder="Paste any public URL (News, YouTube, Reddit...)"
           style={{ flex: 1, padding: '1rem 1.5rem', fontSize: '1rem', borderRadius: '4px' }}
           required
         />
         <button className="btn-primary" type="submit" disabled={loading} style={{ padding: '0 2rem' }}>
            {loading ? 'FINGERPRINTING...' : 'ANALYZE'}
         </button>
      </form>

      {error && <div className="card text-negative bg-negative" style={{ color: '#fff', background: 'rgba(231, 76, 60, 0.1)', border: '1px solid var(--negative)' }}>{error}</div>}

      {loading && (
        <div style={{ textAlign: 'center', margin: '4rem 0' }} className="fade-in">
           <Cpu size={48} color="var(--accent-secondary)" className="spin" />
           <p className="mono" style={{ color: 'var(--text-muted)', marginTop: '1rem' }}>Extracting → Analyzing → Cross-Referencing</p>
           <div className="skeleton" style={{ height: '300px', marginTop: '2rem' }} />
        </div>
      )}

      {data && !loading && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }} className="fade-in">
           
           {/* Column 1: Extraction Base */}
           <div className="card" style={{ borderTop: '4px solid var(--accent-primary)' }}>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Cpu size={18} /> Extracted Fingerprint
              </h3>
              
              <div style={{ marginBottom: '1.5rem' }}>
                 <h4 style={{ fontSize: '1rem', color: 'var(--text-bright)', marginBottom: '0.5rem' }}>{data.content_summary?.title}</h4>
                 <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{data.content_summary?.preview}</p>
                 <a href={data.url} target="_blank" rel="noreferrer" className="mono" style={{ fontSize: '0.75rem', color: 'var(--accent-secondary)', textDecoration: 'none' }}>SOURCE LINK &rarr;</a>
              </div>
              
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '4px', border: '1px solid var(--panel-border)' }}>
                 <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SENTIMENT SCORE</span>
                    <span className="mono" style={{ fontSize: '0.85rem', color: getSentColor(data.sentiment) }}>
                      {data.sentiment ? data.sentiment.compound.toFixed(2) : "N/A"}
                    </span>
                 </div>
                 {data.is_toxic && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--toxic)', marginTop: '1rem', background: 'rgba(255, 90, 90, 0.1)', padding: '0.5rem', borderRadius: '4px' }}>
                       <ShieldAlert size={16} /> HIGH TOXICITY DETECTED
                    </div>
                 )}
              </div>
           </div>

           {/* Column 2: Internal Database */}
           <div className="card" style={{ borderTop: '4px solid var(--accent-secondary)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                 <h3 style={{ fontSize: '1.1rem', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Database size={18} /> Internal Heatmap
                 </h3>
                 <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--positive)', background: 'rgba(46, 204, 113, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>
                    {data.confidence_score}% CONFIDENCE
                 </span>
              </div>
              
              {data.internal_matches.length > 0 ? (
                 <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {data.internal_matches.map((match, i) => (
                       <div key={i} style={{ padding: '0.75rem', background: 'var(--bg-color)', borderRadius: '4px', border: '1px solid var(--panel-border)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                             <span className="mono" style={{ color: 'var(--accent-secondary)', fontSize: '0.75rem' }}>r/{match.subreddit}</span>
                             <span className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{match.similarity}% SIMILAR</span>
                          </div>
                          <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.85rem' }}>{match.title}</p>
                       </div>
                    ))}
                 </div>
              ) : (
                <p className="mono" style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '4rem' }}>No internal conversations matched.</p>
              )}
           </div>

           {/* Column 3: External Web */}
           <div className="card" style={{ borderTop: '4px solid var(--text-muted)' }}>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Globe size={18} /> External Propagation
              </h3>
              
              {data.external_web.length > 0 ? (
                 <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {data.external_web.map((web, i) => (
                       <a key={i} href={web.href || web.url} target="_blank" rel="noreferrer" style={{ display: 'block', textDecoration: 'none', padding: '0.75rem', background: 'var(--bg-color)', borderRadius: '4px', border: '1px solid var(--panel-border)' }}>
                          <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.85rem', color: 'var(--text-bright)' }}>{web.title}</h4>
                          <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-muted)', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                            {web.body || web.snippet}
                          </p>
                       </a>
                    ))}
                 </div>
              ) : (
                <p className="mono" style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '4rem' }}>No external tracking found.</p>
              )}
           </div>

        </div>
      )}

    </div>
  );
}
