import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';

const PRIORITY_COLORS = { critical:'#ff3b3b', high:'#fa709a', medium:'#fee140', low:'#43e97b' };
const STATUS_COLORS = { active:'#43e97b', paused:'#fee140', closed:'#888', archived:'#555' };

const InvestigationDashboard = ({ onSelectInvestigation }) => {
  const [investigations, setInvestigations] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({ title:'', description:'', investigator:'', priority:'medium', tags:'' });

  async function loadInvestigations() {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/investigations`);
      if (res.ok) {
        const data = await res.json();
        setInvestigations(data.investigations || []);
      }
    } catch (e) { console.error('Error:', e); }
    setLoading(false);
  }

  const createInvestigation = async () => {
    if (!formData.title.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/investigations`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({ ...formData, tags: formData.tags ? formData.tags.split(',').map(t => t.trim()) : [] })
      });
      if (res.ok) {
        const data = await res.json();
        setShowCreate(false);
        setFormData({ title:'', description:'', investigator:'', priority:'medium', tags:'' });
        loadInvestigations();
        if (onSelectInvestigation && data.investigation) onSelectInvestigation(data.investigation);
      }
    } catch (e) { console.error('Error creating:', e); }
    setLoading(false);
  };

  useEffect(() => { loadInvestigations(); }, []);

  return (
    <div>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', borderBottom:'1px solid #2a2a3a', paddingBottom:12, marginBottom:20 }}>
        <h2 style={{ margin:0, fontSize:22 }}>🕵️ Investigations</h2>
        <button onClick={() => setShowCreate(!showCreate)}
          style={{ padding:'10px 24px', background:'linear-gradient(135deg,#667eea,#764ba2)', border:'none', borderRadius:8, color:'#fff', fontSize:13, fontWeight:600, cursor:'pointer' }}
        >{showCreate ? '✕ Cancel' : '+ New Investigation'}</button>
      </div>

      {/* Create Form */}
      {showCreate && (
        <div style={{ background:'#14141e', border:'1px solid #667eea44', borderRadius:12, padding:24, marginBottom:20 }}>
          <h3 style={{ margin:'0 0 16px', fontSize:16, color:'#667eea' }}>Create Investigation</h3>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:12 }}>
            <div>
              <label style={{ fontSize:11, color:'#888', display:'block', marginBottom:4 }}>Title *</label>
              <input value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})}
                placeholder="Investigation title..."
                style={{ width:'100%', padding:'10px 14px', background:'#0a0a14', border:'1px solid #333', borderRadius:8, color:'#fff', fontSize:13, outline:'none', boxSizing:'border-box' }}
              />
            </div>
            <div>
              <label style={{ fontSize:11, color:'#888', display:'block', marginBottom:4 }}>Investigator</label>
              <input value={formData.investigator} onChange={e => setFormData({...formData, investigator: e.target.value})}
                placeholder="Your name or handle..."
                style={{ width:'100%', padding:'10px 14px', background:'#0a0a14', border:'1px solid #333', borderRadius:8, color:'#fff', fontSize:13, outline:'none', boxSizing:'border-box' }}
              />
            </div>
          </div>
          <div style={{ marginBottom:12 }}>
            <label style={{ fontSize:11, color:'#888', display:'block', marginBottom:4 }}>Description</label>
            <textarea value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})}
              placeholder="What is this investigation about? What are you looking for?"
              rows={3} style={{ width:'100%', padding:'10px 14px', background:'#0a0a14', border:'1px solid #333', borderRadius:8, color:'#fff', fontSize:13, outline:'none', resize:'vertical', boxSizing:'border-box', fontFamily:'inherit' }}
            />
          </div>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:16 }}>
            <div>
              <label style={{ fontSize:11, color:'#888', display:'block', marginBottom:4 }}>Priority</label>
              <select value={formData.priority} onChange={e => setFormData({...formData, priority: e.target.value})}
                style={{ width:'100%', padding:'10px 14px', background:'#0a0a14', border:'1px solid #333', borderRadius:8, color:'#fff', fontSize:13 }}
              >
                <option value="low">🟢 Low</option>
                <option value="medium">🟡 Medium</option>
                <option value="high">🔴 High</option>
                <option value="critical">🚨 Critical</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize:11, color:'#888', display:'block', marginBottom:4 }}>Tags (comma-separated)</label>
              <input value={formData.tags} onChange={e => setFormData({...formData, tags: e.target.value})}
                placeholder="phishing, fraud, recon..."
                style={{ width:'100%', padding:'10px 14px', background:'#0a0a14', border:'1px solid #333', borderRadius:8, color:'#fff', fontSize:13, outline:'none', boxSizing:'border-box' }}
              />
            </div>
          </div>
          <button onClick={createInvestigation} disabled={loading || !formData.title.trim()}
            style={{ padding:'12px 32px', background: !formData.title.trim() ? '#444' : 'linear-gradient(135deg,#667eea,#764ba2)', border:'none', borderRadius:8, color:'#fff', fontSize:14, fontWeight:600, cursor: !formData.title.trim() ? 'not-allowed' : 'pointer' }}
          >{loading ? '⏳ Creating...' : '🚀 Create Investigation'}</button>
        </div>
      )}

      {/* Investigation List */}
      {loading && investigations.length === 0 ? (
        <div style={{ textAlign:'center', padding:40, color:'#888' }}>⏳ Loading investigations...</div>
      ) : investigations.length === 0 ? (
        <div style={{ textAlign:'center', padding:'50px 20px', background:'#14141e', borderRadius:12, border:'1px solid #2a2a3a' }}>
          <div style={{ fontSize:48, marginBottom:16 }}>🕵️</div>
          <h3 style={{ color:'#667eea' }}>No Investigations Yet</h3>
          <p style={{ color:'#888', maxWidth:400, margin:'0 auto 20px' }}>Create your first investigation to start organizing your OSINT data collection and analysis.</p>
          <button onClick={() => setShowCreate(true)} style={{ padding:'12px 32px', background:'linear-gradient(135deg,#667eea,#764ba2)', border:'none', borderRadius:8, color:'#fff', fontSize:14, cursor:'pointer', fontWeight:600 }}>
            + Create First Investigation
          </button>
        </div>
      ) : (
        <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
          {investigations.map(inv => (
            <div key={inv.investigation_id}
              style={{ background:'#14141e', border:'1px solid #2a2a3a', borderRadius:12, padding:20, cursor:'pointer', transition:'all 0.2s' }}
              onClick={() => onSelectInvestigation && onSelectInvestigation(inv)}
              onMouseEnter={e => { e.currentTarget.style.borderColor = '#667eea'; e.currentTarget.style.background = '#1a1a2e'; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = '#2a2a3a'; e.currentTarget.style.background = '#14141e'; }}
            >
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:16 }}>
                <div style={{ flex:1 }}>
                  <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:8 }}>
                    <h3 style={{ margin:0, fontSize:17, color:'#e0e0e0' }}>{inv.title}</h3>
                    <span style={{ background: (PRIORITY_COLORS[inv.priority] || '#888') + '22', color: PRIORITY_COLORS[inv.priority] || '#888', padding:'2px 10px', borderRadius:12, fontSize:10, fontWeight:600, textTransform:'uppercase' }}>{inv.priority}</span>
                    <span style={{ background: (STATUS_COLORS[inv.status] || '#888') + '22', color: STATUS_COLORS[inv.status] || '#888', padding:'2px 10px', borderRadius:12, fontSize:10, fontWeight:600, display:'flex', alignItems:'center', gap:4 }}>
                      <span style={{ width:6, height:6, borderRadius:'50%', background: STATUS_COLORS[inv.status] || '#888' }}></span>
                      {inv.status}
                    </span>
                  </div>
                  {inv.description && <p style={{ margin:'0 0 8px', color:'#888', fontSize:13 }}>{inv.description}</p>}
                  <div style={{ display:'flex', gap:16, fontSize:12, color:'#666' }}>
                    {inv.investigator && <span>👤 {inv.investigator}</span>}
                    <span>📄 {inv.evidence_count || 0} evidence</span>
                    <span>🔗 {inv.identity_count || 0} identities</span>
                    <span>📅 {inv.created_at ? new Date(inv.created_at).toLocaleDateString() : 'N/A'}</span>
                  </div>
                  {inv.tags?.length > 0 && (
                    <div style={{ display:'flex', gap:6, marginTop:8 }}>
                      {inv.tags.map((tag, j) => <span key={j} style={{ background:'#667eea22', color:'#667eea', padding:'2px 10px', borderRadius:12, fontSize:10 }}>#{tag}</span>)}
                    </div>
                  )}
                </div>
                <div style={{ textAlign:'right', fontSize:12, color:'#555' }}>
                  <div>Threat: <strong style={{ color: inv.threat_level === 'critical' ? '#ff3b3b' : inv.threat_level === 'high' ? '#fa709a' : inv.threat_level === 'medium' ? '#fee140' : '#43e97b' }}>{inv.threat_level || 'unknown'}</strong></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default InvestigationDashboard;
