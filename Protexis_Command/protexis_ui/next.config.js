/** @type {import('next').NextConfig} */
const config = {
    reactStrictMode: true,
    swcMinify: false,
    output: 'standalone',
    // Experimental options
    experimental: {
        // Improved RSC configuration
        optimizeServerReact: true,
        // Enable proper RSC streaming
        serverActions: {
            bodySizeLimit: '2mb',
        },
        // PPR removed completely - don't add anything related to PPR here
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
            },
            // Ensure RSC requests are properly handled via proxy
            {
                source: '/:path*/_rsc/:params*',
                destination: 'http://localhost:8080/:path*?_rsc=:params*',
            },
            // Handle RSC query parameter requests
            {
                source: '/:path*',
                has: [{ type: 'query', key: '_rsc' }],
                destination: 'http://localhost:8080/:path*'
            }
        ]
    },
    // Custom headers for RSC support
    async headers() {
        return [
            {
                source: '/:path*',
                headers: [
                    {
                        key: 'Cache-Control',
                        value: 'no-store, must-revalidate',
                    },
                    // CORS headers for RSC requests
                    {
                        key: 'Access-Control-Allow-Origin',
                        value: '*', // In production, restrict this appropriately
                    },
                    {
                        key: 'Access-Control-Allow-Methods',
                        value: 'GET, POST, OPTIONS',
                    },
                    {
                        key: 'Access-Control-Allow-Headers',
                        value: 'Content-Type, Authorization, RSC, Next-Router-State-Tree, Next-Router-Prefetch',
                    },
                    {
                        key: 'Access-Control-Expose-Headers',
                        value: 'Content-Length, Content-Range, RSC, Next-Router-State-Tree, Next-Router-Prefetch, Next-URL',
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
