import React, { useState, useEffect } from 'react';
import { Search, GitBranch, Layers, AlertCircle } from 'lucide-react';

const EntityExplorer = ({ investigationId }) => {
  const [entities, setEntities] = useState([]);
  const [searchEntity, setSearchEntity] = useState('');
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [relatedEntities, setRelatedEntities] = useState([]);
  const [entityType, setEntityType] = useState('email');
  const [loading, setLoading] = useState(false);
  const API = 'http://localhost:5000/api';

  const entityTypes = [
    'email', 'username', 'URL', 'phone', 'domain',
    'person', 'organization', 'location', 'IP_ADDRESS',
    'date', 'hashtag', 'subreddit', 'crypto_wallet'
  ];

  useEffect(() => {
    loadMockEntities();
  }, []);

  const loadMockEntities = () => {
    setEntities([
      { type: 'email', value: 'phisher@fake.com', confidence: 0.95, evidence_count: 3 },
      { type: 'email', value: 'victim@example.com', confidence: 0.99, evidence_count: 5 },
      { type: 'username', value: 'suspicious_user_001', confidence: 0.87, evidence_count: 2 },
      { type: 'domain', value: 'malicious-domain.ru', confidence: 0.92, evidence_count: 4 },
      { type: 'IP_ADDRESS', value: '192.168.1.100', confidence: 0.88, evidence_count: 2 },
      { type: 'person', value: 'John Doe', confidence: 0.75, evidence_count: 1 }
    ]);
  };

  const handleEntitySearch = async () => {
    if (!searchEntity.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(
        `${API}/analyze/pivot?type=${entityType}&value=${encodeURIComponent(searchEntity)}&depth=2`
      );
      
      if (response.ok) {
        const data = await response.json();
        setSelectedEntity({ type: entityType, value: searchEntity });
        setRelatedEntities(data.suggestions || []);
      }
    } catch (error) {
      console.error('Error searching entity:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEntityColor = (type) => {
    const colors = {
      email: '#FF5722',
      username: '#2196F3',
      URL: '#4CAF50',
      phone: '#FF9800',
      domain: '#9C27B0',
      person: '#F44336',
      organization: '#00BCD4',
      location: '#CDDC39',
      IP_ADDRESS: '#3F51B5',
      date: '#673AB7',
      hashtag: '#E91E63',
      subreddit: '#FF6F00',
      crypto_wallet: '#1B5E20'
    };
    return colors[type] || '#999';
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h2 style={{ marginTop: 0 }}>🔗 Entity Explorer</h2>

      <div style={{
        background: '#1a1a1a',
        border: '1px solid #333',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '20px'
      }}>
        <h3>Search Entities</h3>
        <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
          <select
            value={entityType}
            onChange={(e) => setEntityType(e.target.value)}
            style={{
              padding: '10px 15px',
              background: '#2a2a2a',
              border: '1px solid #444',
              borderRadius: '4px',
              color: '#fff',
              cursor: 'pointer'
            }}
          >
            {entityTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>

          <input
            type="text"
            placeholder={`Enter ${entityType}...`}
            value={searchEntity}
            onChange={(e) => setSearchEntity(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleEntitySearch()}
            style={{
              flex: 1,
              padding: '10px 15px',
              background: '#2a2a2a',
              border: '1px solid #444',
              borderRadius: '4px',
              color: '#fff'
            }}
          />

          <button
            onClick={handleEntitySearch}
            disabled={loading}
            style={{
              padding: '10px 20px',
              background: '#667eea',
              border: 'none',
              borderRadius: '4px',
              color: '#fff',
              cursor: 'pointer'
            }}
          >
            {loading ? '🔍 Analyzing...' : '🔍 Analyze'}
          </button>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '15px'
      }}>
        <div>
          <h3>Collected Entities</h3>
          <div style={{
            background: '#1a1a1a',
            border: '1px solid #333',
            borderRadius: '8px',
            overflow: 'hidden'
          }}>
            {entities.map((ent, idx) => (
              <div
                key={idx}
                onClick={() => {
                  setSearchEntity(ent.value);
                  setEntityType(ent.type);
                }}
                style={{
                  padding: '12px 15px',
                  borderBottom: '1px solid #333',
                  cursor: 'pointer',
                  background: selectedEntity?.value === ent.value ? '#2a2a3a' : 'transparent',
                  transition: 'background 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = selectedEntity?.value === ent.value ? '#2a2a3a' : '#252525'}
                onMouseLeave={(e) => e.currentTarget.style.background = selectedEntity?.value === ent.value ? '#2a2a3a' : 'transparent'}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span
                      style={{
                        background: getEntityColor(ent.type),
                        color: '#fff',
                        padding: '3px 8px',
                        borderRadius: '3px',
                        fontSize: '11px',
                        marginRight: '8px'
                      }}
                    >
                      {ent.type}
                    </span>
                    <span style={{ fontSize: '13px' }}>{ent.value}</span>
                  </div>
                  <span style={{ fontSize: '11px', color: '#888' }}>
                    {ent.evidence_count} refs
                  </span>
                </div>
                <div style={{
                  fontSize: '11px',
                  color: '#666',
                  marginTop: '5px'
                }}>
                  🎯 {(ent.confidence * 100).toFixed(0)}% confidence
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3>Entity Relationships</h3>
          <div style={{
            background: '#1a1a1a',
            border: '1px solid #333',
            borderRadius: '8px',
            padding: '15px'
          }}>
            {selectedEntity ? (
              <>
                <div style={{
                  background: '#2a2a2a',
                  padding: '15px',
                  borderRadius: '4px',
                  marginBottom: '15px'
                }}>
                  <div style={{ fontSize: '12px', color: '#aaa', marginBottom: '5px' }}>Analyzing:</div>
                  <div style={{
                    fontSize: '14px',
                    fontWeight: 'bold'
                  }}>
                    <span
                      style={{
                        background: getEntityColor(selectedEntity.type),
                        color: '#fff',
                        padding: '3px 8px',
                        borderRadius: '3px',
                        marginRight: '8px'
                      }}
                    >
                      {selectedEntity.type}
                    </span>
                    {selectedEntity.value}
                  </div>
                </div>

                {relatedEntities.length > 0 ? (
                  <div>
                    <div style={{ fontSize: '12px', color: '#aaa', marginBottom: '10px' }}>
                      Found {relatedEntities.length} related entities:
                    </div>
                    {relatedEntities.map((rel, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: '#252525',
                          padding: '12px',
                          borderRadius: '4px',
                          marginBottom: '8px',
                          fontSize: '12px',
                          borderLeft: `3px solid ${getEntityColor(rel.to_entity.split(':')[0] || 'email')}`
                        }}
                      >
                        <div style={{ marginBottom: '5px' }}>
                          <strong>Pivot:</strong> {rel.to_entity}
                        </div>
                        <div style={{ color: '#aaa', fontSize: '11px' }}>
                          💪 Strength: {rel.strength}%
                        </div>
                        <div style={{ color: '#888', fontSize: '11px', marginTop: '5px' }}>
                          {rel.justification}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{
                    textAlign: 'center',
                    padding: '30px 15px',
                    color: '#666'
                  }}>
                    <AlertCircle size={32} style={{ margin: '0 auto 10px' }} />
                    <p>No related entities found</p>
                    <p style={{ fontSize: '12px' }}>Or click "Analyze" to search</p>
                  </div>
                )}
              </>
            ) : (
              <div style={{
                textAlign: 'center',
                padding: '40px 15px',
                color: '#666'
              }}>
                <GitBranch size={48} style={{ margin: '0 auto 10px', opacity: 0.5 }} />
                <p>Select an entity to explore relationships</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EntityExplorer;
