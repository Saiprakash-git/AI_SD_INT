import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { Activity, MessageSquare, AlertTriangle, TrendingUp, BarChart3, Clock, ThumbsUp, ArrowLeft, LayoutDashboard, HeartPulse, Search, Bell, Camera, Link as LinkIcon, AlertOctagon, Zap } from 'lucide-react';

import Feed from './pages/Feed';
import Incidents from './pages/Incidents';
import NarrativeSearch from './pages/NarrativeSearch';
import LinkAnalyzer from './pages/LinkAnalyzer';
import Trends from './pages/Trends';
import CrawlMode from './pages/CrawlMode';
import { DataCacheProvider } from './DataCacheContext';

const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:5000/api' : 'https://sd-int.onrender.com/api');

function App() {
  const [rssStatus, setRssStatus] = useState(null);

  async function fetchRssStatus() {
    try {
      const res = await axios.get(`${API_BASE}/status`);
      if (res.data && res.data.length > 0) {
        const sorted = res.data.sort((a,b) => new Date(b.last_poll_time) - new Date(a.last_poll_time));
        setRssStatus(sorted[0]);
      }
    } catch {
      setRssStatus(null);
    }
  }

  useEffect(() => {
    fetchRssStatus();
    const interval = setInterval(fetchRssStatus, 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = () => {
    if (!rssStatus) return 'var(--negative)';
    const minDiff = (new Date() - new Date(rssStatus.last_poll_time)) / 60000;
    if (minDiff < 5) return 'var(--positive)';
    if (minDiff < 15) return 'var(--neutral)';
    return 'var(--negative)';
  };

  return (
    <DataCacheProvider>
    <Router>
      <div className="app-shell">
        
        {/* Persistent Left Sidebar */}
        <aside className="sidebar-nav">
          <div className="brand-section">
            <h1><Activity size={24} color="var(--accent-primary)" /> SocialPulse<span>.ai</span></h1>
            <p className="mono" style={{ color: "var(--text-muted)", fontSize: "0.75rem", marginTop: "4px" }}>INTELLIGENCE PLATFORM</p>
          </div>
          
          <div className="nav-links">
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', padding: '12px 0', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 'bold' }}>📊 Social Analysis</div>
            <NavLink to="/" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
              <LayoutDashboard size={18} /> Live Feed
            </NavLink>
            <NavLink to="/incidents" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
              <AlertOctagon size={18} /> Incidents
            </NavLink>
            <NavLink to="/search" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
              <Search size={18} /> Narrative Search
            </NavLink>
            <NavLink to="/analyzer" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
              <LinkIcon size={18} /> Link Analyzer
            </NavLink>
            <NavLink to="/trends" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
              <TrendingUp size={18} /> Trends & Health
            </NavLink>

            <div style={{ height: '1px', background: 'var(--border-color)', margin: '15px 0' }} />

            <div style={{ fontSize: '11px', color: 'var(--accent-primary)', padding: '12px 0', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 'bold' }}>🕵️ OSINT Crawl</div>
            <NavLink to="/crawl" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
              <Zap size={18} /> Crawl Mode
            </NavLink>
          </div>
        </aside>

        {/* Dynamic Workspace */}
        <main className="main-workspace">
          
          <header className="topbar">
             <div className="live-indicator">
               <div className="status-dot" style={{ background: getStatusColor(), boxShadow: `0 0 8px ${getStatusColor()}` }} />
               <span>SYSTEM.LIVE [ {rssStatus ? `Sync'd ${Math.floor((new Date() - new Date(rssStatus.last_poll_time))/60000)}m ago` : 'Waiting'} ]</span>
             </div>
          </header>

          <div className="route-content fade-in">
             <Routes>
                <Route path="/" element={<Feed />} />
                <Route path="/incidents" element={<Incidents />} />
                <Route path="/search" element={<NarrativeSearch />} />
                <Route path="/analyzer" element={<LinkAnalyzer />} />
                <Route path="/trends" element={<Trends />} />
                <Route path="/crawl" element={<CrawlMode />} />
             </Routes>
          </div>
          
        </main>
      </div>
    </Router>
    </DataCacheProvider>
  );
}

export default App;
