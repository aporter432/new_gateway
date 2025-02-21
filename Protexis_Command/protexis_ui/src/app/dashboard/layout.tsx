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
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

interface ProtectedLayoutProps {
    children: React.ReactNode;
}

export default function ProtectedDashboardLayout({ children }: ProtectedLayoutProps) {
    const router = useRouter();
    const [isAuthed, setIsAuthed] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            router.replace('/');
            return;
        }

        // Verify token on mount
        const verifyAuth = async () => {
            try {
                await checkAuth(token);
                setIsAuthed(true);
            } catch (err) {
                console.error('Auth verification failed:', err);
                localStorage.removeItem('token');
                router.replace('/');
            }
        };

        verifyAuth();
    }, [router]);

    // Show nothing while checking auth
    if (!isAuthed) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-black text-white">
                <div className="text-2xl">Verifying access...</div>
            </div>
        );
    }

    // Render children once authenticated
    return (
        <div className="min-h-screen bg-black text-white">
            {/* Protected content wrapper */}
            {children}
        </div>
    );
}
