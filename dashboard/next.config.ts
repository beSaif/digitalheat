import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  // Live demo: friends' laptops open the dev server by LAN IP (or name.local), e.g. http://192.168.1.20:3000/node/basel
  allowedDevOrigins: ["*.*.*.*", "*.local"],
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
