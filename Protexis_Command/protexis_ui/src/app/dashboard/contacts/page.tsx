'use client';

import PageHeader from '@/components/common/PageHeader';
import { FormField, PhoneFormField } from '@/components/forms/FormField';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { canAssignRole, checkAuth, createContact, createUser } from '@/lib/api';
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

// Sample data for contacts table
const mockContacts = [
    { id: 1, name: 'John Doe', company: 'AMCI Wireless', type: 'Primary Administrator', login: 'john@example.com', global: 'Yes' },
    { id: 2, name: 'Jane Smith', company: 'Protexis', type: 'Secondary Administrator', login: 'jane@example.com', global: 'No' },
    { id: 3, name: 'Robert Johnson', company: 'AMCI Wireless', type: 'Technician', login: 'robert@example.com', global: 'Yes' },
];

// Sample data for company dropdown
const mockCompanies = [
    { id: 2, name: 'Protexis' },
    { id: 3, name: 'Gateway Solutions' },
];

export default function ContactDashboardPage() {
    const [currentUserRole, setCurrentUserRole] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [showContactForm, setShowContactForm] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCompany, setSelectedCompany] = useState('');
    const [contacts, setContacts] = useState(mockContacts);
    const ProtexisLogo = '/protexis-logo.png';

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

    // Handle search/filter
    const handleDisplay = () => {
        // In a real application, this would fetch filtered data from the API
        console.log('Filtering with:', { searchTerm, selectedCompany });
        // For demo, just filter the mock data
        const filtered = mockContacts.filter(contact => {
            const matchesSearch = searchTerm === '' ||
                contact.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                contact.company.toLowerCase().includes(searchTerm.toLowerCase());

            const matchesCompany = selectedCompany === '' ||
                contact.company === selectedCompany;

            return matchesSearch && matchesCompany;
        });

        setContacts(filtered);
    };

    // Handle export functions
    const handleExport = (type: 'copy' | 'csv' | 'excel') => {
        console.log(`Exporting as ${type}`);
        // Implement export functionality here
    };

    // Determine if user has admin permissions to create users
    const canCreateUsers = currentUserRole === 'admin' || currentUserRole === 'protexis_administrator';

    if (loading) {
        return (
            <DashboardLayout activeNavItem="contacts">
                <div className="p-4">Loading contacts...</div>
            </DashboardLayout>
        );
    }

    if (showContactForm) {
        // Display the contact creation/edit form
        return <ContactForm onCancel={() => setShowContactForm(false)} currentUserRole={currentUserRole} />;
    }

    // Display the contacts listing page (similar to the image)
    return (
        <DashboardLayout activeNavItem="contacts">
            <div className="bg-blue-700 text-white p-4 flex justify-between items-center">
                <h1 className="text-xl font-bold">Contacts</h1>
                <button className="p-2 bg-blue-600 rounded-full">
                    <span className="text-xl">ⓘ</span>
                </button>
            </div>

            <div className="p-4 space-y-4">
                {/* Search and Filter Controls */}
                <div className="flex items-center space-x-2 mb-4">
                    <div className="relative">
                        <select
                            className="border px-4 py-2 pr-8 rounded appearance-none bg-white"
                            value={selectedCompany}
                            onChange={(e) => setSelectedCompany(e.target.value)}
                        >
                            <option value="">SELECT COMPANIES</option>
                            {mockCompanies.map(company => (
                                <option key={company.id} value={company.name}>
                                    {company.name}
                                </option>
                            ))}
                        </select>
                        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                            <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                                <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                            </svg>
                        </div>
                    </div>

                    <input
                        type="text"
                        placeholder="Contact Search"
                        className="border px-4 py-2 rounded"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />

                    <button
                        className="bg-blue-800 text-white px-4 py-2 rounded"
                        onClick={handleDisplay}
                    >
                        DISPLAY
                    </button>

                    <div className="flex-1"></div>

                    <button
                        className="bg-blue-800 text-white px-4 py-2 rounded"
                        onClick={() => setShowContactForm(true)}
                    >
                        ADD NEW CONTACT
                    </button>
                </div>

                <div>
                    <p className="text-sm mb-2">Select companies above and/or enter a search term and click 'Display'.</p>
                    <div className="flex space-x-2 mb-4">
                        <button
                            className="border px-4 py-1"
                            onClick={() => handleExport('copy')}
                        >
                            COPY
                        </button>
                        <button
                            className="border px-4 py-1"
                            onClick={() => handleExport('csv')}
                        >
                            CSV
                        </button>
                        <button
                            className="border px-4 py-1"
                            onClick={() => handleExport('excel')}
                        >
                            EXCEL
                        </button>
                        <div className="flex-1"></div>
                        <div className="flex items-center">
                            <span className="mr-2">Search:</span>
                            <input type="text" className="border p-1 rounded" />
                        </div>
                    </div>
                </div>

                {/* Contacts Table */}
                <table className="min-w-full bg-white border">
                    <thead className="bg-gray-100">
                        <tr>
                            <th className="border-b p-2 text-left">Contact Name</th>
                            <th className="border-b p-2 text-left">Contact Company</th>
                            <th className="border-b p-2 text-left">Contact Type</th>
                            <th className="border-b p-2 text-left">Login</th>
                            <th className="border-b p-2 text-left">Global?</th>
                            <th className="border-b p-2 text-left">Commands</th>
                        </tr>
                    </thead>
                    <tbody>
                        {contacts.length === 0 ? (
                            <tr>
                                <td colSpan={6} className="border-b p-2 text-center text-gray-500">
                                    No Records Found.
                                </td>
                            </tr>
                        ) : (
                            contacts.map(contact => (
                                <tr key={contact.id}>
                                    <td className="border-b p-2">{contact.name}</td>
                                    <td className="border-b p-2">{contact.company}</td>
                                    <td className="border-b p-2">{contact.type}</td>
                                    <td className="border-b p-2">{contact.login}</td>
                                    <td className="border-b p-2">{contact.global}</td>
                                    <td className="border-b p-2">
                                        <button
                                            className="text-blue-600 hover:text-blue-800"
                                            onClick={() => setShowContactForm(true)}
                                        >
                                            Edit
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>

                <div className="text-sm">
                    Showing {contacts.length} of {contacts.length} entries
                </div>
            </div>
        </DashboardLayout>
    );
}

// Create a separate component for the contact form
function ContactForm({ onCancel, currentUserRole }: { onCancel: () => void, currentUserRole: string }) {
    const [contactData, setContactData] = useState({
        name: '',
        type: 'primary-administrator',
        companyName: 'AMCI Wireless',
        description: '',
        notes: '',
        globalContact: 'Yes',
        email: '',
        phone: '',
        extension: '',
        loginId: '',
        // User creation field
        role: '',
        isUser: false
    });

    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [rolePermissionCheck, setRolePermissionCheck] = useState<{ [key: string]: boolean }>({});

    // Check if the current user can assign a role when the role selection changes
    useEffect(() => {
        if (contactData.role && currentUserRole) {
            const checkRolePermission = async () => {
                try {
                    const result = await canAssignRole(contactData.role);
                    setRolePermissionCheck(prev => ({
                        ...prev,
                        [contactData.role]: result.can_assign
                    }));

                    if (!result.can_assign) {
                        setError(`You don't have permission to assign the role: ${contactData.role}`);
                    } else {
                        setError(null);
                    }
                } catch (err) {
                    console.error('Error checking role permission:', err);
                }
            };

            checkRolePermission();
        }
    }, [contactData.role, currentUserRole]);

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setContactData({
            ...contactData,
            [name]: value
        });
    };

    const handleRoleSelect = (role: string) => {
        setContactData({
            ...contactData,
            role
        });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        setError(null);
        setSuccessMessage(null);

        // Validate email format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(contactData.email)) {
            setError('Please enter a valid email address');
            setIsSubmitting(false);
            return;
        }

        // Validate required fields
        if (!contactData.name) {
            setError('Contact name is required');
            setIsSubmitting(false);
            return;
        }

        // Validate role if creating user
        if (contactData.isUser && !contactData.role) {
            setError('Please select a permission role for the user');
            setIsSubmitting(false);
            return;
        }

        // Check role permission one more time
        if (contactData.isUser && contactData.role && rolePermissionCheck[contactData.role] === false) {
            setError(`You don't have permission to assign the role: ${contactData.role}`);
            setIsSubmitting(false);
            return;
        }

        try {
            // 1. Create the contact record
            const contactPayload = {
                name: contactData.name,
                type: contactData.type,
                company: contactData.companyName,
                description: contactData.description,
                notes: contactData.notes,
                global: contactData.globalContact === 'Yes',
                email: contactData.email,
                phone: contactData.phone,
                extension: contactData.extension,
                login_id: contactData.loginId
            };

            const createdContact = await createContact(contactPayload);
            console.log('Contact created:', createdContact);

            // 2. If isUser is true, also create a user account with the role permissions
            if (contactData.isUser && contactData.role) {
                const userPayload = {
                    email: contactData.email,
                    name: contactData.name,
                    role: contactData.role
                };

                const createdUser = await createUser(userPayload);
                console.log('User account created with role:', createdUser);
                setSuccessMessage('Contact and user account created successfully. A password has been sent to the user\'s email.');
            } else {
                setSuccessMessage('Contact created successfully');
            }

            // After submission, return to the contacts listing
            setTimeout(() => onCancel(), 1500);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create contact');
        } finally {
            setIsSubmitting(false);
        }
    };

    // Determine if user has admin permissions to create users
    const canCreateUsers = currentUserRole === 'admin' || currentUserRole === 'protexis_administrator';

    return (
        <DashboardLayout activeNavItem="contacts">
            <div className="max-w-6xl mx-auto">
                <PageHeader title="ADD Contact Detail" />

                {/* Form Content */}
                <div className="bg-white border border-gray-300 p-4">
                    {error && (
                        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                            {error}
                        </div>
                    )}

                    {successMessage && (
                        <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
                            {successMessage}
                        </div>
                    )}

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

                            <FormField
                                label="Permission Role"
                                name="role"
                                value={contactData.role}
                                onChange={handleInputChange}
                                type="select"
                                options={[
                                    { value: '', label: '- permission role not assigned -' },
                                    { value: 'accounting', label: 'accounting' },
                                    { value: 'protexis_administrator', label: 'protexis_administrator' },
                                    { value: 'protexis_view', label: 'protexis_view' },
                                    { value: 'protexis_request_read', label: 'protexis_request_read' },
                                    { value: 'protexis_request_write', label: 'protexis_request_write' },
                                    { value: 'protexis_site_admin', label: 'protexis_site_admin' },
                                    { value: 'protexis_tech_admin', label: 'protexis_tech_admin' }
                                ]}
                            />

                            {contactData.isUser && (
                                <div className="col-span-2 mt-2 mb-4 p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-800">
                                    <p><strong>Note:</strong> A system-generated password will be created and sent to the email address provided above.</p>
                                    <p className="mt-1">The user will need to use this password for their first login.</p>
                                </div>
                            )}

                            {/* Buttons */}
                            <div className="col-span-2 mt-6 flex justify-center space-x-4">
                                <button
                                    type="submit"
                                    className="px-6 py-2 bg-blue-700 hover:bg-blue-800 text-white font-bold"
                                    disabled={isSubmitting}
                                >
                                    {isSubmitting ? 'Adding...' : 'ADD'}
                                </button>
                                <button
                                    type="button"
                                    className="px-6 py-2 bg-blue-700 hover:bg-blue-800 text-white font-bold"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        console.log('Add & Copy');
                                        // Implement Add & Copy functionality
                                    }}
                                    disabled={isSubmitting}
                                >
                                    ADD & COPY
                                </button>
                                <button
                                    type="button"
                                    onClick={onCancel}
                                    className="px-6 py-2 bg-blue-700 hover:bg-blue-800 text-white font-bold"
                                    disabled={isSubmitting}
                                >
                                    CANCEL
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
