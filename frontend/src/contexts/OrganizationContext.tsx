import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

interface Organization {
  id: number;
  uuid: string;
  name: string;
  slug: string;
  owner_id: number;
  plan: string;
  status: string;
  role?: string;
  max_users: number;
  max_cases: number;
}

interface OrganizationContextType {
  currentOrg: Organization | null;
  organizations: Organization[];
  loading: boolean;
  error: string | null;
  switchOrganization: (orgId: number) => void;
  refreshOrganizations: () => Promise<void>;
  createOrganization: (name: string) => Promise<Organization | null>;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

export const useOrganization = () => {
  const context = useContext(OrganizationContext);
  if (!context) {
    throw new Error('useOrganization must be used within OrganizationProvider');
  }
  return context;
};

interface OrganizationProviderProps {
  children: ReactNode;
}

export const OrganizationProvider: React.FC<OrganizationProviderProps> = ({ children }) => {
  const [currentOrg, setCurrentOrg] = useState<Organization | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadOrganizations();
  }, []);

  const loadOrganizations = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('auth_token');
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await axios.get(
        `${import.meta.env.VITE_API_URL}/api/v1/orgs`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      const orgs = response.data.organizations || [];
      setOrganizations(orgs);

      // Set current org from localStorage or first org
      const savedOrgId = localStorage.getItem('current_org_id');
      if (savedOrgId) {
        const saved = orgs.find((o: Organization) => o.id === parseInt(savedOrgId));
        setCurrentOrg(saved || orgs[0] || null);
      } else {
        setCurrentOrg(orgs[0] || null);
      }

      setError(null);
    } catch (err) {
      console.error('Error loading organizations:', err);
      setError('Failed to load organizations');
    } finally {
      setLoading(false);
    }
  };

  const switchOrganization = (orgId: number) => {
    const org = organizations.find(o => o.id === orgId);
    if (org) {
      setCurrentOrg(org);
      localStorage.setItem('current_org_id', orgId.toString());
      // Trigger page reload to refresh data with new org context
      window.location.reload();
    }
  };

  const refreshOrganizations = async () => {
    await loadOrganizations();
  };

  const createOrganization = async (name: string): Promise<Organization | null> => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/api/v1/orgs`,
        { name },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      const newOrg = response.data;
      await refreshOrganizations();
      switchOrganization(newOrg.id);
      return newOrg;
    } catch (err) {
      console.error('Error creating organization:', err);
      return null;
    }
  };

  return (
    <OrganizationContext.Provider
      value={{
        currentOrg,
        organizations,
        loading,
        error,
        switchOrganization,
        refreshOrganizations,
        createOrganization,
      }}
    >
      {children}
    </OrganizationContext.Provider>
  );
};
