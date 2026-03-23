import { useState, useEffect } from 'react';
import { fetchLinks, fetchStats, startDownload, startGrabber } from './api/api';
import './App.css';

const statusColors = {
  pending: '#f59e0b',
  downloading: '#3b82f6',
  done: '#22c55e',
  failed: '#ef4444'
};

const statusLabels = {
  pending: 'Pending',
  downloading: 'Downloading',
  done: 'Done',
  failed: 'Failed'
};

function App() {
  const [links, setLinks] = useState([]);
  const [stats, setStats] = useState({ pending: 0, downloading: 0, done: 0, failed: 0 });
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [message, setMessage] = useState('');
  const [activeTab, setActiveTab] = useState('links');

  const loadData = async () => {
    try {
      const [linksData, statsData] = await Promise.all([fetchLinks(), fetchStats()]);
      setLinks(linksData);
      setStats(statsData);
    } catch (err) {
      setMessage('Error: API server not running. Start with: python api_server.py');
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleDownload = async () => {
    setDownloading(true);
    setMessage('Downloading...');
    try {
      const result = await startDownload();
      if (result.success) {
        setMessage('Download complete!');
        await loadData();
      } else {
        setMessage(`Error: ${result.error}`);
      }
    } catch (err) {
      setMessage('Error: Could not start download');
    }
    setDownloading(false);
  };

  const handleGrabber = async () => {
    setLoading(true);
    try {
      const result = await startGrabber();
      setMessage(result.success ? 'Grabber active! Copy Instagram links to clipboard.' : `Error: ${result.error}`);
    } catch (err) {
      setMessage('Error: Could not start grabber');
    }
    setLoading(false);
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Elevate Agency Tools</h1>
        <p>Instagram Download Manager</p>
      </header>

      <nav className="nav">
        <button 
          className={activeTab === 'links' ? 'active' : ''} 
          onClick={() => setActiveTab('links')}
        >
          Links ({links.length})
        </button>
        <button 
          className={activeTab === 'dashboard' ? 'active' : ''} 
          onClick={() => setActiveTab('dashboard')}
        >
          Dashboard
        </button>
      </nav>

      {message && <div className="message">{message}</div>}

      <div className="stats-bar">
        <div className="stat" style={{ borderColor: statusColors.pending }}>
          <span className="stat-value">{stats.pending}</span>
          <span className="stat-label">Pending</span>
        </div>
        <div className="stat" style={{ borderColor: statusColors.downloading }}>
          <span className="stat-value">{stats.downloading}</span>
          <span className="stat-label">Downloading</span>
        </div>
        <div className="stat" style={{ borderColor: statusColors.done }}>
          <span className="stat-value">{stats.done}</span>
          <span className="stat-label">Done</span>
        </div>
        <div className="stat" style={{ borderColor: statusColors.failed }}>
          <span className="stat-value">{stats.failed}</span>
          <span className="stat-label">Failed</span>
        </div>
      </div>

      <div className="actions">
        <button onClick={handleGrabber} disabled={loading} className="btn btn-primary">
          {loading ? 'Starting...' : 'Start Clipboard Grabber'}
        </button>
        <button onClick={handleDownload} disabled={downloading || stats.pending === 0} className="btn btn-success">
          {downloading ? 'Downloading...' : `Download (${stats.pending + stats.failed})`}
        </button>
        <button onClick={loadData} className="btn btn-outline">
          Refresh
        </button>
      </div>

      {activeTab === 'links' && (
        <div className="links-list">
          <h2>All Links ({links.length})</h2>
          {links.length === 0 ? (
            <p className="empty">No links found. Start grabber and copy some Instagram URLs!</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Link</th>
                  <th>Timestamp</th>
                  <th>File</th>
                </tr>
              </thead>
              <tbody>
                {links.map((link, i) => (
                  <tr key={i}>
                    <td>
                      <span 
                        className="badge" 
                        style={{ backgroundColor: statusColors[link.status] || '#666' }}
                      >
                        {statusLabels[link.status] || link.status}
                      </span>
                    </td>
                    <td>
                      <a href={link.link} target="_blank" rel="noopener noreferrer">
                        {link.link}
                      </a>
                    </td>
                    <td>{link.timestamp}</td>
                    <td>{link.filepath || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'dashboard' && (
        <div className="dashboard">
          <h2>Quick Stats</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon" style={{ color: statusColors.pending }}>⏳</div>
              <div className="stat-info">
                <span className="stat-number">{stats.pending}</span>
                <span className="stat-text">Waiting to download</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon" style={{ color: statusColors.done }}>✅</div>
              <div className="stat-info">
                <span className="stat-number">{stats.done}</span>
                <span className="stat-text">Successfully downloaded</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon" style={{ color: statusColors.failed }}>❌</div>
              <div className="stat-info">
                <span className="stat-number">{stats.failed}</span>
                <span className="stat-text">Failed downloads</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon" style={{ color: '#8b5cf6' }}>📊</div>
              <div className="stat-info">
                <span className="stat-number">{links.length}</span>
                <span className="stat-text">Total links tracked</span>
              </div>
            </div>
          </div>

          <h2>Quick Actions</h2>
          <div className="quick-actions">
            <div className="action-card">
              <h3>Clipboard Grabber</h3>
              <p>Monitors your clipboard for Instagram links and automatically saves them.</p>
              <button onClick={handleGrabber} disabled={loading} className="btn btn-primary">
                {loading ? 'Running...' : 'Launch Grabber'}
              </button>
            </div>
            <div className="action-card">
              <h3>Download Videos</h3>
              <p>Download all pending and failed videos from the queue.</p>
              <button 
                onClick={handleDownload} 
                disabled={downloading || stats.pending + stats.failed === 0} 
                className="btn btn-success"
              >
                {downloading ? 'Downloading...' : `Download ${stats.pending + stats.failed} Videos`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
