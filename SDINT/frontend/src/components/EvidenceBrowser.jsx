import React, { useState, useEffect, useCallback } from 'react';
import { API_BASE } from '../config';

const ENTITY_COLORS = {
  email:'#f093fb', username:'#667eea', domain:'#43e97b', url:'#4facfe', ip_address:'#fa709a',
  person:'#fee140', organization:'#a18cd1', phone:'#fbc2eb', location:'#00f2fe', hashtag:'#764ba2',
};
const SOURCE_COLORS = { web_search:'#4facfe', breach_data:'#fa709a', domain_intel:'#43e97b', username_discovery:'#667eea', reddit_post:'#ff6b35', manual:'#888' };

const EvidenceBrowser = () => {
  const [evidence, setEvidence] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [sourceFilter, setSourceFilter] = useState('all');
  const [selectedItem, setSelectedItem] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);

  async function loadEvidence() {
    setLoading(true);
    try {
      const [eviRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/osint/evidence?limit=100`),
        fetch(`${API_BASE}/osint/evidence/stats`)
      ]);
      if (eviRes.ok) { const data = await eviRes.json(); setEvidence(data.evidence || data || []); }
      if (statsRes.ok) setStats(await statsRes.json());
    } catch (e) { console.error('Error loading evidence:', e); }
    setLoading(false);
  }

  const applyFilters = useCallback(() => {
    let f = [...evidence];
    if (sourceFilter !== 'all') f = f.filter(e => e.source_type === sourceFilter);
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      f = f.filter(e =>
        (e.content?.title || '').toLowerCase().includes(term) ||
        (e.content?.body || '').toLowerCase().includes(term) ||
        (e.content?.url || '').toLowerCase().includes(term) ||
        (e.entities || []).some(ent => String(ent.value || '').toLowerCase().includes(term))
      );
    }
    setFiltered(f);
  }, [evidence, searchTerm, sourceFilter]);

  useEffect(() => { loadEvidence(); }, []);
  useEffect(() => { applyFilters(); }, [applyFilters]);

  const sourceTypes = [...new Set(evidence.map(e => e.source_type))];

  return (
    <div>
      <h2 style={{ marginTop:0, fontSize:22, borderBottom:'1px solid #2a2a3a', paddingBottom:12 }}>📋 Evidence Browser</h2>

      {/* Stats Bar */}
      {stats && (
        <div style={{ display:'flex', gap:12, marginBottom:16, flexWrap:'wrap' }}>
          {Object.entries(stats.by_source_type || {}).map(([type, count]) => (
            <div key={type} style={{ background: (SOURCE_COLORS[type] || '#667eea') + '18', border:`1px solid ${SOURCE_COLORS[type] || '#667eea'}44`, borderRadius:8, padding:'8px 14px', fontSize:12 }}>
              <span style={{ color: SOURCE_COLORS[type] || '#667eea', fontWeight:600 }}>{count}</span>
              <span style={{ color:'#888', marginLeft:6 }}>{type.replace(/_/g,' ')}</span>
            </div>
          ))}
          <div style={{ background:'#667eea18', border:'1px solid #667eea44', borderRadius:8, padding:'8px 14px', fontSize:12 }}>
            <span style={{ color:'#667eea', fontWeight:600 }}>{stats.total_evidence_items}</span>
            <span style={{ color:'#888', marginLeft:6 }}>total items</span>
          </div>
        </div>
      )}

      {/* Search & Filters */}
      <div style={{ display:'flex', gap:12, marginBottom:20 }}>
        <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
          placeholder="Search evidence by title, content, URL, or entity..."
          style={{ flex:1, padding:'10px 16px', background:'#14141e', border:'1px solid #333', borderRadius:8, color:'#fff', fontSize:13, outline:'none' }}
        />
        <select value={sourceFilter} onChange={e => setSourceFilter(e.target.value)}
          style={{ padding:'10px 16px', background:'#14141e', border:'1px solid #333', borderRadius:8, color:'#fff', fontSize:13 }}
        >
          <option value="all">All Sources ({evidence.length})</option>
          {sourceTypes.map(t => <option key={t} value={t}>{t.replace(/_/g,' ')} ({evidence.filter(e => e.source_type === t).length})</option>)}
        </select>
        <button onClick={loadEvidence} style={{ padding:'10px 20px', background:'#667eea', border:'none', borderRadius:8, color:'#fff', fontSize:13, cursor:'pointer', fontWeight:600 }}>
          🔄 Refresh
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#888' }}>⏳ Loading evidence...</div>
      ) : (
        <div style={{ display:'flex', gap:20 }}>
          {/* Evidence List */}
          <div style={{ flex: selectedItem ? '0 0 55%' : '1 1 auto', display:'flex', flexDirection:'column', gap:10, maxHeight:'65vh', overflowY:'auto', paddingRight:8 }}>
            {filtered.length === 0 ? (
              <div style={{ textAlign:'center', padding:40, color:'#666' }}>
                <div style={{ fontSize:36, marginBottom:12 }}>📭</div>
                <p>No evidence found. Collect data from the <strong>📡 Collect Data</strong> tab first.</p>
              </div>
            ) : filtered.map(item => (
              <div key={item.evidence_id} onClick={() => setSelectedItem(item)}
                style={{ background: selectedItem?.evidence_id === item.evidence_id ? '#1a1a3e' : '#14141e', border: `1px solid ${selectedItem?.evidence_id === item.evidence_id ? '#667eea' : '#2a2a3a'}`, borderRadius:10, padding:16, cursor:'pointer', transition:'all 0.2s' }}
                onMouseEnter={e => { if (selectedItem?.evidence_id !== item.evidence_id) e.currentTarget.style.borderColor = '#444'; }}
                onMouseLeave={e => { if (selectedItem?.evidence_id !== item.evidence_id) e.currentTarget.style.borderColor = '#2a2a3a'; }}
              >
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:12 }}>
                  <div style={{ flex:1, minWidth:0 }}>
                    <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:6 }}>
                      <span style={{ background: SOURCE_COLORS[item.source_type] || '#667eea', color:'#fff', padding:'2px 8px', borderRadius:4, fontSize:10, fontWeight:600 }}>{item.source_type?.replace(/_/g,' ')}</span>
                      <span style={{ color:'#555', fontSize:10 }}>{item.source_platform}</span>
                    </div>
                    <div style={{ fontSize:14, fontWeight:500, color:'#ddd', marginBottom:4, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{item.content?.title || 'Untitled'}</div>
                    <div style={{ fontSize:12, color:'#777', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{item.content?.body?.substring(0, 120) || ''}</div>
                    {item.entities?.length > 0 && (
                      <div style={{ display:'flex', gap:4, marginTop:6, flexWrap:'wrap' }}>
                        {item.entities.slice(0, 4).map((ent, j) => (
                          <span key={j} style={{ background:(ENTITY_COLORS[ent.type]||'#667eea')+'22', color:ENTITY_COLORS[ent.type]||'#667eea', padding:'1px 8px', borderRadius:10, fontSize:10 }}>{ent.value}</span>
                        ))}
                        {item.entities.length > 4 && <span style={{ fontSize:10, color:'#666' }}>+{item.entities.length - 4} more</span>}
                      </div>
                    )}
                  </div>
                  <div style={{ fontSize:13, fontWeight:700, color: item.confidence >= 0.8 ? '#43e97b' : item.confidence >= 0.6 ? '#fee140' : '#fa709a' }}>{Math.round((item.confidence||0)*100)}%</div>
                </div>
              </div>
            ))}
          </div>

          {/* Detail Panel */}
          {selectedItem && (
            <div style={{ flex:'0 0 42%', background:'#14141e', border:'1px solid #2a2a3a', borderRadius:12, padding:24, maxHeight:'65vh', overflowY:'auto', position:'sticky', top:0 }}>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 }}>
                <h3 style={{ margin:0, fontSize:16, color:'#667eea' }}>Evidence Details</h3>
                <button onClick={() => setSelectedItem(null)} style={{ background:'#333', border:'none', color:'#aaa', borderRadius:6, padding:'4px 12px', cursor:'pointer', fontSize:12 }}>✕ Close</button>
              </div>

              {/* Meta Info */}
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:16 }}>
                {[
                  { label:'Evidence ID', value: selectedItem.evidence_id },
                  { label:'Source', value: `${selectedItem.source_platform} (${selectedItem.source_type?.replace(/_/g,' ')})` },
                  { label:'Confidence', value: `${Math.round((selectedItem.confidence||0)*100)}%` },
                  { label:'Status', value: selectedItem.status || 'processed' },
                  { label:'Collected', value: selectedItem.timestamps?.collected_at ? new Date(selectedItem.timestamps.collected_at).toLocaleString() : 'N/A' },
                  { label:'Source ID', value: selectedItem.source_id },
                ].map((field, i) => (
                  <div key={i}>
                    <div style={{ fontSize:10, color:'#666', textTransform:'uppercase', letterSpacing:1, marginBottom:2 }}>{field.label}</div>
                    <div style={{ fontSize:13, color:'#ccc', wordBreak:'break-all' }}>{field.value}</div>
                  </div>
                ))}
              </div>

              {/* Confidence Bar */}
              <div style={{ marginBottom:16 }}>
                <div style={{ height:6, background:'#222', borderRadius:3, overflow:'hidden' }}>
                  <div style={{ height:'100%', width:`${(selectedItem.confidence||0)*100}%`, background: selectedItem.confidence >= 0.8 ? '#43e97b' : selectedItem.confidence >= 0.6 ? '#fee140' : '#fa709a', borderRadius:3, transition:'width 0.3s' }} />
                </div>
              </div>

              {/* Content */}
              <div style={{ marginBottom:16 }}>
                <div style={{ fontSize:10, color:'#666', textTransform:'uppercase', letterSpacing:1, marginBottom:6 }}>Content</div>
                <h4 style={{ margin:'0 0 8px', fontSize:15, color:'#e0e0e0' }}>{selectedItem.content?.title || 'Untitled'}</h4>
                <p style={{ margin:'0 0 8px', fontSize:13, color:'#999', lineHeight:1.7, whiteSpace:'pre-wrap' }}>{selectedItem.content?.body || 'No content body'}</p>
                {selectedItem.content?.url && (
                  <a href={selectedItem.content.url} target="_blank" rel="noreferrer" style={{ color:'#4facfe', fontSize:12, wordBreak:'break-all' }}>
                    🔗 {selectedItem.content.url}
                  </a>
                )}
              </div>

              {/* Entities */}
              {selectedItem.entities?.length > 0 && (
                <div style={{ marginBottom:16 }}>
                  <div style={{ fontSize:10, color:'#666', textTransform:'uppercase', letterSpacing:1, marginBottom:8 }}>Extracted Entities ({selectedItem.entities.length})</div>
                  <div style={{ display:'flex', flexDirection:'column', gap:6 }}>
                    {selectedItem.entities.map((ent, j) => (
                      <div key={j} style={{ display:'flex', alignItems:'center', gap:10, background:'#1a1a2e', borderRadius:6, padding:'8px 12px' }}>
                        <span style={{ background:(ENTITY_COLORS[ent.type]||'#667eea'), color:'#fff', padding:'2px 8px', borderRadius:4, fontSize:10, fontWeight:600, textTransform:'uppercase', minWidth:70, textAlign:'center' }}>{ent.type}</span>
                        <span style={{ fontSize:13, color:'#ddd', flex:1, wordBreak:'break-all' }}>{ent.value}</span>
                        <span style={{ fontSize:11, color:'#666' }}>{Math.round((ent.confidence||0)*100)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Metadata */}
              {selectedItem.metadata && Object.keys(selectedItem.metadata).length > 0 && (
                <div>
                  <div style={{ fontSize:10, color:'#666', textTransform:'uppercase', letterSpacing:1, marginBottom:8 }}>Metadata</div>
                  <div style={{ background:'#0a0a14', borderRadius:8, padding:12, fontSize:12, color:'#999' }}>
                    <pre style={{ margin:0, whiteSpace:'pre-wrap', fontFamily:'monospace' }}>{JSON.stringify(selectedItem.metadata, null, 2)}</pre>
                  </div>
                </div>
              )}

              {/* Tags */}
              {selectedItem.tags?.length > 0 && (
                <div style={{ marginTop:12, display:'flex', gap:6, flexWrap:'wrap' }}>
                  {selectedItem.tags.map((tag, j) => (
                    <span key={j} style={{ background:'#667eea22', color:'#667eea', padding:'3px 10px', borderRadius:12, fontSize:11 }}>#{tag}</span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EvidenceBrowser;
