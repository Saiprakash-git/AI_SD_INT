import React, { useState } from 'react';
import { API_BASE } from '../config';

const ENTITY_COLORS = {
  email:'#f093fb', username:'#667eea', domain:'#43e97b', url:'#4facfe', ip_address:'#fa709a',
  person:'#fee140', organization:'#a18cd1', phone:'#fbc2eb', location:'#00f2fe', hashtag:'#764ba2',
};

const DataCollector = ({ investigationId, onCollectionComplete }) => {
  const [activeSource, setActiveSource] = useState('web');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({ query:'', username:'', email:'', domain:'' });

  const sources = [
    { id:'web', label:'🌐 Web Search', desc:'Search the web via DuckDuckGo for OSINT intelligence', field:'query', placeholder:'e.g. "john doe" site:linkedin.com OR phishing attack 2024' },
    { id:'username', label:'👤 Username Lookup', desc:'Search for a username across social media platforms', field:'username', placeholder:'e.g. johndoe123' },
    { id:'breach', label:'🔓 Breach Check', desc:'Check if an email appears in known data breaches', field:'email', placeholder:'e.g. user@example.com' },
    { id:'domain', label:'🛡️ Domain Intel', desc:'Gather WHOIS, DNS, SSL data for a domain', field:'domain', placeholder:'e.g. example.com' },
  ];

  const runCollection = async () => {
    const src = sources.find(s => s.id === activeSource);
    const value = formData[src.field]?.trim();
    if (!value) { setError(`Please enter a ${src.field}`); return; }

    setLoading(true); setError(''); setResults(null);

    const endpoints = {
      web: { url: `${API_BASE}/collect/web`, body: { query: value, investigation_id: investigationId } },
      username: { url: `${API_BASE}/collect/username`, body: { username: value, investigation_id: investigationId } },
      breach: { url: `${API_BASE}/collect/breach`, body: { query: value, investigation_id: investigationId } },
      domain: { url: `${API_BASE}/collect/domain`, body: { domain: value, investigation_id: investigationId } },
    };

    try {
      const ep = endpoints[activeSource];
      const res = await fetch(ep.url, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(ep.body) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Collection failed');
      setResults(data);
      if (onCollectionComplete) onCollectionComplete();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const currentSource = sources.find(s => s.id === activeSource);
  const items = results?.results || [];
  const stored = results?.stored_count || 0;

  const allEntities = items.flatMap(item => item.entities || []);
  const entitySummary = {};
  allEntities.forEach(e => { entitySummary[e.type] = (entitySummary[e.type] || 0) + 1; });

  return (
    <div>
      <h2 style={{ marginTop:0, fontSize:22, borderBottom:'1px solid #2a2a3a', paddingBottom:12 }}>📡 Data Collection</h2>

      {/* Source Tabs */}
      <div style={{ display:'flex', gap:8, marginBottom:20, flexWrap:'wrap' }}>
        {sources.map(src => (
          <button key={src.id} onClick={() => { setActiveSource(src.id); setResults(null); setError(''); }}
            style={{ padding:'10px 20px', background: activeSource === src.id ? 'linear-gradient(135deg,#667eea,#764ba2)' : '#1a1a2e', border: activeSource === src.id ? 'none' : '1px solid #2a2a3a', borderRadius:8, color:'#fff', cursor:'pointer', fontSize:13, fontWeight: activeSource === src.id ? 600 : 400, transition:'all 0.2s' }}
          >{src.label}</button>
        ))}
      </div>

      {/* Search Form */}
      <div style={{ background:'#14141e', border:'1px solid #2a2a3a', borderRadius:12, padding:24, marginBottom:20 }}>
        <p style={{ color:'#888', fontSize:13, margin:'0 0 12px' }}>{currentSource.desc}</p>
        <div style={{ display:'flex', gap:12 }}>
          <input value={formData[currentSource.field]} onChange={e => setFormData({...formData, [currentSource.field]: e.target.value})}
            placeholder={currentSource.placeholder}
            onKeyDown={e => e.key === 'Enter' && runCollection()}
            style={{ flex:1, padding:'12px 16px', background:'#0a0a14', border:'1px solid #333', borderRadius:8, color:'#fff', fontSize:14, outline:'none' }}
          />
          <button onClick={runCollection} disabled={loading}
            style={{ padding:'12px 32px', background: loading ? '#444' : 'linear-gradient(135deg,#667eea,#764ba2)', border:'none', borderRadius:8, color:'#fff', fontSize:14, fontWeight:600, cursor: loading ? 'wait' : 'pointer', minWidth:140 }}
          >{loading ? '⏳ Collecting...' : '🔍 Collect'}</button>
        </div>
        {error && <p style={{ color:'#fa709a', fontSize:13, marginTop:8 }}>❌ {error}</p>}
      </div>

      {/* Results */}
      {results && (
        <div>
          {/* Summary Banner */}
          <div style={{ background:'linear-gradient(135deg, #1a1a2e, #16213e)', border:'1px solid #2a2a3a', borderRadius:12, padding:20, marginBottom:20 }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', flexWrap:'wrap', gap:16 }}>
              <div>
                <h3 style={{ margin:0, color:'#43e97b', fontSize:18 }}>✅ Collection Complete</h3>
                <p style={{ margin:'6px 0 0', color:'#aaa', fontSize:13 }}>
                  Found <strong style={{ color:'#fff' }}>{items.length}</strong> results • Stored <strong style={{ color:'#43e97b' }}>{stored}</strong> to evidence database
                  {investigationId && <> • Linked to investigation <strong style={{ color:'#667eea' }}>{investigationId}</strong></>}
                </p>
              </div>
              <div style={{ display:'flex', gap:12, flexWrap:'wrap' }}>
                {Object.entries(entitySummary).map(([type, count]) => (
                  <div key={type} style={{ background: (ENTITY_COLORS[type] || '#667eea') + '22', color: ENTITY_COLORS[type] || '#667eea', padding:'6px 14px', borderRadius:20, fontSize:12, fontWeight:600 }}>
                    {type}: {count}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Result Cards */}
          <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
            {items.map((item, idx) => (
              <div key={item.evidence_id || idx} style={{ background:'#14141e', border:'1px solid #2a2a3a', borderRadius:12, padding:20, transition:'border-color 0.2s' }}
                onMouseEnter={e => e.currentTarget.style.borderColor = '#667eea'} onMouseLeave={e => e.currentTarget.style.borderColor = '#2a2a3a'}
              >
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:16 }}>
                  <div style={{ flex:1 }}>
                    {/* Title */}
                    <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:8 }}>
                      <span style={{ background:'#667eea33', color:'#667eea', padding:'2px 10px', borderRadius:4, fontSize:10, fontWeight:600, textTransform:'uppercase' }}>{item.source_type?.replace(/_/g,' ')}</span>
                      <span style={{ color:'#555', fontSize:11 }}>ID: {item.evidence_id?.substring(0, 16)}...</span>
                    </div>
                    <h4 style={{ margin:'0 0 8px', fontSize:16, color:'#e8e8e8', lineHeight:1.4 }}>{item.content?.title || 'Untitled'}</h4>

                    {/* Body */}
                    <p style={{ margin:'0 0 10px', color:'#999', fontSize:13, lineHeight:1.6 }}>
                      {item.content?.body ? (item.content.body.length > 300 ? item.content.body.substring(0, 300) + '...' : item.content.body) : 'No description available'}
                    </p>

                    {/* URL */}
                    {item.content?.url && (
                      <a href={item.content.url} target="_blank" rel="noreferrer"
                        style={{ color:'#4facfe', fontSize:12, textDecoration:'none', wordBreak:'break-all', display:'inline-flex', alignItems:'center', gap:4 }}
                      >🔗 {item.content.url.length > 80 ? item.content.url.substring(0, 80) + '...' : item.content.url}</a>
                    )}

                    {/* Entities */}
                    {item.entities?.length > 0 && (
                      <div style={{ marginTop:10, display:'flex', gap:6, flexWrap:'wrap' }}>
                        {item.entities.map((ent, j) => (
                          <span key={j} style={{ background: (ENTITY_COLORS[ent.type] || '#667eea') + '22', color: ENTITY_COLORS[ent.type] || '#667eea', padding:'3px 10px', borderRadius:12, fontSize:11, fontWeight:500, border:`1px solid ${(ENTITY_COLORS[ent.type] || '#667eea')}44` }}>
                            {ent.type}: {ent.value}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Confidence Badge */}
                  <div style={{ textAlign:'center', minWidth:60 }}>
                    <div style={{ width:52, height:52, borderRadius:'50%', border:`3px solid ${item.confidence >= 0.8 ? '#43e97b' : item.confidence >= 0.6 ? '#fee140' : '#fa709a'}`, display:'flex', alignItems:'center', justifyContent:'center', fontSize:14, fontWeight:700, color: item.confidence >= 0.8 ? '#43e97b' : item.confidence >= 0.6 ? '#fee140' : '#fa709a' }}>
                      {Math.round((item.confidence || 0) * 100)}%
                    </div>
                    <div style={{ fontSize:10, color:'#666', marginTop:4 }}>confidence</div>
                  </div>
                </div>

                {/* Metadata */}
                {item.metadata && Object.keys(item.metadata).length > 0 && (
                  <div style={{ marginTop:12, paddingTop:12, borderTop:'1px solid #222', display:'flex', gap:16, flexWrap:'wrap' }}>
                    {Object.entries(item.metadata).map(([k, v]) => (
                      <span key={k} style={{ fontSize:11, color:'#666' }}><strong style={{ color:'#888' }}>{k.replace(/_/g,' ')}:</strong> {typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          {items.length === 0 && (
            <div style={{ textAlign:'center', padding:40, color:'#666' }}>
              <div style={{ fontSize:36, marginBottom:12 }}>🤷</div>
              <p>No results found for this query. Try a different search term.</p>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!results && !loading && (
        <div style={{ textAlign:'center', padding:'50px 20px', color:'#555' }}>
          <div style={{ fontSize:48, marginBottom:16 }}>📡</div>
          <h3 style={{ color:'#888' }}>Ready to Collect Intelligence</h3>
          <p style={{ maxWidth:500, margin:'0 auto' }}>Enter a query above and click Collect. Results will be stored as evidence items with automatically extracted entities.</p>
        </div>
      )}
    </div>
  );
};

export default DataCollector;
