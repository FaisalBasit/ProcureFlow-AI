import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProcureFlow AI — Intelligent Procurement Orchestrator",
  description:
    "Multi-agent procurement approval system powered by Band. Submit purchase requests and track agent-driven risk analysis, policy compliance, and approvals.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <nav className="navbar">
          <div className="container navbar-inner">
            <a href="/" className="navbar-brand">
              <span className="logo">🔷</span> ProcureFlow AI
            </a>
            <div className="navbar-links">
              <a href="/" className="nav-link">Submit</a>
              <a href="/dashboard" className="nav-link">Dashboard</a>
              <a href="/approve" className="nav-link">Approvals</a>
            </div>
          </div>
        </nav>
        <main className="container main-content">{children}</main>
      </body>
    </html>
  );
}