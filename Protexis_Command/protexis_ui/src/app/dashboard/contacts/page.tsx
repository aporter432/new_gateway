'use client';

import PageHeader from '@/components/common/PageHeader';
import { FormField, PhoneFormField } from '@/components/forms/FormField';
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

export default function ContactDashboardPage() {
    const [currentUserRole, setCurrentUserRole] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [contactData, setContactData] = useState({
        name: 'Aaron Porter',
        type: 'primary-administrator',
        companyName: 'AMCI Wireless',
        description: '',
        notes: '',
        globalContact: 'Yes',
        email: 'aaron@example.com',
        phone: '5553904744',
        extension: '',
        loginId: 'aaron@amci-wireless.com',
        // Added fields for user creation
        password: '',
        role: 'user',
        isUser: false
    });

    // Check current user's role for permission control
    useEffect(() => {
        const token = localStorage.getItem('token') || sessionStorage.getItem('token');
        if (!token) return;

        const checkUserRole = async () => {
            try {
                const data = await checkAuth(token);
                setCurrentUserRole(data.role || '');
                setLoading(false);
            } catch (error) {
                console.error('Error fetching user role:', error);
                setLoading(false);
            }
        };

        checkUserRole();
    }, []);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setContactData({
            ...contactData,
            [name]: value
        });
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        console.log('Form submitted:', contactData);

        // Here you would typically call your API to save the data
        // If isUser is true, also create a user account with the role permissions
        if (contactData.isUser) {
            console.log('Creating user account with role:', contactData.role);
            // API call would go here to create user account
        }
    };

    // Determine if user has admin permissions to create users
    const canCreateUsers = currentUserRole === 'admin' || currentUserRole === 'protexis_administrator';

    return (
        <DashboardLayout activeNavItem="contacts">
            <div className="max-w-6xl mx-auto">
                <PageHeader title="EDIT Contact Detail" />

                {/* Form Content */}
                <div className="bg-white border border-gray-300 p-4">
                    <form onSubmit={handleSubmit}>
                        <div className="grid grid-cols-[200px_1fr] gap-4 items-center mb-4">
                            <FormField
                                label="Contact Name"
                                name="name"
                                value={contactData.name}
                                onChange={handleInputChange}
                                required
                            />

                            <FormField
                                label="Contact Type"
                                name="type"
                                value={contactData.type}
                                onChange={handleInputChange}
                                type="select"
                                required
                                options={[
                                    { value: 'primary-administrator', label: 'Primary Administrator' },
                                    { value: 'secondary-administrator', label: 'Secondary Administrator' },
                                    { value: 'technician', label: 'Technician' }
                                ]}
                            />

                            <FormField
                                label="Company Name"
                                name="companyName"
                                value={contactData.companyName}
                                onChange={handleInputChange}
                                required
                            />

                            <FormField
                                label="Contact Description"
                                name="description"
                                value={contactData.description}
                                onChange={handleInputChange}
                            />

                            <FormField
                                label="Notes"
                                name="notes"
                                value={contactData.notes}
                                onChange={handleInputChange}
                                type="textarea"
                            />

                            <FormField
                                label="Global Contact?"
                                name="globalContact"
                                value={contactData.globalContact}
                                onChange={handleInputChange}
                                type="select"
                                width="w-16"
                                options={[
                                    { value: 'Yes', label: 'Yes' },
                                    { value: 'No', label: 'No' }
                                ]}
                            />

                            <FormField
                                label="Email Address"
                                name="email"
                                value={contactData.email}
                                onChange={handleInputChange}
                                type="email"
                                required
                            />

                            <PhoneFormField
                                label="Phone Number"
                                phoneName="phone"
                                phoneValue={contactData.phone}
                                extName="extension"
                                extValue={contactData.extension}
                                onChange={handleInputChange}
                            />

                            <FormField
                                label="Login ID"
                                name="loginId"
                                value={contactData.loginId}
                                onChange={handleInputChange}
                            />

                            {/* User Account Creation Fields - Only visible to admins */}
                            {canCreateUsers && (
                                <>
                                    <div className="col-span-2 mt-4 mb-2 border-t border-gray-300 pt-4">
                                        <h3 className="font-semibold text-lg">User Account Details</h3>
                                        <p className="text-sm text-gray-600">Configure this contact as a system user</p>
                                    </div>

                                    <FormField
                                        label="Create User Account"
                                        name="isUser"
                                        value={contactData.isUser ? "Yes" : "No"}
                                        onChange={(e) => {
                                            const isUser = e.target.value === "Yes";
                                            setContactData({
                                                ...contactData,
                                                isUser
                                            });
                                        }}
                                        type="select"
                                        options={[
                                            { value: "No", label: "No" },
                                            { value: "Yes", label: "Yes" }
                                        ]}
                                    />

                                    {contactData.isUser && (
                                        <>
                                            <FormField
                                                label="Password"
                                                name="password"
                                                value={contactData.password}
                                                onChange={handleInputChange}
                                                type="password"
                                                required={contactData.isUser}
                                            />

                                            <FormField
                                                label="User Role"
                                                name="role"
                                                value={contactData.role}
                                                onChange={handleInputChange}
                                                type="select"
                                                required={contactData.isUser}
                                                options={availableRoles.map(role => ({
                                                    value: role.id,
                                                    label: role.name
                                                }))}
                                            />
                                        </>
                                    )}
                                </>
                            )}

                            {/* Buttons */}
                            <div className="col-span-2 mt-6 flex justify-end space-x-4">
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
                                >
                                    Save
                                </button>
                                <button
                                    type="button"
                                    className="px-4 py-2 bg-gray-300 hover:bg-gray-400 rounded"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </DashboardLayout>
    );
}

// Simple component for navigation items
function NavItem({ label, active }: { label: string; active: boolean }) {
    return (
        <a
            href="#"
            className={`px-4 py-1 ${active ? 'bg-blue-800' : 'hover:bg-blue-600'}`}
        >
            {label}
        </a>
    );
}
