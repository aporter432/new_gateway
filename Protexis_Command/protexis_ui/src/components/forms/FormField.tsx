import React from 'react';

interface FormFieldProps {
    label: string;
    name: string;
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => void;
    type?: 'text' | 'email' | 'tel' | 'select' | 'textarea';
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
            <label className="text-right font-medium">
                {required && <span className="text-red-500">* </span>}
                {label}:
            </label>

            {type === 'select' ? (
                <select
                    name={name}
                    value={value}
                    onChange={onChange}
                    className={`border border-gray-300 p-1 ${width}`}
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
                    className={`border border-gray-300 p-1 ${width}`}
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
                    className={`border border-gray-300 p-1 ${width}`}
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
            <label className="text-right font-medium">
                {required && <span className="text-red-500">* </span>}
                {label}:
            </label>
            <div className="flex">
                <input
                    type="tel"
                    name={phoneName}
                    value={phoneValue}
                    onChange={onChange}
                    className="border border-gray-300 p-1 w-32"
                    required={required}
                />
                <span className="mx-2">Ext:</span>
                <input
                    type="text"
                    name={extName}
                    value={extValue}
                    onChange={onChange}
                    className="border border-gray-300 p-1 w-16"
                />
            </div>
        </>
    );
}
