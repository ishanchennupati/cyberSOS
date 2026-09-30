/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow verification builds alongside a running development server.
  distDir: process.env.CYBERSOS_BUILD_DIR || ".next",
};

export default nextConfig;
