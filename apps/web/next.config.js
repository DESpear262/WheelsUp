/** @type {import('next').NextConfig} */
const nextConfig = {
  // Exclude OpenSearch client from client-side bundles
  serverExternalPackages: ['@opensearch-project/opensearch'],
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Exclude OpenSearch from client-side bundle
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
        stream: false,
        url: false,
        zlib: false,
        http: false,
        https: false,
        assert: false,
        os: false,
        path: false,
      };
    }
    return config;
  },
};

module.exports = nextConfig;
