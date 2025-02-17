/** @type {import('next').NextConfig} */
const config = {
    reactStrictMode: true,
    swcMinify: false,
    output: 'standalone',
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: `${process.env.BACKEND_URL}/api/:path*`,
            },
        ]
    },
    webpack: (config, { dev, isServer }) => {
        // Force webpack to watch for changes
        if (dev && !isServer) {
            config.watchOptions = {
                ...config.watchOptions,
                poll: 1000, // Check for changes every second
                aggregateTimeout: 300
            }
        }
        return config
    }
}

module.exports = config
