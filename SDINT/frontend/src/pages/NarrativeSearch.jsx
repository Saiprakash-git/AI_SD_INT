import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Globe, ChevronRight } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:5000/api' : 'https://sd-int.onrender.com/api');

export default function NarrativeSearch() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  
  const placeholders = ["AI Safety...", "OpenAI Board...", "Cyberpunk 2077 Release...", "SVB Collapse..."];
  const [phIdx, setPhIdx] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setPhIdx((p) => (p + 1) % placeholders.length), 3000);
    return () => clearInterval(t);
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query) return;
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/search/narrative?q=${encodeURIComponent(query)}`);
      setData(res.data);
    } catch(err) { }
    setLoading(false);
  };

  return (
    <div className="fade-in">
      <div style={{ textAlign: 'center', margin: '2rem 0 4rem 0' }}>
         <h2 style={{ fontSize: '2rem', marginBottom: '1rem' }}><Search size={28} color="var(--accent-primary)" style={{ verticalAlign: 'middle', marginRight: '10px' }} /> NARRATIVE SEARCH</h2>
         <form onSubmit={handleSearch} style={{ position: 'relative', maxWidth: '600px', margin: '0 auto' }}>
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={`Search as a story... e.g. ${placeholders[phIdx]}`}
              style={{ width: '100%', padding: '1rem 2rem', fontSize: '1.1rem', borderRadius: '50px', background: 'var(--panel-bg)', border: '2px solid var(--panel-border)' }}
            />
            <button type="submit" disabled={loading} style={{ position: 'absolute', right: '8px', top: '8px', bottom: '8px', borderRadius: '50px', background: 'var(--accent-primary)', color: '#000', border: 'none', padding: '0 2rem', fontWeight: 600, cursor: 'pointer' }}>
              {loading ? 'ANALYZING...' : 'EXPLORE'}
            </button>
         </form>
      </div>

      {loading && <div className="skeleton" style={{ height: '400px', maxWidth: '800px', margin: '0 auto' }} />}

      {data && !loading && (
         <div style={{ maxWidth: '900px', margin: '0 auto' }} className="fade-in">
            {/* Summary Banner */}
            <div className="card" style={{ textAlign: 'center', marginBottom: '3rem', borderLeft: '4px solid var(--accent-secondary)' }}>
               <p style={{ fontSize: '1.1rem', color: 'var(--text-bright)' }}>
                 Topic <strong className="text-accent">{data.query}</strong> first appeared <strong className="text-positive">{data.first_appeared_days_ago} days ago</strong>, 
                 peaked around <strong className="text-neutral">{data.peaked_on}</strong>. 
                 Currently sitting at <strong className="text-mixed">{data.current_sentiment.toUpperCase()}</strong> status across {data.total_posts} major conversations.
               </p>
            </div>

            {/* Vertical Timeline */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', position: 'relative', margin: '0 0 4rem 0' }}>
               <div style={{ position: 'absolute', left: '16px', top: 0, bottom: 0, width: '2px', background: 'var(--panel-border)' }} />
               
               {data.timeline.map((node, i) => {
                 const size = Math.min(node.activity_score * 2, 24) + 12; // Dynamic node sizing
                 return (
                   <div key={i} style={{ position: 'relative', paddingLeft: '4rem', display: 'flex', alignItems: 'center' }}>
                      <div style={{ 
                        position: 'absolute', left: `${17 - (size/2)}px`, width: `${size}px`, height: `${size}px`, 
                        borderRadius: '50%', background: 'var(--bg-color)', border: '2px solid var(--accent-secondary)',
                        boxShadow: `0 0 ${size}px rgba(88, 166, 255, 0.2)`
                      }} />
                      
                      <div className="card" style={{ flex: 1, padding: '1rem' }}>
                         <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                           <span className="mono bg-mixed" style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '12px', color: '#000' }}>
                             #{node.post_id}
                           </span>
                           <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{node.date}</span>
                         </div>
                         <p style={{ fontSize: '1rem', margin: 0, color: 'var(--text-bright)' }}>{node.summary}</p>
                      </div>
                   </div>
                 );
               })}
            </div>

            {/* External Web Integration */}
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1.5rem', color: 'var(--text-bright)' }}>
              <Globe color="var(--accent-secondary)" /> World News Footprint
            </h3>
            
            <div style={{ display: 'flex', gap: '1rem', overflowX: 'auto', paddingBottom: '1rem' }}>
               {data.external_news.map((news, i) => (
                  <a key={i} href={news.url} target="_blank" rel="noreferrer" className="card" style={{ minWidth: '300px', display: 'flex', flexDirection: 'column', textDecoration: 'none' }}>
                     <h4 style={{ fontSize: '0.95rem', margin: '0 0 1rem 0', color: 'var(--text-bright)', flex: 1 }}>{news.headline}</h4>
                     <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                       <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--accent-secondary)' }}>{news.source}</span>
                       <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}><ChevronRight size={14} /></span>
                     </div>
                  </a>
               ))}
               {data.external_news.length === 0 && (
                 <p className="mono" style={{ color: 'var(--text-muted)' }}>No external signals found.</p>
               )}
            </div>
         </div>
      )}
    </div>
  );
}
