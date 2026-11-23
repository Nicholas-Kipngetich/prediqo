'use client';

import { useEffect, useState } from 'react';
import { api, Dashboard, Health } from '../lib/api';

export default function HomePage() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .get<Dashboard>('/api/v1/admin/dashboard')
      .then(setDashboard)
      .catch((e: Error) => setError(e.message));
    api
      .get<Health>('/api/v1/admin/system/health')
      .then(setHealth)
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <div className="error">Failed to load: {error}</div>;
  if (!dashboard || !health) return <div className="muted">Loading…</div>;

  const cards = [
    { label: 'Registered users', value: dashboard.total_users },
    { label: 'Active users', value: dashboard.active_users },
    { label: 'Administrators', value: dashboard.admin_users },
    { label: 'Predictions', value: health.predictions },
    { label: 'Sync jobs', value: health.sync_jobs },
  ];

  return (
    <div>
      <h1>Overview</h1>
      <div className="grid">
        {cards.map((card) => (
          <div className="card" key={card.label}>
            <div className="muted">{card.label}</div>
            <div className="metric">{card.value}</div>
          </div>
        ))}
      </div>
      <div className="card">
        <h2>Services</h2>
        <p>API: {health.api}</p>
        <p>Database: {health.db}</p>
        <p>Redis: {health.redis}</p>
      </div>
    </div>
  );
}
