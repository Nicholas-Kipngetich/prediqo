'use client';

import { useEffect, useState } from 'react';
import { api, AuditRow, Health } from '../../lib/api';

export default function SystemPage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [audit, setAudit] = useState<AuditRow[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get<Health>('/api/v1/admin/system/health').then(setHealth).catch((e: Error) => setError(e.message));
    api.get<AuditRow[]>('/api/v1/admin/audit-logs').then(setAudit).catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <div className="error">Failed to load: {error}</div>;
  if (!health) return <div className="muted">Loading…</div>;

  return (
    <div>
      <h1>System</h1>
      <div className="grid">
        <div className="card">
          <div className="muted">API</div>
          <div className="metric">{health.api}</div>
        </div>
        <div className="card">
          <div className="muted">Database</div>
          <div className="metric">{health.db}</div>
        </div>
        <div className="card">
          <div className="muted">Redis</div>
          <div className="metric">{health.redis}</div>
        </div>
      </div>
      <h2>Audit log</h2>
      <table>
        <thead>
          <tr>
            <th>Action</th>
            <th>Target</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {audit.map((row) => (
            <tr key={row.id}>
              <td>{row.action}</td>
              <td>{row.target_type ?? '—'}</td>
              <td>{row.created_at}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
