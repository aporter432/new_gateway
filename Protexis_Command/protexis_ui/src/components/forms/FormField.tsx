import React from 'react';

interface FormFieldProps {
    label: string;
    name: string;
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void;
    type?: 'text' | 'email' | 'tel' | 'select' | 'textarea' | 'password';
    required?: boolean;
    width?: string;
    options?: { value: string; label: string }[];
    placeholder?: string;
}

export function FormField({
    label,
    name,
    value,
    onChange,
    type = 'text',
    required = false,
    width = 'w-64',
    options = [],
    placeholder = ''
}: FormFieldProps) {
    return (
        <>
            <label className="text-right font-medium text-gray-700 text-sm">
                {required && <span className="text-red-500 font-bold">* </span>}
                {label}:
            </label>

            {type === 'select' ? (
                <select
                    name={name}
                    value={value}
                    onChange={onChange}
                    className={`border border-gray-300 p-2 rounded ${width}`}
                    required={required}
                >
                    {options.map(option => (
                        <option key={option.value} value={option.value}>
                            {option.label}
                        </option>
                    ))}
                </select>
            ) : type === 'textarea' ? (
                <textarea
                    name={name}
                    value={value}
                    onChange={onChange}
                    className={`border border-gray-300 p-2 rounded ${width}`}
                    required={required}
                    placeholder={placeholder}
                    rows={4}
                />
            ) : (
                <input
                    type={type}
                    name={name}
                    value={value}
                    onChange={onChange}
                    className={`border border-gray-300 p-2 rounded ${width}`}
                    required={required}
                    placeholder={placeholder}
                />
            )}
        </>
    );
}

// Extension for a phone field with extension
export function PhoneFormField({
    label,
    phoneName,
    phoneValue,
    extName,
    extValue,
    onChange,
    required = false
}: {
    label: string;
    phoneName: string;
    phoneValue: string;
    extName: string;
    extValue: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    required?: boolean;
}) {
    return (
        <>
            <label className="text-right font-medium text-gray-700 text-sm">
                {required && <span className="text-red-500 font-bold">* </span>}
                {label}:
            </label>
            <div className="flex">
                <input
                    type="tel"
                    name={phoneName}
                    value={phoneValue}
                    onChange={onChange}
                    className="border border-gray-300 p-2 rounded w-32"
                    required={required}
                />
                <span className="mx-2 self-center">Ext:</span>
                <input
                    type="text"
                    name={extName}
                    value={extValue}
                    onChange={onChange}
                    className="border border-gray-300 p-2 rounded w-16"
                />
            </div>
        </>
    );
}
