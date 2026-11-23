const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const TOKEN = process.env.NEXT_PUBLIC_DEV_TOKEN || 'prediqo-dev-token';

async function request<T>(path: string, method: 'GET' | 'POST' = 'GET'): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    method,
    headers: { Authorization: `Bearer ${TOKEN}` },
    cache: 'no-store',
  });
  if (!response.ok) {
    throw new Error(`${method} ${path} failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string) => request<T>(path, 'POST'),
};

export type Dashboard = {
  total_users: number;
  active_users: number;
  admin_users: number;
};

export type Health = {
  api: string;
  db: string;
  redis: string;
  users: number;
  predictions: number;
  sync_jobs: number;
};

export type AdminUser = {
  id: string;
  email: string | null;
  display_name: string | null;
  status: string;
  roles: string[];
  is_vip: boolean;
};

export type PredictionRow = {
  id: string;
  fixture_id: string;
  market: string;
  model_version: string;
  status: string;
  selected_outcome: string;
  is_sample_data: boolean;
};

export type PackageRow = {
  id: string;
  name: string;
  tokens: number;
  price_minor: number;
  currency: string;
  active: boolean;
};

export type PlanRow = {
  id: string;
  code: string;
  interval: string;
  price_minor: number;
  currency: string;
  active: boolean;
};

export type AuditRow = {
  id: string;
  action: string;
  target_type: string | null;
  created_at: string;
};
