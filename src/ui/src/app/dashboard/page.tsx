/**
 * Dashboard Page Component
 *
 * Protected route that displays user information after successful authentication.
 * Implements client-side authentication check using JWT token stored in localStorage.
 *
 * Authentication Flow:
 * 1. Checks for token in localStorage
 * 2. Verifies token validity with backend
 * 3. Redirects to login if token is invalid/missing
 * 4. Displays user information if authenticated
 *
 * @component
 */

'use client';

import { checkAuth, logout } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function Dashboard() {
    const router = useRouter();
    const [userName, setUserName] = useState<string>('');

    // Authentication check on component mount
    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            router.push('/');
            return;
        }

        /**
         * Verify user authentication with backend
         * Redirects to login page if verification fails
         */
        const verifyAuth = async () => {
            try {
                const data = await checkAuth(token);
                setUserName(data.name || '');
            } catch (err) {
                console.error('Auth check failed:', err);
                router.push('/');
            }
        };

        verifyAuth();
    }, [router]);

    /**
     * Handle user logout
     * Clears token and redirects to login page
     */
    const handleLogout = async () => {
        try {
            await logout();
            localStorage.removeItem('token');
        } catch (err) {
            console.error('Logout failed:', err);
        } finally {
            router.push('/');
        }
    };

    return (
        <main className="min-h-screen bg-black text-white">
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
        </main>
    );
}
