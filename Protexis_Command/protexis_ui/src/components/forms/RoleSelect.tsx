'use client';

import { useEffect, useState } from 'react';

interface Role {
  role: string;
  description: string;
}

interface RoleSelectProps {
  onSelect: (role: string) => void;
  selectedRole?: string;
  currentUserRole?: string;
}

// Role hierarchy levels (1 is highest permissions, 7 is lowest)
const ROLE_LEVELS = {
  'protexis_administrator': 1,
  'accounting': 2,
  'protexis_site_admin': 3,
  'protexis_tech_admin': 4,
  'protexis_request_read': 5,
  'protexis_request_write': 6,
  'protexis_view': 7,
  // Include legacy roles for backward compatibility
  'admin': 1,
  'user': 7,
};

export function RoleSelect({ onSelect, selectedRole, currentUserRole }: RoleSelectProps) {
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

  // Filter roles based on current user's role level
  const filteredRoles = currentUserRole
    ? roles.filter(role => {
      const currentLevel = ROLE_LEVELS[currentUserRole as keyof typeof ROLE_LEVELS] || 999;
      const roleLevel = ROLE_LEVELS[role.role as keyof typeof ROLE_LEVELS] || 999;
      // Only show roles with higher level numbers (lower permissions) than current user
      return roleLevel > currentLevel;
    })
    : roles;

  return (
    <div className="w-full">
      <select
        className="w-full p-2 border border-gray-300 rounded"
        value={selectedRole || ''}
        onChange={(e) => onSelect(e.target.value)}
      >
        <option value="">- permission role not assigned -</option>
        {filteredRoles.map((role) => (
          <option key={role.role} value={role.role}>
            {role.role} - {role.description}
          </option>
        ))}
      </select>
    </div>
  );
}
