import React from 'react';
import { Shield, Zap, Target } from 'lucide-react';
import InvestigationMode from '../components/InvestigationMode';

const CrawlMode = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Page Header - Integrated into new theme */}
      <div className="glass-panel" style={{
        margin: '0.5rem',
        marginBottom: 0,
        borderRadius: '12px 12px 0 0',
        borderTop: '3px solid var(--accent-primary)',
        padding: '1.5rem 2rem'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '2rem'
        }}>
          <div>
            <h1 style={{
              margin: 0,
              fontSize: '1.8rem',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              color: 'var(--text-bright)'
            }}>
              <Target size={32} style={{ color: 'var(--accent-primary)' }} />
              OSINT Investigation Center
            </h1>
            <p style={{
              margin: '0.5rem 0 0 0',
              color: 'var(--text-muted)',
              fontSize: '0.95rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <Zap size={14} /> Advanced identity discovery across 10+ data connectors
            </p>
          </div>

          {/* Quick Stats */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '1.5rem',
            minWidth: '280px',
            padding: '1rem 0'
          }}>
            {[
              { label: 'Data Connectors', value: '10+' },
              { label: 'Evidence Types', value: '50+' },
              { label: 'Platforms', value: 'Real-time' }
            ].map((stat, i) => (
              <div key={i} style={{ textAlign: 'right' }}>
                <div style={{
                  fontSize: '0.8rem',
                  color: 'var(--text-muted)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  fontWeight: 'bold'
                }}>
                  {stat.label}
                </div>
                <div style={{
                  fontSize: '1.2rem',
                  color: 'var(--accent-primary)',
                  fontWeight: 'bold',
                  marginTop: '0.25rem'
                }}>
                  {stat.value}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Content Area - Fills remaining space */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        margin: '0 0.5rem 0.5rem 0.5rem'
      }}>
        <InvestigationMode />
      </div>
    </div>
  );
};

export default CrawlMode;
