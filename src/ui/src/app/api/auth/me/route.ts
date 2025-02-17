import { NextResponse } from 'next/server';

/**
 * Backend URL Configuration
 *
 * This service acts as a proxy between the frontend and our Gateway API.
 * All authentication requests are routed to /api/auth/* on our backend,
 * which is separate from the OGWS API (/api/v1.0/*).
 *
 * The backend handles:
 * - User authentication
 * - Session management
 * - OGWS API communication (internally)
 */
const BACKEND_URL = process.env.BACKEND_URL || 'http://proxy:8080';

/**
 * GET /api/auth/me
 *
 * Retrieves the current user's information.
 * This endpoint proxies to our Gateway API, not directly to OGWS.
 *
 * Flow:
 * 1. Frontend calls this endpoint (/api/auth/me)
 * 2. This handler forwards to Gateway API (/api/auth/me)
 * 3. Gateway API validates the token
 * 4. Gateway API returns user info
 */
export async function GET(request: Request) {
    try {
        const token = request.headers.get('Authorization');

        if (!token) {
            return NextResponse.json(
                { error: 'No token provided' },
                { status: 401 }
            );
        }

        // Forward request to Gateway API
        // Important: Keep the /api/auth/me path to match our Gateway API routes
        const response = await fetch(`${BACKEND_URL}/api/auth/me`, {
            method: 'GET',
            headers: {
                'Authorization': token,
                'Accept': 'application/json',
            },
        });

        if (!response.ok) {
            return NextResponse.json(
                { error: 'Authentication failed' },
                { status: response.status }
            );
        }

        const data = await response.json();
        return NextResponse.json(data);
    } catch (error) {
        console.error('Error in /me endpoint:', error);
        return NextResponse.json(
            { error: 'Authentication service unavailable' },
            { status: 503 }
        );
    }
}
