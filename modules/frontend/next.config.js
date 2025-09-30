/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: [],
  },
  webpack: (config) => {
    config.resolve.alias.canvas = false
    return config
  },
}

module.exports = nextConfig
