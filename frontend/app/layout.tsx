import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "AgentOps Control Plane",
  description: "Observability, evaluation, and replay for enterprise AI agents",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-gray-100 min-h-screen font-sans antialiased">
        <nav className="border-b border-gray-800 px-6 py-3 flex items-center gap-6 sticky top-0 bg-gray-950/90 backdrop-blur z-10">
          <Link href="/runs" className="font-semibold text-white tracking-tight">
            AgentOps
          </Link>
          <div className="h-4 w-px bg-gray-800" />
          <Link
            href="/runs"
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            Runs
          </Link>
          <Link
            href="/demo"
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            Demo
          </Link>
        </nav>
        <main className="px-6 py-8 max-w-6xl mx-auto">{children}</main>
      </body>
    </html>
  );
}
