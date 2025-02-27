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

import DashboardLayout from '@/components/layout/DashboardLayout';
import { checkAuth, getToken } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

// Component for activity items
function ActivityItem({ title, time, description }: { title: string; time: string; description: string }) {
    return (
        <div className="border-b border-gray-700 pb-4">
            <div className="flex justify-between mb-2">
                <h3 className="font-semibold">{title}</h3>
                <span className="text-sm text-gray-400">{time}</span>
            </div>
            <p className="text-gray-300">{description}</p>
        </div>
    );
}

export default function DashboardHomePage() {
    const router = useRouter();
    const [userName, setUserName] = useState('');
    const [userRole, setUserRole] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const authInProgress = useRef(false);
    const isFirstRender = useRef(true);

    // Mock statistics for dashboard
    const stats = [
        { label: 'Total Sites', value: 1254, color: 'bg-blue-500' },
        { label: 'Active Alerts', value: 7, color: 'bg-yellow-500' },
        { label: 'Critical Issues', value: 2, color: 'bg-red-500' },
        { label: 'Pending Tasks', value: 12, color: 'bg-green-500' }
    ];

    useEffect(() => {
        // For React 18 Strict Mode and RSC compatibility:
        // Only run the authentication once per actual mount (not double-render)
        if (!isFirstRender.current) return;
        isFirstRender.current = false;

        // Prevent duplicate authentication calls
        if (authInProgress.current) return;
        authInProgress.current = true;

        const token = getToken();
        if (!token) {
            console.log('No token found, redirecting to login');
            router.push('/');
            return;
        }

        // First check if we have cached user info to avoid redundant API calls
        const cachedUserInfo = sessionStorage.getItem('userInfo');
        if (cachedUserInfo) {
            try {
                const userInfo = JSON.parse(cachedUserInfo);
                setUserName(userInfo.name || '');
                setUserRole(userInfo.role || '');
                setLoading(false);
                authInProgress.current = false;
                console.log('Using cached user info');
                return;
            } catch (err) {
                console.warn('Failed to parse cached user info, fetching fresh data');
                // Fall through to fetch fresh data
            }
        }

        // Only fetch user info if not already cached
        const getUserInfo = async () => {
            try {
                console.log('Dashboard page fetching user info');
                const data = await checkAuth(token);

                if (!data) {
                    throw new Error('Failed to fetch user data');
                }

                setUserName(data.name || '');
                setUserRole(data.role || '');

                // Cache the user info to prevent redundant API calls
                sessionStorage.setItem('userInfo', JSON.stringify(data));
                setLoading(false);
            } catch (error) {
                console.error('Error fetching user info:', error);
                setError('Failed to load user data. Please try logging in again.');
                setLoading(false);

                // Clear tokens on authentication failure
                localStorage.removeItem('token');
                sessionStorage.removeItem('token');
                sessionStorage.removeItem('userInfo');

                // Redirect to login after a short delay to allow error to be displayed
                setTimeout(() => {
                    router.push('/');
                }, 2000);
            } finally {
                authInProgress.current = false;
            }
        };

        getUserInfo();

        // Cleanup function
        return () => {
            authInProgress.current = false;
        };
    }, [router]);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-black text-white">
                <div className="text-2xl">Loading dashboard data...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-black text-white">
                <div className="text-2xl text-red-500">{error}</div>
            </div>
        );
    }

    return (
        <DashboardLayout
            activeNavItem="home"
            userName={userName}
            userRole={userRole}
        >
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-2">Welcome to Protexis Command</h1>
                <p className="text-xl text-gray-300">
                    Hello, {userName} | Role: {userRole}
                </p>
                <p className="mt-4">
                    This dashboard provides you with an overview of your Protexis system.
                    Use the navigation menu to access different sections.
                </p>
            </div>

            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {stats.map((stat, index) => (
                    <div key={index} className="bg-gray-800 p-6 rounded-lg shadow-md">
                        <div className={`${stat.color} w-12 h-12 rounded-full flex items-center justify-center mb-4`}>
                            <span className="text-white text-xl font-bold">{index + 1}</span>
                        </div>
                        <h3 className="text-lg font-semibold mb-1">{stat.label}</h3>
                        <p className="text-3xl font-bold">{stat.value}</p>
                    </div>
                ))}
            </div>

            {/* Recent Activity */}
            <div>
                <h2 className="text-2xl font-bold mb-4">Recent Activity</h2>
                <div className="bg-gray-800 rounded-lg shadow-md p-6">
                    <div className="space-y-4">
                        <ActivityItem
                            title="System Update Completed"
                            time="Today, 14:32"
                            description="Software update v2.3.1 was successfully installed."
                        />
                        <ActivityItem
                            title="New User Created"
                            time="Yesterday, 10:15"
                            description="New user 'John Smith' was added to the system."
                        />
                        <ActivityItem
                            title="Alert Resolved"
                            time="Feb 25, 08:43"
                            description="Connection issue at Site #245 has been resolved."
                        />
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
