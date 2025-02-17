import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://proxy:8080';

export async function POST(request: Request) {
    try {
        const body = await request.formData();
        const username = body.get('username');
        const password = body.get('password');

        if (!username || !password) {
            return NextResponse.json(
                { error: 'Username and password are required' },
                { status: 400 }
            );
        }

        console.log('Login attempt:', {
            username,
            backendUrl: BACKEND_URL,
            timestamp: new Date().toISOString()
        });

        const response = await fetch(`${BACKEND_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
            },
            body: `username=${encodeURIComponent(username.toString())}&password=${encodeURIComponent(password.toString())}&grant_type=password`,
        });

        console.log('Backend response:', {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries()),
            url: response.url
        });

        const responseText = await response.text();
        console.log('Response body:', responseText);

        if (!response.ok) {
            console.error('Authentication failed:', {
                status: response.status,
                statusText: response.statusText,
                body: responseText,
                url: `${BACKEND_URL}/api/auth/login`,
            });
            return NextResponse.json(
                { error: responseText || 'Authentication failed' },
                { status: response.status }
            );
        }

        try {
            const data = JSON.parse(responseText);
            console.log('Authentication successful');
            return NextResponse.json(data);
        } catch (error) {
            console.error('Failed to parse response:', {
                error: error instanceof Error ? error.message : String(error),
                responseText,
            });
            return NextResponse.json(
                { error: 'Invalid response from server' },
                { status: 500 }
            );
        }
    } catch (error) {
        console.error('Authentication error:', {
            error: error instanceof Error ? error.message : String(error),
            stack: error instanceof Error ? error.stack : undefined,
            backendUrl: BACKEND_URL,
        });
        return NextResponse.json(
            { error: 'Authentication service unavailable' },
            { status: 503 }
        );
    }
}
