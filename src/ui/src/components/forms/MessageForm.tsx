'use client';

import { submitMessage } from '@/lib/api';
import { MessageSubmission, NetworkType } from '@/types/api';
import { useState } from 'react';

export function MessageForm() {
    const [networkType, setNetworkType] = useState<NetworkType>(NetworkType.OGX);
    const [destinationId, setDestinationId] = useState('');
    const [payload, setPayload] = useState('');
    const [status, setStatus] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');
    const [error, setError] = useState<string | null>(null);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setStatus('submitting');
        setError(null);

        try {
            const message: MessageSubmission = {
                networkType,
                destinationId,
                payload: JSON.parse(payload),
            };

            await submitMessage(message);
            setStatus('success');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to submit message');
            setStatus('error');
        }
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label className="block text-sm font-medium text-gray-700">
                    Network Type
                    <select
                        value={networkType}
                        onChange={(e) => setNetworkType(Number(e.target.value))}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                    >
                        <option value={NetworkType.OGX}>OGx</option>
                        <option value={NetworkType.ISATDATA_PRO}>IsatData Pro</option>
                    </select>
                </label>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700">
                    Destination ID
                    <input
                        type="text"
                        value={destinationId}
                        onChange={(e) => setDestinationId(e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                        required
                    />
                </label>
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700">
                    Payload (JSON)
                    <textarea
                        value={payload}
                        onChange={(e) => setPayload(e.target.value)}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                        rows={4}
                        required
                    />
                </label>
            </div>

            {error && (
                <div className="text-red-600 text-sm">{error}</div>
            )}

            <button
                type="submit"
                disabled={status === 'submitting'}
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
            >
                {status === 'submitting' ? 'Submitting...' : 'Submit Message'}
            </button>
        </form>
    );
} 