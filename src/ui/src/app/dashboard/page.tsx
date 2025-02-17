/**
 * Dashboard Page Component
 *
 * Protected route that displays user information.
 * Authentication is handled by the parent layout.tsx.
 *
 * Next.js App Directory Structure:
 * app/
 * ├── api/                  # API routes
 * │   └── auth/            # Auth endpoints
 * │       ├── login/       # Login handler
 * │       ├── logout/      # Logout handler
 * │       └── me/          # User info handler
 * ├── dashboard/           # Protected routes
 * │   ├── layout.tsx      # Auth protection
 * │   └── page.tsx        # THIS FILE
 * └── page.tsx            # Login page
 */

'use client';

import { checkAuth, logout } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function DashboardPage() {
    const router = useRouter();
    const [userName, setUserName] = useState<string>('');
    const [loading, setLoading] = useState(true);

    // Get user info on mount
    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            router.replace('/');
            return;
        }

        const loadUserInfo = async () => {
            try {
                const data = await checkAuth(token);
                setUserName(data.name || '');
            } catch (err) {
                console.error('Failed to load user info:', err);
            } finally {
                setLoading(false);
            }
        };

        loadUserInfo();
    }, [router]);

    const handleLogout = async () => {
        try {
            const token = localStorage.getItem('token');
            if (token) {
                await logout();
                localStorage.removeItem('token');
            }
            router.push('/');
        } catch (err) {
            console.error('Logout failed:', err);
            // Still redirect even if logout fails
            router.push('/');
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-2xl">Loading user info...</div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto p-8">
            {/* Header with Logout */}
            <div className="flex justify-between items-center mb-12">
                <h1 className="text-3xl font-bold">Protexis Command</h1>
                <button
                    onClick={handleLogout}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded transition-all"
                >
                    Get Me The Fuck Out
                </button>
            </div>

            {/* Main Content */}
            <div className="text-center bg-gray-900 rounded-lg p-12 shadow-xl">
                <h1 className="text-4xl font-bold mb-4">
                    🎉 Congrats {userName}!
                </h1>
                <p className="text-xl text-gray-400 mb-8">
                    You successfully logged in. Now fuck off.
                </p>
                <div className="text-sm text-gray-500">
                    (Seriously though, what were you expecting to find here?)
                </div>
            </div>
        </div>
    );
}
