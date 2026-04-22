import React, { useState } from 'react';
import { Settings, Eye, Database, Network, Zap } from 'lucide-react';
import InvestigationDashboard from '../components/InvestigationDashboard';
import EvidenceBrowser from '../components/EvidenceBrowser';
import EntityExplorer from '../components/EntityExplorer';
import DataCollector from '../components/DataCollector';

const CrawlMode = () => {
  const [activeTab, setActiveTab] = useState('investigations');
  const [selectedInvestigation, setSelectedInvestigation] = useState(null);

  const tabs = [
    { id: 'investigations', label: '🕵️ Investigations', icon: '🔍' },
    { id: 'evidence', label: '📋 Evidence', icon: '📊' },
    { id: 'entities', label: '🔗 Entities', icon: '🔀' },
    { id: 'collection', label: '📡 Collectors', icon: '⚙️' }
  ];

  return (
    <div style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: '#0a0a0a',
      color: '#fff'
    }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        borderBottom: '2px solid #667eea',
        padding: '20px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          maxWidth: '1400px',
          margin: '0 auto'
        }}>
          <div>
            <h1 style={{
              margin: 0,
              fontSize: '28px',
              fontWeight: 'bold',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              display: 'inline-block'
            }}>
              🕵️ CRAWL MODE
            </h1>
            <p style={{
              margin: '5px 0 0 0',
              fontSize: '13px',
              color: '#aaa'
            }}>
              Professional OSINT Investigation Framework
            </p>
          </div>

          <div style={{
            fontSize: '12px',
            color: '#aaa',
            textAlign: 'right'
          }}>
            <div>✓ Evidence Engine</div>
            <div>✓ Entity Resolution</div>
            <div>✓ Data Collection</div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{
        display: 'flex',
        gap: '1px',
        background: '#1a1a1a',
        borderBottom: '1px solid #333',
        overflowX: 'auto'
      }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '15px 25px',
              background: activeTab === tab.id
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : 'transparent',
              border: 'none',
              borderBottom: activeTab === tab.id ? 'none' : '1px solid transparent',
              color: '#fff',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: activeTab === tab.id ? 'bold' : 'normal',
              transition: 'all 0.3s',
              whiteSpace: 'nowrap',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
            onMouseEnter={(e) => {
              if (activeTab !== tab.id) {
                e.currentTarget.style.background = 'rgba(102, 126, 234, 0.1)';
              }
            }}
            onMouseLeave={(e) => {
              if (activeTab !== tab.id) {
                e.currentTarget.style.background = 'transparent';
              }
            }}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        background: '#0a0a0a'
      }}>
        {activeTab === 'investigations' && (
          <InvestigationDashboard onSelectInvestigation={setSelectedInvestigation} />
        )}

        {activeTab === 'evidence' && (
          <EvidenceBrowser investigationId={selectedInvestigation?.investigation_id} />
        )}

        {activeTab === 'entities' && (
          <EntityExplorer investigationId={selectedInvestigation?.investigation_id} />
        )}

        {activeTab === 'collection' && (
          <DataCollector investigationId={selectedInvestigation?.investigation_id} />
        )}
      </div>

      {/* Footer */}
      <div style={{
        background: '#1a1a1a',
        borderTop: '1px solid #333',
        padding: '15px 20px',
        fontSize: '12px',
        color: '#666'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          {selectedInvestigation ? (
            <div>
              Active Investigation: <strong>{selectedInvestigation.title}</strong> • {selectedInvestigation.status}
            </div>
          ) : (
            <div>
              Select or create an investigation to begin OSINT analysis
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CrawlMode;
