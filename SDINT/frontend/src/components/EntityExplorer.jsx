import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const ENTITY_COLORS = {
  email:'#f093fb', username:'#667eea', domain:'#43e97b', url:'#4facfe', ip_address:'#fa709a',
  person:'#fee140', organization:'#a18cd1', phone:'#fbc2eb', location:'#00f2fe', hashtag:'#764ba2',
};
const COLORS_LIST = Object.values(ENTITY_COLORS);

const EntityExplorer = () => {
  const [stats, setStats] = useState(null);
  const [searchType, setSearchType] = useState('email');
  const [searchValue, setSearchValue] = useState('');
  const [pivotResults, setPivotResults] = useState(null);
  const [entityEvidence, setEntityEvidence] = useState([]);
  const [loading, setLoading] = useState(false);

  const entityTypes = ['email','username','domain','url','phone','ip_address','person','organization','location','hashtag'];

  async function loadStats() {
    try {
      const res = await fetch(`${API_BASE}/osint/evidence/stats`);
      if (res.ok) setStats(await res.json());
    } catch (e) { console.error('Error loading stats:', e); }
  }

  const searchEntity = async (type = searchType, value = searchValue) => {
    if (!value.trim()) return;
    setLoading(true);
    setPivotResults(null);
    setEntityEvidence([]);

    try {
      // Run pivot analysis and evidence search in parallel
      const [pivotRes, evidenceRes] = await Promise.all([
        fetch(`${API_BASE}/analyze/pivot`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type,
            value,
            depth: 2
          })
        }),
        fetch(`${API_BASE}/osint/evidence/by-entity?type=${type}&value=${encodeURIComponent(value)}`)
      ]);

      if (pivotRes.ok) {
        const data = await pivotRes.json();
        setPivotResults(data);
      }
      if (evidenceRes.ok) {
        const data = await evidenceRes.json();
        setEntityEvidence(data.evidence || data || []);
      }
    } catch (e) {
      console.error('Entity search error:', e);
    }
    setLoading(false);
  };

  const handleEntityClick = (type, value) => {
    setSearchType(type);
    setSearchValue(value);
    searchEntity(type, value);
  };

  useEffect(() => { loadStats(); }, []);

  const topEntities = stats?.top_entities || [];
  const entityDistribution = stats?.entity_type_distribution
    ? Object.entries(stats.entity_type_distribution).map(([name, value]) => ({ name, value }))
    : [];
  const totalEntities = entityDistribution.reduce((sum, e) => sum + e.value, 0);

  return (
    <div>
      <h2 style={{ marginTop:0, fontSize:22, borderBottom:'1px solid #2a2a3a', paddingBottom:12 }}>🔗 Entity Explorer</h2>

      {/* Entity Overview */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20, marginBottom:24 }}>
        {/* Distribution Chart */}
        <div style={{ background:'#14141e', border:'1px solid #2a2a3a', borderRadius:12, padding:20 }}>
          <h3 style={{ margin:'0 0 12px', fontSize:14, color:'#ccc' }}>Entity Distribution ({totalEntities} total)</h3>
          {entityDistribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={entityDistribution} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value"
                  label={({ name, percent }) => percent > 0.05 ? `${name} ${(percent*100).toFixed(0)}%` : ''} labelLine={false}
                >
                  {entityDistribution.map((entry, i) => <Cell key={i} fill={ENTITY_COLORS[entry.name] || COLORS_LIST[i % COLORS_LIST.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background:'#1a1a2e', border:'1px solid #333', borderRadius:8, color:'#fff' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign:'center', padding:40, color:'#555' }}>No entities yet. Collect data first.</div>
          )}
        </div>

        {/* Top Entities List */}
        <div style={{ background:'#14141e', border:'1px solid #2a2a3a', borderRadius:12, padding:20 }}>
          <h3 style={{ margin:'0 0 12px', fontSize:14, color:'#ccc' }}>Top Entities (click to investigate)</h3>
          <div style={{ display:'flex', flexDirection:'column', gap:6, maxHeight:200, overflowY:'auto' }}>
            {topEntities.length > 0 ? topEntities.map((ent, i) => (
              <div key={i} onClick={() => handleEntityClick(ent.type, ent.value)}
                style={{ display:'flex', alignItems:'center', gap:10, padding:'8px 12px', background:'#1a1a2e', borderRadius:6, cursor:'pointer', transition:'background 0.2s', border:'1px solid transparent' }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = ENTITY_COLORS[ent.type] || '#667eea'; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'transparent'; }}
              >
                <span style={{ background: ENTITY_COLORS[ent.type] || '#667eea', color:'#fff', padding:'2px 8px', borderRadius:4, fontSize:10, fontWeight:600, textTransform:'uppercase', minWidth:65, textAlign:'center' }}>{ent.type}</span>
                <span style={{ flex:1, fontSize:13, color:'#ddd' }}>{ent.value}</span>
                <span style={{ background:'#667eea22', color:'#667eea', padding:'3px 10px', borderRadius:12, fontSize:11, fontWeight:600 }}>{ent.count}×</span>
              </div>
            )) : (
              <div style={{ textAlign:'center', padding:20, color:'#555', fontSize:13 }}>No entities found. Collect data to extract entities.</div>
            )}
          </div>
        </div>
      </div>

      {/* Search */}
      <div style={{ background:'#14141e', border:'1px solid #2a2a3a', borderRadius:12, padding:20, marginBottom:20 }}>
        <h3 style={{ margin:'0 0 12px', fontSize:14, color:'#ccc' }}>🔍 Investigate Entity</h3>
        <p style={{ color:'#777', fontSize:12, margin:'0 0 12px' }}>Search for an entity to discover related entities, co-occurrences, and suggested next investigation steps.</p>
        <div style={{ display:'flex', gap:10 }}>
          <select value={searchType} onChange={e => setSearchType(e.target.value)}
            style={{ padding:'10px 14px', background:'#0a0a14', border:'1px solid #333', borderRadius:8, color:'#fff', fontSize:13 }}
          >
            {entityTypes.map(t => <option key={t} value={t}>{t.replace(/_/g,' ')}</option>)}
          </select>
          <input value={searchValue} onChange={e => setSearchValue(e.target.value)}
            placeholder="Enter entity value to investigate..."
            onKeyDown={e => e.key === 'Enter' && searchEntity()}
            style={{ flex:1, padding:'10px 16px', background:'#0a0a14', border:'1px solid #333', borderRadius:8, color:'#fff', fontSize:13, outline:'none' }}
          />
          <button onClick={searchEntity} disabled={loading}
            style={{ padding:'10px 24px', background: loading ? '#444' : 'linear-gradient(135deg,#667eea,#764ba2)', border:'none', borderRadius:8, color:'#fff', fontSize:13, fontWeight:600, cursor: loading ? 'wait' : 'pointer' }}
          >{loading ? '⏳...' : '🔍 Analyze'}</button>
        </div>
      </div>

      {/* Results */}
      {(pivotResults || entityEvidence.length > 0) && (
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20 }}>
          {/* Evidence for this Entity */}
          <div style={{ background:'#14141e', border:'1px solid #2a2a3a', borderRadius:12, padding:20 }}>
            <h3 style={{ margin:'0 0 12px', fontSize:14, color:'#4facfe' }}>📋 Evidence Mentioning "{searchValue}" ({entityEvidence.length} items)</h3>
            <div style={{ display:'flex', flexDirection:'column', gap:8, maxHeight:400, overflowY:'auto' }}>
              {entityEvidence.length > 0 ? entityEvidence.map((item, i) => (
                <div key={i} style={{ background:'#1a1a2e', borderRadius:8, padding:12, borderLeft:'3px solid ' + (ENTITY_COLORS[searchType] || '#667eea') }}>
                  <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:4 }}>
                    <span style={{ fontSize:10, color:'#888', background:'#333', padding:'1px 6px', borderRadius:3 }}>{item.source_type?.replace(/_/g,' ')}</span>
                    <span style={{ fontSize:10, color:'#555' }}>{item.evidence_id?.substring(0, 16)}</span>
                  </div>
                  <div style={{ fontSize:13, color:'#ddd', marginBottom:4 }}>{item.content?.title || 'Untitled'}</div>
                  <div style={{ fontSize:11, color:'#888' }}>{item.content?.body?.substring(0, 150) || ''}</div>
                  {item.content?.url && <a href={item.content.url} target="_blank" rel="noreferrer" style={{ fontSize:11, color:'#4facfe', textDecoration:'none', display:'block', marginTop:4 }}>🔗 {item.content.url.substring(0, 60)}...</a>}
                </div>
              )) : (
                <div style={{ textAlign:'center', padding:20, color:'#555', fontSize:13 }}>No evidence references this entity directly.</div>
              )}
            </div>
          </div>

          {/* Pivot Suggestions */}
          <div style={{ background:'#14141e', border:'1px solid #2a2a3a', borderRadius:12, padding:20 }}>
            <h3 style={{ margin:'0 0 12px', fontSize:14, color:'#43e97b' }}>🔗 Related Entities & Pivot Suggestions</h3>
            {pivotResults?.suggestions?.length > 0 ? (
              <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
                {pivotResults.suggestions.map((sug, i) => (
                  <div key={i} style={{ background:'#1a1a2e', borderRadius:8, padding:14, border:'1px solid #2a2a3a' }}>
                    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8 }}>
                      <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                        <span style={{ background: ENTITY_COLORS[sug.to_entity?.type] || '#667eea', color:'#fff', padding:'2px 8px', borderRadius:4, fontSize:10, fontWeight:600, textTransform:'uppercase' }}>{sug.to_entity?.type}</span>
                        <span style={{ fontSize:14, fontWeight:500, color:'#e0e0e0', cursor:'pointer' }}
                          onClick={() => handleEntityClick(sug.to_entity?.type, sug.to_entity?.value)}
                        >{sug.to_entity?.value}</span>
                      </div>
                      <div style={{ background: sug.strength > 0.5 ? '#43e97b22' : '#fee14022', color: sug.strength > 0.5 ? '#43e97b' : '#fee140', padding:'3px 10px', borderRadius:12, fontSize:11, fontWeight:600 }}>
                        {Math.round((sug.strength||0)*100)}% link
                      </div>
                    </div>
                    <p style={{ margin:'0 0 8px', fontSize:12, color:'#888' }}>{sug.justification}</p>
                    {sug.next_steps?.length > 0 && (
                      <div>
                        <div style={{ fontSize:10, color:'#667eea', marginBottom:4, fontWeight:600 }}>SUGGESTED NEXT STEPS:</div>
                        {sug.next_steps.map((step, j) => (
                          <div key={j} style={{ fontSize:11, color:'#999', padding:'2px 0', paddingLeft:12, borderLeft:'2px solid #333' }}>→ {step}</div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign:'center', padding:30, color:'#555' }}>
                <div style={{ fontSize:28, marginBottom:8 }}>🕸️</div>
                <p style={{ fontSize:13 }}>No pivot connections found for this entity yet. Collect more data to build entity relationships.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default EntityExplorer;
