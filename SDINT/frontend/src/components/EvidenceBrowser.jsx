import React, { useState, useEffect } from 'react';
import { Search, Filter, Download, Eye, Trash2, Tag } from 'lucide-react';

const EvidenceBrowser = ({ investigationId }) => {
  const [evidence, setEvidence] = useState([]);
  const [filteredEvidence, setFilteredEvidence] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSource, setSelectedSource] = useState('all');
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [loading, setLoading] = useState(false);
  const API = 'http://localhost:5000/api';

  useEffect(() => {
    loadEvidence();
  }, []);

  useEffect(() => {
    filterEvidence();
  }, [searchTerm, selectedSource, evidence]);

  const loadEvidence = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API}/osint/evidence?limit=50`);
      if (response.ok) {
        const data = await response.json();
        setEvidence(data || []);
      }
    } catch (error) {
      console.error('Error loading evidence:', error);
      // Load mock data
      setEvidence([
        {
          evidence_id: 'evi_001',
          title: 'Phishing Email Detected',
          source_type: 'web_search',
          source_platform: 'email',
          content: { body: 'Suspicious email from fake.bank.com' },
          entities: [{ type: 'email', value: 'phisher@fake.com', confidence: 0.95 }],
          confidence: 0.85,
          created_at: new Date(Date.now() - 2*24*3600000).toISOString()
        },
        {
          evidence_id: 'evi_002',
          title: 'Leaked Credentials Found',
          source_type: 'breach_data',
          source_platform: 'hibp',
          content: { body: 'Credentials found in breach database' },
          entities: [{ type: 'email', value: 'victim@example.com', confidence: 0.99 }],
          confidence: 0.99,
          created_at: new Date(Date.now() - 1*24*3600000).toISOString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const filterEvidence = () => {
    let filtered = evidence;

    if (selectedSource !== 'all') {
      filtered = filtered.filter(e => e.source_type === selectedSource);
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(e =>
        (e.title && e.title.toLowerCase().includes(term)) ||
        (e.content?.body && e.content.body.toLowerCase().includes(term)) ||
        (e.entities && e.entities.some(ent => ent.value.toLowerCase().includes(term)))
      );
    }

    setFilteredEvidence(filtered);
  };

  const getSourceColor = (source) => {
    const colors = {
      reddit_post: '#FF4500',
      web_search: '#4285F4',
      breach_data: '#EA4335',
      username_discovery: '#FBBC04',
      domain_intel: '#34A853',
      manual: '#9C27B0'
    };
    return colors[source] || '#999';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.9) return 'Very High';
    if (confidence >= 0.7) return 'High';
    if (confidence >= 0.5) return 'Medium';
    return 'Low';
  };

  const sourceTypes = [...new Set(evidence.map(e => e.source_type))];

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <h2 style={{ marginTop: 0 }}>📋 Evidence Browser</h2>

      <div style={{
        display: 'flex',
        gap: '15px',
        marginBottom: '20px',
        flexWrap: 'wrap',
        alignItems: 'center'
      }}>
        <div style={{ flex: 1, minWidth: '250px' }}>
          <input
            type="text"
            placeholder="Search evidence..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 15px',
              background: '#2a2a2a',
              border: '1px solid #444',
              borderRadius: '4px',
              color: '#fff'
            }}
          />
        </div>

        <select
          value={selectedSource}
          onChange={(e) => setSelectedSource(e.target.value)}
          style={{
            padding: '10px 15px',
            background: '#2a2a2a',
            border: '1px solid #444',
            borderRadius: '4px',
            color: '#fff',
            cursor: 'pointer'
          }}
        >
          <option value="all">All Sources</option>
          {sourceTypes.map(type => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>

        <button
          onClick={loadEvidence}
          style={{
            padding: '10px 15px',
            background: '#667eea',
            border: 'none',
            borderRadius: '4px',
            color: '#fff',
            cursor: 'pointer'
          }}
        >
          {loading ? '⟳ Loading...' : '↻ Refresh'}
        </button>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: selectedEvidence ? '1fr 300px' : '1fr',
        gap: '15px'
      }}>
        <div style={{
          background: '#1a1a1a',
          border: '1px solid #333',
          borderRadius: '8px',
          overflow: 'hidden'
        }}>
          {filteredEvidence.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
              No evidence found
            </div>
          ) : (
            <div>
              {filteredEvidence.map(evi => (
                <div
                  key={evi.evidence_id}
                  onClick={() => setSelectedEvidence(evi)}
                  style={{
                    padding: '15px',
                    borderBottom: '1px solid #333',
                    cursor: 'pointer',
                    background: selectedEvidence?.evidence_id === evi.evidence_id ? '#2a2a3a' : 'transparent',
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = selectedEvidence?.evidence_id === evi.evidence_id ? '#2a2a3a' : '#252525'}
                  onMouseLeave={(e) => e.currentTarget.style.background = selectedEvidence?.evidence_id === evi.evidence_id ? '#2a2a3a' : 'transparent'}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '8px' }}>
                    <h4 style={{ margin: 0, fontSize: '14px' }}>{evi.title}</h4>
                    <span
                      style={{
                        background: getSourceColor(evi.source_type),
                        color: '#fff',
                        padding: '3px 8px',
                        borderRadius: '3px',
                        fontSize: '11px'
                      }}
                    >
                      {evi.source_type}
                    </span>
                  </div>

                  <p style={{ margin: '5px 0', fontSize: '12px', color: '#aaa' }}>
                    {evi.content?.body?.substring(0, 100)}...
                  </p>

                  <div style={{
                    display: 'flex',
                    gap: '10px',
                    fontSize: '11px',
                    color: '#888',
                    marginTop: '8px'
                  }}>
                    <span>🎯 {getConfidenceLabel(evi.confidence)} ({(evi.confidence * 100).toFixed(0)}%)</span>
                    <span>📊 {evi.entities?.length || 0} entities</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {selectedEvidence && (
          <div style={{
            background: '#1a1a1a',
            border: '1px solid #333',
            borderRadius: '8px',
            padding: '15px',
            maxHeight: '600px',
            overflowY: 'auto'
          }}>
            <h4 style={{ marginTop: 0 }}>Details</h4>

            <div style={{ fontSize: '12px' }}>
              <div style={{ marginBottom: '15px' }}>
                <strong>ID:</strong>
                <div style={{ color: '#aaa', marginTop: '5px' }}>{selectedEvidence.evidence_id}</div>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <strong>Source:</strong>
                <div style={{ color: '#aaa', marginTop: '5px' }}>{selectedEvidence.source_platform}</div>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <strong>Confidence:</strong>
                <div style={{
                  marginTop: '5px',
                  background: '#2a2a2a',
                  height: '6px',
                  borderRadius: '3px',
                  overflow: 'hidden'
                }}>
                  <div
                    style={{
                      height: '100%',
                      background: '#667eea',
                      width: `${selectedEvidence.confidence * 100}%`
                    }}
                  />
                </div>
              </div>

              <div>
                <strong>Entities:</strong>
                <div style={{ marginTop: '8px' }}>
                  {selectedEvidence.entities?.map((ent, idx) => (
                    <div
                      key={idx}
                      style={{
                        background: '#2a2a2a',
                        padding: '8px',
                        borderRadius: '4px',
                        marginBottom: '5px',
                        fontSize: '11px'
                      }}
                    >
                      <div style={{ color: '#aaa' }}>
                        <strong>{ent.type}:</strong> {ent.value}
                      </div>
                      <div style={{ color: '#666', fontSize: '10px', marginTop: '3px' }}>
                        Confidence: {(ent.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <button
              onClick={() => setSelectedEvidence(null)}
              style={{
                width: '100%',
                marginTop: '15px',
                padding: '8px',
                background: '#444',
                border: 'none',
                borderRadius: '4px',
                color: '#fff',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              Close
            </button>
          </div>
        )}
      </div>

      <div style={{
        marginTop: '20px',
        padding: '15px',
        background: '#2a2a2a',
        borderRadius: '4px',
        fontSize: '12px',
        color: '#aaa'
      }}>
        📊 Showing {filteredEvidence.length} of {evidence.length} evidence items
      </div>
    </div>
  );
};

export default EvidenceBrowser;
