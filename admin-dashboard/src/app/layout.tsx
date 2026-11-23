import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: 'Prediqo Admin',
  description: 'Prediqo administration dashboard',
};

const nav = [
  { href: '/', label: 'Overview' },
  { href: '/users', label: 'Users' },
  { href: '/predictions', label: 'Predictions' },
  { href: '/monetization', label: 'Monetization' },
  { href: '/system', label: 'System' },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <aside className="sidebar">
            <div className="brand">Prediqo</div>
            <div className="brand-sub">Admin Console</div>
            <nav>
              {nav.map((item) => (
                <Link key={item.href} href={item.href} className="nav-link">
                  {item.label}
                </Link>
              ))}
            </nav>
          </aside>
          <main className="content">{children}</main>
        </div>
      </body>
    </html>
  );
}
