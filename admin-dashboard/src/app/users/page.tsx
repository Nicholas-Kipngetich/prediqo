'use client';

import { useEffect, useState } from 'react';
import { AdminUser, api } from '../../lib/api';

export default function UsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get<AdminUser[]>('/api/v1/admin/users').then(setUsers).catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <div className="error">Failed to load: {error}</div>;

  return (
    <div>
      <h1>Users</h1>
      <table>
        <thead>
          <tr>
            <th>User</th>
            <th>Status</th>
            <th>Roles</th>
            <th>VIP</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.display_name ?? user.email ?? user.id}</td>
              <td>{user.status}</td>
              <td>{user.roles.join(', ')}</td>
              <td>{user.is_vip ? 'Yes' : 'No'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {users.length === 0 && !error && <p className="muted">No users found.</p>}
    </div>
  );
}
