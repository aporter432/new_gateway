import { checkAuth, getToken } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { ReactNode, useEffect, useRef, useState } from 'react';
import Header from '../common/Header';
import Navigation from '../common/Navigation';
import PageHeader from '../common/PageHeader';

interface DashboardLayoutProps {
    children: ReactNode;
    pageTitle?: string;
    activeNavItem?: string;
    userName?: string;
    userRole?: string;
}

export default function DashboardLayout({
    children,
    pageTitle,
    activeNavItem = 'home',
    userName: propUserName,
    userRole: propUserRole
}: DashboardLayoutProps) {
    const router = useRouter();
    const [userName, setUserName] = useState<string>(propUserName || '');
    const [userRole, setUserRole] = useState<string>(propUserRole || '');
    const [loading, setLoading] = useState(!propUserName || !propUserRole);
    const [activeNav, setActiveNav] = useState(activeNavItem);
    const authInProgress = useRef(false);
    const isFirstRender = useRef(true);

    useEffect(() => {
        // For React 18 Strict Mode, only run once on real mount
        if (!isFirstRender.current) return;
        isFirstRender.current = false;

        // If user info provided via props, use that and skip authentication
        if (propUserName && propUserRole) {
            setUserName(propUserName);
            setUserRole(propUserRole);
            setLoading(false);
            return;
        }

        // Prevent duplicate authentication calls
        if (authInProgress.current) return;
        authInProgress.current = true;

        const token = getToken();
        if (!token) {
            console.log('DashboardLayout: No token found, redirecting to login');
            router.push('/');
            return;
        }

        // Check if we already have cached user info
        const cachedUserInfo = sessionStorage.getItem('userInfo');
        if (cachedUserInfo) {
            try {
                const userInfo = JSON.parse(cachedUserInfo);
                setUserName(userInfo.name || '');
                setUserRole(userInfo.role || '');
                setLoading(false);
                authInProgress.current = false;
                console.log('DashboardLayout: Using cached user info');
                return;
            } catch (err) {
                console.warn('Failed to parse cached user info, fetching fresh data');
                // Fall through to fetch fresh data
            }
        }

        // Only make API call if no props and no cached data
        const loadUserInfo = async () => {
            try {
                console.log('DashboardLayout fetching user info - should only happen if not provided or cached');
                const data = await checkAuth(token);

                if (!data) {
                    throw new Error('Failed to fetch user data');
                }

                setUserName(data.name || '');
                setUserRole(data.role || '');
                // Cache user info to avoid repeated auth checks
                sessionStorage.setItem('userInfo', JSON.stringify(data));
            } catch (err) {
                console.error('Auth verification failed:', err);
                // Clear both storage locations on error
                localStorage.removeItem('token');
                sessionStorage.removeItem('token');
                sessionStorage.removeItem('userInfo');
                router.push('/');
            } finally {
                setLoading(false);
                authInProgress.current = false;
            }
        };

        loadUserInfo();

        // Cleanup function to prevent memory leaks
        return () => {
            authInProgress.current = false;
        };
    }, [router, propUserName, propUserRole]);

    const handleLogout = () => {
        // Clear storage
        if (typeof window !== 'undefined') {
            localStorage.removeItem('token');
            sessionStorage.removeItem('token');
            sessionStorage.removeItem('userInfo');
        }
        router.push('/');
    };

    const handleNavChange = (item: string) => {
        setActiveNav(item);
    };

    // Show loading state while checking auth
    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen bg-black text-white">
                <div className="text-2xl">Loading dashboard layout...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex flex-col bg-black text-white">
            {/* Header */}
            <Header
                userName={userName}
                userRole={userRole}
                onLogout={handleLogout}
            />

            {/* Navigation */}
            <Navigation
                activeItem={activeNav}
                userRole={userRole}
                onNavChange={handleNavChange}
            />

            {/* Main Content */}
            <div className="flex-grow p-8">
                {pageTitle && <PageHeader title={pageTitle} className="mb-4" />}
                {children}
            </div>

            {/* Footer */}
            <footer className="bg-gray-800 p-4 text-center text-sm text-gray-400">
                <div className="flex justify-between items-center">
                    <div>© 2025 Protexis Command</div>
                    <div>Technical Support: 555-279-2602</div>
                </div>
            </footer>
        </div>
    );
}
