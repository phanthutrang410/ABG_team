/** @type {import('next').NextConfig} */

// H27: browser calls stay same-origin locally and on Vercel. Rewrites proxy
// to BACKEND_URL, avoiding mixed content and localhost/127.0.0.1 cookie drift.
const isVercel = Boolean(process.env.VERCEL);
const liveApiDefault = "http://52.74.255.88:8000";
const localApiDefault = "http://localhost:8000";
const backendUrl = (
  process.env.BACKEND_URL || (isVercel ? liveApiDefault : localApiDefault)
).replace(/\/+$/, "");

const publicApiBase = (
  process.env.NEXT_PUBLIC_API_BASE !== undefined
    ? process.env.NEXT_PUBLIC_API_BASE
    : ""
).replace(/\/+$/, "");

const distDir =
  process.env.NEXT_DIST_DIR ||
  (process.env.NODE_ENV === "development" ? ".next-dev" : ".next");

const nextConfig = {
  reactStrictMode: true,
  distDir,
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
      // Do NOT redirect /cases/:caseId here — that path is the care-workflow API
      // (GET/POST via same-origin rewrite). UI case pages live under /analysis/:caseId.
    ];
  },
  async rewrites() {
    if (!backendUrl) return [];
    // beforeFiles: API proxy wins over any App Router page at the same path
    // (e.g. legacy app/cases/[caseId] must not swallow GET /cases/{id} JSON).
    const apiProxies = [
      {
        source: "/auth/:path*",
        destination: `${backendUrl}/auth/:path*`,
      },
      {
        source: "/review-cases",
        destination: `${backendUrl}/review-cases`,
      },
      {
        source: "/review-cases/:path*",
        destination: `${backendUrl}/review-cases/:path*`,
      },
      {
        source: "/cases",
        destination: `${backendUrl}/cases`,
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
      {
        source: "/weekly-reports/:path*",
        destination: `${backendUrl}/weekly-reports/:path*`,
      },
      {
        source: "/weekly-briefings/:path*",
        destination: `${backendUrl}/weekly-briefings/:path*`,
      },
      {
        source: "/agent/:path*",
        destination: `${backendUrl}/agent/:path*`,
      },
    ];
    return { beforeFiles: apiProxies };
  },
};

export default nextConfig;
