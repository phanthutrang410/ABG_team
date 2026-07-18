/** @type {import('next').NextConfig} */

// H27: on Vercel (HTTPS) the browser must not call the EC2 HTTP API directly
// (mixed content). Empty NEXT_PUBLIC_API_BASE → same-origin fetch; rewrites
// proxy to BACKEND_URL (or the known Live API host when unset on Vercel).
const isVercel = Boolean(process.env.VERCEL);
const liveApiDefault = "http://52.74.255.88:8000";
const backendUrl = (
  process.env.BACKEND_URL || (isVercel ? liveApiDefault : "")
).replace(/\/+$/, "");

const publicApiBase = (
  process.env.NEXT_PUBLIC_API_BASE !== undefined
    ? process.env.NEXT_PUBLIC_API_BASE
    : isVercel
      ? ""
      : "http://localhost:8000"
).replace(/\/+$/, "");

const nextConfig = {
  reactStrictMode: true,
  // Bake public API base at build time (client bundle).
  env: {
    NEXT_PUBLIC_API_BASE: publicApiBase,
  },
  async redirects() {
    const analysisTabs = ["signals", "students", "fairness", "threshold"];
    return [
      {
        source: "/dashboard",
        has: [{ type: "query", key: "tab", value: "analytics" }],
        destination: "/analysis?tab=dashboard",
        permanent: false,
      },
      ...analysisTabs.map((tab) => ({
        source: "/dashboard",
        has: [{ type: "query", key: "tab", value: tab }],
        destination: `/analysis?tab=${tab}`,
        permanent: false,
      })),
      { source: "/dashboard", destination: "/overview", permanent: false },
      { source: "/select-role", destination: "/login", permanent: false },
      { source: "/my-class", destination: "/analysis", permanent: false },
      { source: "/cases/:caseId", destination: "/analysis/:caseId", permanent: false },
    ];
  },
  async rewrites() {
    if (!backendUrl) return [];
    return [
      {
        source: "/review-cases",
        destination: `${backendUrl}/review-cases`,
      },
      {
        source: "/review-cases/:path*",
        destination: `${backendUrl}/review-cases/:path*`,
      },
      {
        source: "/cases/:path*",
        destination: `${backendUrl}/cases/:path*`,
      },
      {
        source: "/config/:path*",
        destination: `${backendUrl}/config/:path*`,
      },
      {
        source: "/fairness/:path*",
        destination: `${backendUrl}/fairness/:path*`,
      },
      {
        source: "/health",
        destination: `${backendUrl}/health`,
      },
      {
        source: "/advisor-handoff-drafts",
        destination: `${backendUrl}/advisor-handoff-drafts`,
      },
      {
        source: "/advisor-handoff-drafts/:path*",
        destination: `${backendUrl}/advisor-handoff-drafts/:path*`,
      },
    ];
  },
};

export default nextConfig;
