/**
 * Protected Dashboard Layout
 *
 * Next.js Special Files:
 * - layout.tsx: Shared UI for a segment (required)
 * - page.tsx: UI for the segment route (required)
 * - loading.tsx: Loading UI for the segment (optional)
 * - error.tsx: Error UI for the segment (optional)
 * - not-found.tsx: 404 UI for the segment (optional)
 *
 * Directory Structure:
 * app/
 * ├── layout.tsx      # Root layout (server)
 * ├── page.tsx        # Home page (client)
 * └── dashboard/      # Protected route segment
 *     ├── layout.tsx  # Protected layout (client) - THIS FILE
 *     └── page.tsx    # Dashboard page (client)
 */

'use client';

import { checkAuth } from '@/lib/api';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

interface ProtectedLayoutProps {
    children: React.ReactNode;
}

export default function ProtectedDashboardLayout({ children }: ProtectedLayoutProps) {
    const router = useRouter();
    const [userName, setUserName] = useState<string>('');
    const [userRole, setUserRole] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [activeNav, setActiveNav] = useState('home');

    useEffect(() => {
        const token = localStorage.getItem('token') || sessionStorage.getItem('token');
        if (!token) {
            router.replace('/');
            return;
        }

        // Verify token on mount and get user info
        const loadUserInfo = async () => {
            try {
                const data = await checkAuth(token);
                setUserName(data.name || '');
                setUserRole(data.role || '');
                // Authentication successful
            } catch (err) {
                console.error('Auth verification failed:', err);
                // Clear both storage locations on error
                localStorage.removeItem('token');
                sessionStorage.removeItem('token');
                router.replace('/');
            } finally {
                setLoading(false);
            }
        };

        loadUserInfo();
    }, [router]);

    const handleLogout = async () => {
        try {
            // Clear storage
            localStorage.removeItem('token');
            sessionStorage.removeItem('token');
            router.replace('/');
        } catch (err) {
            console.error('Logout failed:', err);
            router.replace('/');
        }
    };

    // Check if user can access a specific feature based on role
    const canAccess = (requiredRole: string): boolean => {
        // Basic role hierarchy check (this can be expanded as needed)
        if (userRole === 'protexis_administrator') return true;
        return userRole === requiredRole;
    };

    // Show loading state while checking auth
    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-black text-white">
                <div className="text-2xl">Verifying access...</div>
            </div>
        );
    }

    // Render dashboard once authenticated
    return (
        <div className="min-h-screen flex flex-col bg-black text-white">
            {/* Header */}
            <div className="bg-blue-800 text-white p-4">
                <div className="flex justify-between items-center">
                    <h1 className="text-2xl font-bold">Protexis Command</h1>
                    <div className="flex items-center space-x-4">
                        <div className="flex flex-col items-end">
                            <span>Hello, {userName}</span>
                            <span className="text-xs bg-blue-600 px-2 py-0.5 rounded">
                                Role: {userRole}
                            </span>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded"
                        >
                            Log Off
                        </button>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <div className="bg-blue-700 text-white p-2">
                <div className="flex space-x-4">
                    <NavItem
                        label="HOME"
                        active={activeNav === 'home'}
                        href="/dashboard"
                        onClick={() => setActiveNav('home')}
                    />
                    <NavItem
                        label="SITES"
                        active={activeNav === 'sites'}
                        href="/dashboard/sites"
                        onClick={() => setActiveNav('sites')}
                    />
                    <NavItem
                        label="REPORTS"
                        active={activeNav === 'reports'}
                        href="/dashboard/reports"
                        onClick={() => setActiveNav('reports')}
                    />
                    <NavItem
                        label="CONTACTS"
                        active={activeNav === 'contacts'}
                        href="/dashboard/contacts"
                        onClick={() => setActiveNav('contacts')}
                    />
                    {/* Only display admin section if user has appropriate role */}
                    {(userRole === 'protexis_administrator' || userRole === 'admin') && (
                        <NavItem
                            label="ADMINISTRATION"
                            active={activeNav === 'admin'}
                            href="/dashboard/admin"
                            onClick={() => setActiveNav('admin')}
                        />
                    )}
                    <NavItem
                        label="PREFERENCES"
                        active={activeNav === 'preferences'}
                        href="/dashboard/preferences"
                        onClick={() => setActiveNav('preferences')}
                    />
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-grow">
                {children}
            </div>

            {/* Footer */}
            <div className="bg-gray-200 p-4 text-center text-sm text-gray-600">
                <div className="flex justify-between items-center">
                    <div>© 2025 Protexis Command</div>
                    <div>Technical Support: 555-279-2602</div>
                </div>
            </div>
        </div>
    );
}

// Navigation Item component with Links
function NavItem({ label, active, href, onClick }: {
    label: string;
    active: boolean;
    href: string;
    onClick: () => void;
}) {
    return (
        <Link
            href={href}
            className={`px-4 py-1 ${active ? 'bg-blue-800' : 'hover:bg-blue-600'}`}
            onClick={onClick}
        >
            {label}
        </Link>
    );
}
