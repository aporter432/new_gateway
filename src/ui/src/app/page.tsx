/**
 * Login Page Component
 *
 * Main authentication entry point for the application.
 * Handles user login and token management.
 *
 * Authentication Flow:
 * 1. User submits credentials
 * 2. Credentials sent to backend via Next.js API route
 * 3. On success, JWT token stored in localStorage
 * 4. User redirected to dashboard
 *
 * @component
 */

'use client';

import { login } from '@/lib/api';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function Home() {
    const router = useRouter();
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    /**
     * Handle login form submission
     * @param e Form submission event
     */
    async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        const formData = new FormData(e.currentTarget);
        const username = formData.get('username') as string;
        const password = formData.get('password') as string;

        try {
            const data = await login(username, password);
            localStorage.setItem('token', data.access_token);
            router.push('/dashboard');
        } catch (err) {
            console.error('Login error:', err);
            setError(err instanceof Error ? err.message : 'Invalid username or password');
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <main className="relative min-h-screen w-screen bg-black text-white">
            <div
                className="absolute left-[400px] top-1/2 -translate-y-1/2 w-full max-w-md p-8 bg-white shadow-lg rounded-lg text-center"
            >
                {/* Branding Section */}
                <div className="text-center mb-6">
                    <h1 className="text-3xl font-bold text-black">Protexis Command</h1>
                    <p className="text-sm text-gray-500 mt-2">BECAUSE WE ARENT DICK SUCKERS</p>
                    <p className="text-sm text-gray-500 mt-2">We Know the Work. That's Why We Built the Tech.</p>
                </div>

                {/* Error Message */}
                {error && (
                    <div className="mb-4 p-2 bg-red-100 border border-red-400 text-red-700 rounded">
                        {error}
                    </div>
                )}

                {/* Login Form */}
                <form onSubmit={handleSubmit} className="w-full space-y-4 flex flex-col items-center">
                    <input
                        name="username"
                        type="email"
                        placeholder="Email"
                        required
                        className="w-full px-4 py-2 border rounded-lg focus:ring focus:ring-blue-300 focus:outline-none text-black"
                    />
                    <input
                        name="password"
                        type="password"
                        placeholder="Password"
                        required
                        className="w-full px-4 py-2 border rounded-lg focus:ring focus:ring-blue-300 focus:outline-none text-black"
                    />
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg transition-all disabled:opacity-50"
                    >
                        {isLoading ? 'Signing In...' : 'Sign In'}
                    </button>
                </form>

                {/* Forgot Password */}
                <div className="mt-4 text-sm">
                    <Link href="#" className="text-blue-600 hover:underline">Forgot Password?</Link>
                </div>

                {/* Footer */}
                <footer className="text-xs text-gray-400 mt-6 text-center">
                    &copy; {new Date().getFullYear()} Protexis Command. All rights reserved.
                </footer>
            </div>
        </main>
    );
}
