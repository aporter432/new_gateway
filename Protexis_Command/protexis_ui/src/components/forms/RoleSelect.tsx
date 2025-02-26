'use client';

import { useState, useEffect } from 'react';

interface Role {
  role: string;
  description: string;
}

interface RoleSelectProps {
  onSelect: (role: string) => void;
  selectedRole?: string;
}

export function RoleSelect({ onSelect, selectedRole }: RoleSelectProps) {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchRoles() {
      try {
        const response = await fetch('/api/auth/roles');
        if (!response.ok) {
          throw new Error('Failed to fetch roles');
        }
        const data = await response.json();
        setRoles(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load roles');
      } finally {
        setLoading(false);
      }
    }

    fetchRoles();
  }, []);

  if (loading) return <div>Loading roles...</div>;
  if (error) return <div className="text-red-500">Error: {error}</div>;

  return (
    <div className="w-full">
      <select
        className="w-full p-2 border border-gray-300 rounded"
        value={selectedRole || ''}
        onChange={(e) => onSelect(e.target.value)}
      >
        <option value="">- permission role not assigned -</option>
        {roles.map((role) => (
          <option key={role.role} value={role.role}>
            {role.role} - {role.description}
          </option>
        ))}
      </select>
    </div>
  );
}
