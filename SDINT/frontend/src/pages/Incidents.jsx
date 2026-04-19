import React, { useState, useEffect } from 'react';
import { AlertOctagon, TrendingUp, Clock, FileText } from 'lucide-react';
import { useDataCache } from '../DataCacheContext';

export default function Incidents() {
  const { fetchWithCache, getCached, API_BASE } = useDataCache();
  const [incidents, setIncidents] = useState(() => getCached('incidents') || []);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    fetchIncidents();
  }, []);

  const fetchIncidents = async () => {
    try {
      const data = await fetchWithCache('incidents', `${API_BASE}/incidents`);
      setIncidents(data);
    } catch(e) {}
  };

  const severityColor = (sev) => {
    if (sev > 75) return 'var(--negative)';
    if (sev > 40) return 'var(--neutral)';
    return 'var(--positive)';
  };

  return (
    <div className="fade-in">
      <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <AlertOctagon color="var(--accent-primary)" /> Detected Incidents
      </h2>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {incidents.map((inc, i) => (
          <div key={i} className="card" style={{ borderLeft: `4px solid ${severityColor(inc.severity)}` }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }} onClick={() => setExpanded(expanded === i ? null : i)} className="cursor-pointer">
              <div>
                <h3 style={{ fontSize: '1.4rem', margin: '0 0 0.5rem 0' }}>{inc.title}</h3>
                <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-muted)' }} className="mono">
                   <span style={{ fontSize: '0.8rem' }}>SEVERITY: {inc.severity}/100</span>
                   <span style={{ fontSize: '0.8rem' }}>POSTS: {inc.posts?.length}</span>
                </div>
              </div>
              
              <button className="btn-primary" style={{ padding: '0.5rem 1rem' }}>
                {expanded === i ? 'Collapse' : 'Analyze'}
              </button>
            </div>

            {/* Horizontal Timeline Overview */}
            {expanded !== i && (
               <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
                 {inc.timeline.map((node, i) => (
                    <div key={i} style={{ minWidth: '200px', background: 'var(--bg-color)', padding: '1rem', borderRadius: '4px', border: '1px solid var(--panel-border)' }}>
                       <p className="mono" style={{ fontSize: '0.75rem', color: 'var(--accent-secondary)', marginBottom: '0.5rem' }}>{node.phase.toUpperCase()}</p>
                       <p style={{ fontSize: '0.85rem', margin: 0 }}>{node.summary}</p>
                       <p className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>{node.date}</p>
                    </div>
                 ))}
               </div>
            )}

            {/* Expanded Split Pane */}
            {expanded === i && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginTop: '2rem', borderTop: '1px solid var(--panel-border)', paddingTop: '2rem' }} className="fade-in">
                
                {/* Left: Narrative Timeline */}
                <div>
                  <h4 style={{ color: 'var(--accent-primary)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <TrendingUp size={16} /> Community Reconstruction
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', position: 'relative' }}>
                    <div style={{ position: 'absolute', left: '7px', top: '10px', bottom: '10px', width: '2px', background: 'var(--panel-border)' }} />
                    
                    {inc.timeline.map((node, i) => (
                      <div key={i} style={{ position: 'relative', paddingLeft: '2rem' }}>
                        <div style={{ position: 'absolute', left: 0, top: '5px', width: '16px', height: '16px', borderRadius: '50%', background: 'var(--bg-color)', border: '3px solid var(--accent-primary)' }} />
                        <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{node.date} &bull; {node.phase}</span>
                        <p style={{ marginTop: '0.5rem', fontSize: '0.95rem' }}>{node.summary}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Right: External Coverage */}
                <div>
                   <h4 style={{ color: 'var(--accent-secondary)', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                     <FileText size={16} /> External News Coverage
                   </h4>
                   
                   {inc.news && inc.news.length > 0 ? inc.news.map((article, i) => (
                      <a href={article.url} target="_blank" rel="noreferrer" key={i} className="card" style={{ display: 'block', textDecoration: 'none', marginBottom: '1rem', background: 'var(--bg-color)' }}>
                         <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', color: 'var(--text-bright)' }}>{article.title}</h4>
                         <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                           <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--accent-secondary)' }}>{article.source}</span>
                           <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{article.date}</span>
                         </div>
                      </a>
                   )) : (
                     <div style={{ padding: '2rem', textAlign: 'center', border: '1px dashed var(--panel-border)', borderRadius: '4px' }}>
                       <p className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>NO EXTERNAL COVERAGE FOUND</p>
                     </div>
                   )}
                </div>

              </div>
            )}
            
          </div>
        ))}

        {incidents.length === 0 && (
           <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
             <AlertOctagon size={48} color="var(--text-muted)" style={{ marginBottom: '1rem' }} />
             <p className="mono" style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No incidents detected yet. Incidents are auto-generated from topic clusters with 3+ posts.</p>
           </div>
        )}
      </div>

    </div>
  );
}
