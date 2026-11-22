import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  // Live demo: phones and laptops open the dev server by LAN IP (or name.local), e.g. http://192.168.1.20:3000/join,
  // or through a cloudflared quick tunnel when the venue Wi-Fi keeps devices apart
  allowedDevOrigins: ["*.*.*.*", "*.local", "*.trycloudflare.com"],
  partialPrefetching: true,
  // the room screen moved from /live to /; old links and QR codes (?join=… passes through) still land on it
  async redirects() {
    return [{ source: "/live", destination: "/", permanent: false }];
  },
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
