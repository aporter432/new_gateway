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

import { getToken } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

interface ProtectedLayoutProps {
    children: React.ReactNode;
}

export default function ProtectedDashboardLayout({ children }: ProtectedLayoutProps) {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(true);
    const checkComplete = useRef(false);

    useEffect(() => {
        // Skip multiple checks - for React 18 strict mode
        if (checkComplete.current) return;
        checkComplete.current = true;

        // This layout only performs a simple token check
        // The actual auth verification happens in the dashboard components
        const token = getToken();

        if (!token) {
            // No token found, redirect to login
            console.log("Dashboard layout: No token found, redirecting to login");
            router.push('/');
            return;
        }

        // Token exists, allow access to dashboard children
        console.log("Dashboard layout: Token found, allowing access");
        setIsLoading(false);

        // Cleanup function
        return () => {
            checkComplete.current = false;
        };
    }, [router]);

    // Show minimal loading state while checking token existence
    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-black text-white">
                <div className="text-2xl">Initializing dashboard...</div>
            </div>
        );
    }

    // Render dashboard once token is found
    return (
        <div className="min-h-screen flex flex-col bg-black text-white">
            {children}
        </div>
    );
}
