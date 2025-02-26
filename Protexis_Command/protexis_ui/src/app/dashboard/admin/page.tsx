'use client';

import { checkAuth } from '@/lib/api';
import { useEffect, useState } from 'react';

// Define available roles based on your user.py
const availableRoles = [
    { id: 'user', name: 'Standard User' },
    { id: 'admin', name: 'Admin' },
    { id: 'accounting', name: 'Accounting' },
    { id: 'protexis_administrator', name: 'Protexis Administrator' },
    { id: 'protexis_view', name: 'Protexis View' },
    { id: 'protexis_request_read', name: 'Protexis Request Read' },
    { id: 'protexis_request_write', name: 'Protexis Request Write' },
    { id: 'protexis_site_admin', name: 'Protexis Site Admin' },
    { id: 'protexis_tech_admin', name: 'Protexis Tech Admin' },
    { id: 'protexis_admin', name: 'Protexis Admin' },
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

    // Form state for new user
    const [newUser, setNewUser] = useState({
        name: '',
        email: '',
        password: '',
        role: 'user',
    });

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
            } catch (err) {
                console.error('Failed to verify role:', err);
                setLoading(false);
            }
        };

        checkUserRole();
    }, []);

    // Handle form input changes
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setNewUser({ ...newUser, [name]: value });
    };

    // Handle form submission
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // In a real app, you would send this data to your API
        // For now, we'll just update our local state
        const newId = users.length > 0 ? Math.max(...users.map(u => u.id)) + 1 : 1;

        setUsers([
            ...users,
            {
                id: newId,
                name: newUser.name,
                email: newUser.email,
                role: newUser.role,
                isActive: true,
            }
        ]);

        // Reset form
        setNewUser({
            name: '',
            email: '',
            password: '',
            role: 'user',
        });

        alert('User created successfully! (In a real app, this would be saved to the database)');
    };

    // If user doesn't have admin privileges
    if (currentUserRole !== 'admin' && currentUserRole !== 'protexis_administrator') {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
                <p>You do not have the required permissions to access this page.</p>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-4">Administration</h1>
                <p>Loading...</p>
            </div>
        );
    }

    return (
        <div className="p-8">
            <h1 className="text-2xl font-bold mb-6">User Administration</h1>

            {/* Create New User Form */}
            <div className="bg-gray-800 p-6 rounded-lg mb-8">
                <h2 className="text-xl font-semibold mb-4">Create New User</h2>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium mb-1">Name</label>
                            <input
                                type="text"
                                name="name"
                                value={newUser.name}
                                onChange={handleInputChange}
                                required
                                className="w-full p-2 bg-gray-700 rounded border border-gray-600 text-white"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1">Email</label>
                            <input
                                type="email"
                                name="email"
                                value={newUser.email}
                                onChange={handleInputChange}
                                required
                                className="w-full p-2 bg-gray-700 rounded border border-gray-600 text-white"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1">Password</label>
                            <input
                                type="password"
                                name="password"
                                value={newUser.password}
                                onChange={handleInputChange}
                                required
                                className="w-full p-2 bg-gray-700 rounded border border-gray-600 text-white"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1">Role</label>
                            <select
                                name="role"
                                value={newUser.role}
                                onChange={handleInputChange}
                                className="w-full p-2 bg-gray-700 rounded border border-gray-600 text-white"
                            >
                                {availableRoles.map(role => (
                                    <option key={role.id} value={role.id}>
                                        {role.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white"
                    >
                        Create User
                    </button>
                </form>
            </div>

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
    );
}
