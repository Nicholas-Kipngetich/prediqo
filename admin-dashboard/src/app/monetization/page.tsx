'use client';

import { useEffect, useState } from 'react';
import { api, PackageRow, PlanRow } from '../../lib/api';

export default function MonetizationPage() {
  const [packages, setPackages] = useState<PackageRow[]>([]);
  const [plans, setPlans] = useState<PlanRow[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get<PackageRow[]>('/api/v1/admin/token-packages').then(setPackages).catch((e: Error) => setError(e.message));
    api.get<PlanRow[]>('/api/v1/admin/subscription-plans').then(setPlans).catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <div className="error">Failed to load: {error}</div>;

  return (
    <div>
      <h1>Monetization</h1>
      <h2>Token packages</h2>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Tokens</th>
            <th>Price</th>
            <th>Active</th>
          </tr>
        </thead>
        <tbody>
          {packages.map((row) => (
            <tr key={row.id}>
              <td>{row.name}</td>
              <td>{row.tokens}</td>
              <td>{row.currency} {(row.price_minor / 100).toFixed(0)}</td>
              <td>{row.active ? 'Yes' : 'No'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h2>VIP plans</h2>
      <table>
        <thead>
          <tr>
            <th>Code</th>
            <th>Interval</th>
            <th>Price</th>
            <th>Active</th>
          </tr>
        </thead>
        <tbody>
          {plans.map((row) => (
            <tr key={row.id}>
              <td>{row.code}</td>
              <td>{row.interval}</td>
              <td>{row.currency} {(row.price_minor / 100).toFixed(0)}</td>
              <td>{row.active ? 'Yes' : 'No'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
