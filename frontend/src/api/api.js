const API_BASE = 'http://localhost:5000/api';

export const fetchLinks = async () => {
  const res = await fetch(`${API_BASE}/links`);
  return res.json();
};

export const fetchStats = async () => {
  const res = await fetch(`${API_BASE}/stats`);
  return res.json();
};

export const startDownload = async () => {
  const res = await fetch(`${API_BASE}/download`, { method: 'POST' });
  return res.json();
};

export const startGrabber = async () => {
  const res = await fetch(`${API_BASE}/grab`, { method: 'POST' });
  return res.json();
};

export const addLink = async (link) => {
  const res = await fetch(`${API_BASE}/add-link`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ link })
  });
  return res.json();
};

export const downloadSingle = async (link) => {
  const res = await fetch(`${API_BASE}/download-single`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ link })
  });
  return res.json();
};
