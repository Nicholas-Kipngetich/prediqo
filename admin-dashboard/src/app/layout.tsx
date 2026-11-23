import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Prediqo Admin",
  description: "Prediqo administration dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
