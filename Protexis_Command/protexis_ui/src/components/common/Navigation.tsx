import Link from 'next/link';

interface NavItem {
    label: string;
    href: string;
    requiresRoles?: string[];
}

interface NavigationProps {
    activeItem: string;
    userRole?: string;
    onNavChange?: (item: string) => void;
}

// Default navigation items
const defaultNavItems: NavItem[] = [
    { label: 'HOME', href: '/dashboard' },
    { label: 'SITES', href: '/dashboard/sites' },
    { label: 'REPORTS', href: '/dashboard/reports' },
    {
        label: 'MANAGE CONTACTS',
        href: '/dashboard/contacts',
        requiresRoles: ['admin', 'protexis_site_admin']
    },
    {
        label: 'ADMINISTRATION',
        href: '/dashboard/admin',
        requiresRoles: ['admin', 'protexis_administrator']
    },
    {
        label: 'COMPANY MANAGEMENT',
        href: '/dashboard/companies',
        requiresRoles: ['admin', 'protexis_administrator']
    },
];

export default function Navigation({ activeItem, userRole, onNavChange }: NavigationProps) {
    // Filter nav items by user role if needed
    const navItems = defaultNavItems.filter(item => {
        if (!item.requiresRoles) return true;
        if (!userRole) return false;
        return item.requiresRoles.includes(userRole);
    });

    return (
        <nav className="bg-blue-700 text-white p-2">
            <div className="flex space-x-4">
                {navItems.map((item) => (
                    <Link
                        key={item.label}
                        href={item.href}
                        className={`px-4 py-2 font-montserrat tracking-wide transition-colors duration-200 ${activeItem === item.label.toLowerCase()
                            ? 'bg-blue-800'
                            : 'hover:bg-blue-600'
                            }`}
                        onClick={() => onNavChange && onNavChange(item.label.toLowerCase())}
                    >
                        {item.label}
                    </Link>
                ))}
            </div>
        </nav>
    );
}
