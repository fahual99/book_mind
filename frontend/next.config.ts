import type { NextConfig } from "next";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    "cacti-spearmint-hypocrisy.ngrok-free.dev",
  ],
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.gr-assets.com",
        pathname: "/books/**",
      },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/graphql",
        destination: `${BACKEND_URL}/graphql`,
      },
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
