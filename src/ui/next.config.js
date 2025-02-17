/** @type {import('next').NextConfig} */
const config = {
    reactStrictMode: true,
    swcMinify: false,
    output: 'standalone',
    // Disable server components and enable client-side routing
    experimental: {
        appDir: true,
        serverActions: false,
    },
    pageExtensions: ['tsx', 'ts'],
    // Rewrite API routes to our backend
    async rewrites() {
        return [
            {
                // Forward auth requests to our FastAPI backend
                source: '/api/auth/:path*',
                destination: 'http://localhost:8080/api/auth/:path*',
            },
            {
                // Forward API requests to our FastAPI backend
                source: '/api/:path*',
                destination: 'http://localhost:8080/api/:path*',
            }
        ]
    },
    // Disable automatic static optimization for dynamic routes
    async headers() {
        return [
            {
                source: '/:path*',
                headers: [
                    {
                        key: 'Cache-Control',
                        value: 'no-store, must-revalidate',
                    }
                ],
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
