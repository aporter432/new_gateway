'use client';

import { useState } from 'react';
import { FormField, PhoneFormField } from '@/components/forms/FormField';

export default function ContactDashboardPage() {
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
        loginId: 'aaron@amci-wireless.com'
    });

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
    };

    return (
        <div className="max-w-6xl mx-auto">
            {/* Header */}
            <div className="bg-blue-800 text-white p-4">
                <div className="flex justify-between items-center">
                    <h1 className="text-2xl font-bold">Protexis Command</h1>
                    <div>
                        <button className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded">
                            Log Off
                        </button>
                    </div>
                </div>
            </div>

            {/* Navigation Bar */}
            <div className="bg-blue-700 text-white p-2">
                <div className="flex space-x-4">
                    <NavItem label="HOME" active={false} />
                    <NavItem label="SITES" active={false} />
                    <NavItem label="REPORTS" active={false} />
                    <NavItem label="CONTACTS" active={true} />
                    <NavItem label="ADMINISTRATION" active={false} />
                    <NavItem label="PREFERENCES" active={false} />
                </div>
            </div>

            {/* Main Content */}
            <div className="mt-4">
                <div className="bg-blue-700 text-white p-2">
                    <h2 className="text-lg font-bold">EDIT Contact Detail</h2>
                </div>

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
                        </div>

                        {/* Action Buttons */}
                        <div className="flex justify-center space-x-2 mt-8">
                            <button
                                type="submit"
                                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2"
                            >
                                UPDATE
                            </button>
                            <button
                                type="button"
                                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2"
                            >
                                UPDATE & COPY
                            </button>
                            <button
                                type="button"
                                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2"
                            >
                                RESET & SEND PASSWORD
                            </button>
                            <button
                                type="button"
                                className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2"
                            >
                                CANCEL
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
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
