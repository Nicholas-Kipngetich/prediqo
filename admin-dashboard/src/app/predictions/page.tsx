'use client';

import { useEffect, useState } from 'react';
import { api, PredictionRow } from '../../lib/api';

export default function PredictionsPage() {
  const [rows, setRows] = useState<PredictionRow[]>([]);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const load = () => {
    api.get<PredictionRow[]>('/api/v1/admin/predictions').then(setRows).catch((e: Error) => setError(e.message));
  };

  useEffect(load, []);

  const run = async (path: string) => {
    setMessage('Working…');
    try {
      const result = await api.post<Record<string, number>>(path);
      setMessage(JSON.stringify(result));
      load();
    } catch (e) {
      setMessage((e as Error).message);
    }
  };

  if (error) return <div className="error">Failed to load: {error}</div>;

  return (
    <div>
      <h1>Predictions</h1>
      <div className="actions">
        <button onClick={() => run('/api/v1/admin/sync/trigger')}>Run data sync</button>
        <button onClick={() => run('/api/v1/predictions/generate')}>Generate predictions</button>
        <button onClick={() => run('/api/v1/predictions/settle')}>Settle predictions</button>
      </div>
      {message && <p className="muted">{message}</p>}
      <table>
        <thead>
          <tr>
            <th>Market</th>
            <th>Model</th>
            <th>Outcome</th>
            <th>Status</th>
            <th>Data</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>{row.market}</td>
              <td>{row.model_version}</td>
              <td>{row.selected_outcome}</td>
              <td>{row.status}</td>
              <td>{row.is_sample_data ? 'DEMO' : 'LIVE'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
