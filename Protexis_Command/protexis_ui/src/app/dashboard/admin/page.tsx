'use client';

import DashboardLayout from '@/components/layout/DashboardLayout';
import { checkAuth } from '@/lib/api';
import { useEffect, useState } from 'react';

// Define available roles based on your user.py
const availableRoles = [
    { id: 'accounting', name: 'Accounting' },
    { id: 'protexis_administrator', name: 'Protexis Administrator' },
    { id: 'protexis_view', name: 'Protexis View' },
    { id: 'protexis_request_read', name: 'Protexis Request Read' },
    { id: 'protexis_request_write', name: 'Protexis Request Write' },
    { id: 'protexis_site_admin', name: 'Protexis Site Admin' },
    { id: 'protexis_tech_admin', name: 'Protexis Tech Admin' },
];

// Mock user data for MVP display
const mockUsers = [
    { id: 1, name: 'John Doe', email: 'john@example.com', role: 'user', isActive: true },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', role: 'admin', isActive: true },
];

export default function AdminPage() {
    const [currentUserRole, setCurrentUserRole] = useState<string>('');
    const [users, setUsers] = useState(mockUsers);
    const [loading, setLoading] = useState(true);

    // Check current user's role
    useEffect(() => {
        const token = localStorage.getItem('token') || sessionStorage.getItem('token');
        if (!token) return;

        const checkUserRole = async () => {
            try {
                const data = await checkAuth(token);
                setCurrentUserRole(data.role || '');

                // In a real app, you would fetch users from your API here
                // For now, we'll use mock data
                setLoading(false);
            } catch (error) {
                console.error('Error fetching user role:', error);
            } finally {
                setLoading(false);
            }
        };

        checkUserRole();
    }, []);

    if (loading) {
        return <div className="p-4">Loading user management...</div>;
    }

    // Only allow admin access
    if (currentUserRole !== 'admin' && currentUserRole !== 'protexis_administrator') {
        return (
            <DashboardLayout activeNavItem="admin">
                <div className="bg-red-600 text-white p-4 rounded">
                    Access Denied: You do not have permission to view this page.
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout activeNavItem="admin">
            <div className="space-y-8">


                {/* User List */}
                <div className="bg-gray-800 p-6 rounded-lg">
                    <h2 className="text-xl font-semibold mb-4">Existing Users</h2>

                    <div className="overflow-x-auto">
                        <table className="min-w-full bg-gray-900 rounded-lg">
                            <thead>
                                <tr className="border-b border-gray-800">
                                    <th className="text-left p-4">ID</th>
                                    <th className="text-left p-4">Name</th>
                                    <th className="text-left p-4">Email</th>
                                    <th className="text-left p-4">Role</th>
                                    <th className="text-left p-4">Status</th>
                                    <th className="text-left p-4">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users.map(user => (
                                    <tr key={user.id} className="border-b border-gray-800">
                                        <td className="p-4">{user.id}</td>
                                        <td className="p-4">{user.name}</td>
                                        <td className="p-4">{user.email}</td>
                                        <td className="p-4">
                                            <span className="px-2 py-1 bg-blue-900 rounded text-xs">
                                                {user.role}
                                            </span>
                                        </td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded text-xs ${user.isActive ? 'bg-green-800' : 'bg-red-800'}`}>
                                                {user.isActive ? 'Active' : 'Inactive'}
                                            </span>
                                        </td>
                                        <td className="p-4">
                                            <button className="px-2 py-1 bg-yellow-600 hover:bg-yellow-700 rounded text-xs mr-2">
                                                Edit
                                            </button>
                                            <button className={`px-2 py-1 rounded text-xs ${user.isActive ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'}`}>
                                                {user.isActive ? 'Deactivate' : 'Activate'}
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
