import React, { useState, useEffect } from 'react';
import { AlertCircle, Search, Plus, Trash2, Clock, Shield, Target, GitBranch } from 'lucide-react';

const InvestigationDashboard = ({ onSelectInvestigation }) => {
  const [investigations, setInvestigations] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    investigator: '',
    priority: 'medium',
    tags: []
  });
  const [tagInput, setTagInput] = useState('');
  const [loading, setLoading] = useState(false);
  const API = 'http://localhost:5000/api';

  useEffect(() => {
    // Load mock investigations
    setInvestigations([
      {
        investigation_id: 'inv_001',
        title: 'Phishing Campaign Q1 2024',
        description: 'Large scale phishing targeting financial sector',
        status: 'active',
        priority: 'high',
        investigator: 'analyst_01',
        evidence_count: 45,
        created_at: '2024-01-15'
      },
      {
        investigation_id: 'inv_002',
        title: 'Credential Compromise Incident',
        description: 'Investigation into exposed credentials',
        status: 'active',
        priority: 'critical',
        investigator: 'analyst_02',
        evidence_count: 28,
        created_at: '2024-02-01'
      }
    ]);
  }, []);

  const handleCreateInvestigation = async () => {
    if (!formData.title.trim()) {
      alert('Title is required');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API}/investigations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const data = await response.json();
        const newInv = data.investigation || {
          investigation_id: `inv_${Date.now()}`,
          ...formData,
          status: 'active',
          evidence_count: 0,
          created_at: new Date().toISOString().split('T')[0]
        };
        
        setInvestigations([...investigations, newInv]);
        setShowCreateModal(false);
        setFormData({ title: '', description: '', investigator: '', priority: 'medium', tags: [] });
      }
    } catch (error) {
      console.error('Error creating investigation:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority) => {
    const colors = {
      low: '#4CAF50',
      medium: '#FF9800',
      high: '#FF5722',
      critical: '#9C27B0'
    };
    return colors[priority] || '#666';
  };

  const getStatusColor = (status) => {
    const colors = {
      active: '#4CAF50',
      paused: '#FF9800',
      closed: '#999',
      archived: '#666'
    };
    return colors[status] || '#666';
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ margin: 0, fontSize: '24px', fontWeight: 'bold' }}>🕵️ Investigations</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: '#fff',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '14px'
          }}
        >
          <Plus size={18} /> New Investigation
        </button>
      </div>

      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: '#1a1a1a',
            border: '1px solid #333',
            borderRadius: '8px',
            padding: '20px',
            maxWidth: '500px',
            width: '90%'
          }}>
            <h3 style={{ marginTop: 0 }}>Create New Investigation</h3>
            
            <input
              type="text"
              placeholder="Investigation Title"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              style={{
                width: '100%',
                padding: '10px',
                marginBottom: '10px',
                background: '#2a2a2a',
                border: '1px solid #444',
                borderRadius: '4px',
                color: '#fff',
                boxSizing: 'border-box'
              }}
            />

            <textarea
              placeholder="Description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              style={{
                width: '100%',
                padding: '10px',
                marginBottom: '10px',
                background: '#2a2a2a',
                border: '1px solid #444',
                borderRadius: '4px',
                color: '#fff',
                boxSizing: 'border-box',
                minHeight: '80px'
              }}
            />

            <input
              type="text"
              placeholder="Investigator Name"
              value={formData.investigator}
              onChange={(e) => setFormData({ ...formData, investigator: e.target.value })}
              style={{
                width: '100%',
                padding: '10px',
                marginBottom: '10px',
                background: '#2a2a2a',
                border: '1px solid #444',
                borderRadius: '4px',
                color: '#fff',
                boxSizing: 'border-box'
              }}
            />

            <select
              value={formData.priority}
              onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
              style={{
                width: '100%',
                padding: '10px',
                marginBottom: '20px',
                background: '#2a2a2a',
                border: '1px solid #444',
                borderRadius: '4px',
                color: '#fff',
                boxSizing: 'border-box'
              }}
            >
              <option value="low">Low Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="high">High Priority</option>
              <option value="critical">Critical Priority</option>
            </select>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowCreateModal(false)}
                style={{
                  background: '#444',
                  color: '#fff',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateInvestigation}
                disabled={loading}
                style={{
                  background: '#667eea',
                  color: '#fff',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                {loading ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
        gap: '15px'
      }}>
        {investigations.map(inv => (
          <div
            key={inv.investigation_id}
            onClick={() => onSelectInvestigation(inv)}
            style={{
              background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
              border: '1px solid #333',
              borderRadius: '8px',
              padding: '15px',
              cursor: 'pointer',
              transition: 'all 0.3s',
              ':hover': { borderColor: '#667eea' }
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#667eea';
              e.currentTarget.style.boxShadow = '0 0 15px rgba(102, 126, 234, 0.3)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = '#333';
              e.currentTarget.style.boxShadow = 'none';
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '10px' }}>
              <h4 style={{ margin: 0, fontSize: '16px' }}>{inv.title}</h4>
              <div style={{ display: 'flex', gap: '5px' }}>
                <span style={{
                  background: getPriorityColor(inv.priority),
                  color: '#fff',
                  padding: '3px 8px',
                  borderRadius: '3px',
                  fontSize: '11px',
                  textTransform: 'capitalize'
                }}>
                  {inv.priority}
                </span>
              </div>
            </div>

            <p style={{ margin: '0 0 10px 0', fontSize: '13px', color: '#aaa' }}>
              {inv.description}
            </p>

            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '12px',
              color: '#888',
              paddingTop: '10px',
              borderTop: '1px solid #333'
            }}>
              <span>👤 {inv.investigator}</span>
              <span>📊 {inv.evidence_count} evidence</span>
              <span style={{ color: getStatusColor(inv.status) }}>● {inv.status}</span>
            </div>
          </div>
        ))}
      </div>

      {investigations.length === 0 && (
        <div style={{
          textAlign: 'center',
          padding: '40px 20px',
          color: '#666'
        }}>
          <AlertCircle size={48} style={{ margin: '0 auto 10px', opacity: 0.5 }} />
          <p>No investigations yet. Create one to get started.</p>
        </div>
      )}
    </div>
  );
};

export default InvestigationDashboard;
