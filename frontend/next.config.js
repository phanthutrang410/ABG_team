/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
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
};

module.exports = nextConfig;
