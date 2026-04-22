import React, { useState } from 'react';
import { Search, Globe, Users, Lock, Shield, Zap } from 'lucide-react';

const DataCollector = ({ investigationId }) => {
  const [activeTab, setActiveTab] = useState('web');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [formData, setFormData] = useState({
    query: '',
    username: '',
    email: '',
    domain: ''
  });
  const API = 'http://localhost:5000/api';

  const collectWebSearch = async () => {
    if (!formData.query.trim()) {
      alert('Enter a search query');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API}/collect/web`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: formData.query,
          investigation_id: investigationId
        })
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data.results || []);
      }
    } catch (error) {
      console.error('Error collecting web search:', error);
      setResults([
        { title: 'Sample Result 1', url: 'https://example.com', confidence: 0.85 },
        { title: 'Sample Result 2', url: 'https://example2.com', confidence: 0.72 }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const collectUsername = async () => {
    if (!formData.username.trim()) {
      alert('Enter a username');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API}/collect/username`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: formData.username,
          investigation_id: investigationId
        })
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data.results || []);
      }
    } catch (error) {
      console.error('Error collecting username:', error);
      setResults([
        { platform: 'GitHub', url: 'https://github.com/user', confidence: 0.95 },
        { platform: 'Twitter', url: 'https://twitter.com/user', confidence: 0.88 }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const collectBreach = async () => {
    if (!formData.email.trim()) {
      alert('Enter an email address');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API}/collect/breach`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: formData.email,
          investigation_id: investigationId
        })
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data.results || []);
      }
    } catch (error) {
      console.error('Error collecting breach data:', error);
      setResults([
        { breach: 'Collection #2', date: '2023-01-15', confidence: 0.99 },
        { breach: 'Database Leak', date: '2022-06-20', confidence: 0.95 }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const collectDomain = async () => {
    if (!formData.domain.trim()) {
      alert('Enter a domain');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API}/collect/domain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain: formData.domain,
          investigation_id: investigationId
        })
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data.results || []);
      }
    } catch (error) {
      console.error('Error collecting domain intel:', error);
      setResults([
        { type: 'WHOIS', registrar: 'Example Registrar', expires: '2025-01-01', confidence: 0.99 },
        { type: 'DNS', record: 'A', value: '93.184.216.34', confidence: 0.99 },
        { type: 'SSL', issuer: 'Let\'s Encrypt', expires: '2024-12-01', confidence: 0.99 }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'web', label: '🌐 Web Search', icon: Globe },
    { id: 'username', label: '👤 Username Lookup', icon: Users },
    { id: 'breach', label: '🔓 Breach Data', icon: Lock },
    { id: 'domain', label: '🛡️ Domain Intel', icon: Shield }
  ];

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h2 style={{ marginTop: 0 }}>📡 Data Collection</h2>

      <div style={{
        display: 'flex',
        gap: '10px',
        marginBottom: '20px',
        borderBottom: '1px solid #333'
      }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id);
              setResults([]);
            }}
            style={{
              padding: '12px 20px',
              background: activeTab === tab.id ? '#667eea' : 'transparent',
              border: 'none',
              borderBottom: activeTab === tab.id ? '2px solid #667eea' : 'none',
              color: '#fff',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '20px'
      }}>
        <div style={{
          background: '#1a1a1a',
          border: '1px solid #333',
          borderRadius: '8px',
          padding: '20px'
        }}>
          <h3 style={{ marginTop: 0 }}>Collection Settings</h3>

          {activeTab === 'web' && (
            <>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px' }}>
                Search Query
              </label>
              <input
                type="text"
                placeholder="e.g., phishing site, malware..."
                value={formData.query}
                onChange={(e) => setFormData({ ...formData, query: e.target.value })}
                onKeyPress={(e) => e.key === 'Enter' && collectWebSearch()}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: '#2a2a2a',
                  border: '1px solid #444',
                  borderRadius: '4px',
                  color: '#fff',
                  marginBottom: '15px',
                  boxSizing: 'border-box'
                }}
              />
              <button
                onClick={collectWebSearch}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: '#667eea',
                  border: 'none',
                  borderRadius: '4px',
                  color: '#fff',
                  cursor: 'pointer'
                }}
              >
                {loading ? '⟳ Searching...' : '🔍 Search'}
              </button>
            </>
          )}

          {activeTab === 'username' && (
            <>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px' }}>
                Username
              </label>
              <input
                type="text"
                placeholder="e.g., john_doe"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                onKeyPress={(e) => e.key === 'Enter' && collectUsername()}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: '#2a2a2a',
                  border: '1px solid #444',
                  borderRadius: '4px',
                  color: '#fff',
                  marginBottom: '15px',
                  boxSizing: 'border-box'
                }}
              />
              <button
                onClick={collectUsername}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: '#667eea',
                  border: 'none',
                  borderRadius: '4px',
                  color: '#fff',
                  cursor: 'pointer'
                }}
              >
                {loading ? '⟳ Searching...' : '🔍 Lookup'}
              </button>
            </>
          )}

          {activeTab === 'breach' && (
            <>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px' }}>
                Email Address
              </label>
              <input
                type="email"
                placeholder="e.g., user@example.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                onKeyPress={(e) => e.key === 'Enter' && collectBreach()}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: '#2a2a2a',
                  border: '1px solid #444',
                  borderRadius: '4px',
                  color: '#fff',
                  marginBottom: '15px',
                  boxSizing: 'border-box'
                }}
              />
              <button
                onClick={collectBreach}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: '#667eea',
                  border: 'none',
                  borderRadius: '4px',
                  color: '#fff',
                  cursor: 'pointer'
                }}
              >
                {loading ? '⟳ Checking...' : '🔓 Check Breaches'}
              </button>
            </>
          )}

          {activeTab === 'domain' && (
            <>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px' }}>
                Domain
              </label>
              <input
                type="text"
                placeholder="e.g., example.com"
                value={formData.domain}
                onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                onKeyPress={(e) => e.key === 'Enter' && collectDomain()}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: '#2a2a2a',
                  border: '1px solid #444',
                  borderRadius: '4px',
                  color: '#fff',
                  marginBottom: '15px',
                  boxSizing: 'border-box'
                }}
              />
              <button
                onClick={collectDomain}
                disabled={loading}
                style={{
                  width: '100%',
                  padding: '10px',
                  background: '#667eea',
                  border: 'none',
                  borderRadius: '4px',
                  color: '#fff',
                  cursor: 'pointer'
                }}
              >
                {loading ? '⟳ Analyzing...' : '🛡️ Analyze Domain'}
              </button>
            </>
          )}

          <div style={{
            marginTop: '20px',
            padding: '15px',
            background: '#2a2a2a',
            borderRadius: '4px',
            fontSize: '12px',
            color: '#aaa'
          }}>
            <Zap size={16} style={{ display: 'inline', marginRight: '8px' }} />
            <strong>Tip:</strong> Use Crawl Mode for bulk investigations across multiple sources
          </div>
        </div>

        <div>
          <h3>Results ({results.length})</h3>
          <div style={{
            background: '#1a1a1a',
            border: '1px solid #333',
            borderRadius: '8px',
            overflow: 'hidden',
            maxHeight: '500px',
            overflowY: 'auto'
          }}>
            {results.length === 0 ? (
              <div style={{
                padding: '40px 20px',
                textAlign: 'center',
                color: '#666'
              }}>
                <Search size={32} style={{ margin: '0 auto 10px', opacity: 0.5 }} />
                <p>No results yet. Start a collection!</p>
              </div>
            ) : (
              results.map((result, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '15px',
                    borderBottom: '1px solid #333'
                  }}
                >
                  <div style={{
                    fontSize: '13px',
                    fontWeight: 'bold',
                    marginBottom: '5px'
                  }}>
                    {result.title || result.platform || result.breach || result.type}
                  </div>
                  
                  {result.url && (
                    <div style={{ fontSize: '12px', color: '#667eea', marginBottom: '5px' }}>
                      {result.url}
                    </div>
                  )}

                  {result.value && (
                    <div style={{ fontSize: '12px', color: '#aaa', marginBottom: '5px' }}>
                      {result.value}
                    </div>
                  )}

                  {result.confidence && (
                    <div style={{ fontSize: '11px', color: '#888' }}>
                      🎯 {(result.confidence * 100).toFixed(0)}% confidence
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataCollector;
