import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images.unsplash.com" },
      { protocol: "https", hostname: "cdn.watchbase.com" },
      { protocol: "https", hostname: "**.railway.app" },
      { protocol: "http", hostname: "localhost" },
    ],
  },
};

export default nextConfig;
