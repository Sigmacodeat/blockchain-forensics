import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { UserRole } from '@/lib/auth';
import {
  Shield, AlertTriangle, CheckCircle, XCircle, Eye,
  Download, RefreshCw, Clock, Users, Database,
  FileText, Lock, Key, Activity, TrendingUp
} from 'lucide-react';
import { Button } from '@/components/ui/button';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface AuditEntry {
  timestamp: string;
  action: string;
  user_id: string | null;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, any>;
  ip_address: string | null;
  user_agent: string | null;
  severity: string;
}

interface ComplianceReport {
  generated_at: string;
  data_retention_periods: Record<string, number>;
  retention_compliance: {
    retention_violations: Record<string, any[]>;
    compliance_status: string;
  };
  pii_handling: {
    anonymization_enabled: boolean;
    pii_fields_configured: string[];
    encryption_enabled: boolean;
  };
  audit_trail_integrity: {
    total_entries_checked: number;
    verified_entries: number;
    tampered_entries: number;
    integrity_percentage: number;
  };
  gdpr_compliance: Record<string, any>;
  certifications: string[];
}

const SecurityComplianceDashboard: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [refreshInterval, setRefreshInterval] = useState<number>(30000); // 30 seconds
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // Audit Trail
  const { data: auditTrail, isLoading: auditLoading } = useQuery({
    queryKey: ['auditTrail'],
    queryFn: async () => {
      const response = await api.get(`/api/v1/security/audit-trail`, { params: { limit: 50 } });
      return response.data;
    },
    refetchInterval: refreshInterval
  });

  // Compliance Report
  const { data: complianceReport, isLoading: complianceLoading } = useQuery({
    queryKey: ['complianceReport'],
    queryFn: async () => {
      const response = await api.get(`/api/v1/security/compliance/report`);
      return response.data;
    },
    refetchInterval: refreshInterval
  });

  // Security Report
  const { data: securityReport, isLoading: securityLoading } = useQuery({
    queryKey: ['securityReport'],
    queryFn: async () => {
      const response = await api.get(`/api/v1/security/security/report`);
      return response.data;
    },
    refetchInterval: refreshInterval
  });

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getComplianceStatusColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'text-green-600';
      case 'minor_violations': return 'text-yellow-600';
      case 'major_violations': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <Shield className="h-8 w-8 text-green-600" />
                {t('sec.header.title', 'Security & Compliance Dashboard')}
              </h1>
              <p className="text-gray-600 mt-2">
                {t('sec.header.subtitle', 'Audit-Trails, GDPR-Compliance und Sicherheits-Monitoring')}
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-sm text-gray-500">
                {t('sec.header.last_refresh', 'Letzte Aktualisierung')}: {lastRefresh.toLocaleTimeString()}
              </div>
              <Button onClick={() => setLastRefresh(new Date())} className="flex items-center gap-2 bg-green-600 text-white hover:bg-green-700">
                <RefreshCw className="h-4 w-4" />
                {t('sec.actions.refresh', 'Aktualisieren')}
              </Button>
            </div>
          </div>
        </div>

        {/* Compliance Status Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-card p-6 rounded-lg shadow border border-border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{t('sec.cards.gdpr.title', 'GDPR Compliance')}</p>
                <p className={`text-2xl font-bold ${getComplianceStatusColor(complianceReport?.retention_compliance?.compliance_status)}`}>
                  {complianceReport?.retention_compliance?.compliance_status || t('sec.common.unknown', 'Unknown')}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${complianceReport?.retention_compliance?.compliance_status === 'compliant' ? 'bg-green-100' : 'bg-yellow-100'}`}>
                <Shield className={`h-6 w-6 ${complianceReport?.retention_compliance?.compliance_status === 'compliant' ? 'text-green-600' : 'text-yellow-600'}`} />
              </div>
            </div>
          </div>

          <div className="bg-card p-6 rounded-lg shadow border border-border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{t('sec.cards.audit_integrity.title', 'Audit Trail Integrity')}</p>
                <p className="text-2xl font-bold text-primary-600">
                  {complianceReport?.audit_trail_integrity?.integrity_percentage?.toFixed(1) || 'N/A'}%
                </p>
              </div>
              <div className="p-3 rounded-lg bg-primary-100">
                <CheckCircle className="h-6 w-6 text-primary-600" />
              </div>
            </div>
          </div>

          <div className="bg-card p-6 rounded-lg shadow border border-border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{t('sec.cards.security_incidents.title', 'Security Incidents')}</p>
                <p className="text-2xl font-bold text-orange-600">
                  {securityReport?.security_incidents || 0}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-orange-100">
                <AlertTriangle className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </div>

          <div className="bg-card p-6 rounded-lg shadow border border-border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">{t('sec.cards.failed_logins.title', 'Failed Login Attempts')}</p>
                <p className="text-2xl font-bold text-red-600">
                  {securityReport?.failed_login_attempts || 0}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-red-100">
                <XCircle className="h-6 w-6 text-red-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Recent Audit Trail */}
          <div className="bg-card p-6 rounded-lg shadow border border-border">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Activity className="h-5 w-5 text-purple-600" />
                {t('sec.audit.title', 'Aktuelle Audit-Trail-Einträge')}
              </h3>
              <button className="text-sm text-primary-600 hover:text-primary-800">
                {t('sec.audit.view_all', 'Alle anzeigen →')}
              </button>
            </div>

            {auditLoading ? (
              <div className="text-center py-8">{t('sec.audit.loading', 'Lade Audit-Trail...')}</div>
            ) : auditTrail && auditTrail.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {auditTrail.slice(0, 10).map((entry: AuditEntry, index: number) => (
                  <div key={index} className="flex items-start gap-3 p-3 bg-muted rounded border border-border">
                    <div className={`w-2 h-2 rounded-full mt-2 ${getSeverityColor(entry.severity)}`} />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900">{entry.action}</div>
                      <div className="text-xs text-gray-600">
                        {entry.resource_type} {entry.resource_id ? `• ${entry.resource_id.slice(0, 10)}...` : ''}
                      </div>
                      <div className="text-xs text-gray-500">
                        {formatTimestamp(entry.timestamp)}
                        {entry.user_id && ` • ${t('sec.audit.user', 'User')}: ${entry.user_id}`}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">{t('sec.audit.empty', 'Keine Audit-Trail-Einträge verfügbar')}</div>
            )}
          </div>

          {/* Compliance Status */}
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                {t('sec.compliance.title', 'GDPR Compliance Status')}
              </h3>
            </div>

            {complianceLoading ? (
              <div className="text-center py-8">{t('sec.compliance.loading', 'Lade Compliance-Status...')}</div>
            ) : complianceReport ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-gray-50 rounded">
                    <div className="text-lg font-bold text-gray-900">
                      {complianceReport.pii_handling.anonymization_enabled ? '✅' : '❌'}
                    </div>
                    <div className="text-sm text-gray-600">{t('sec.compliance.anonymization', 'Anonymisierung')}</div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded">
                    <div className="text-lg font-bold text-gray-900">
                      {complianceReport.pii_handling.encryption_enabled ? '✅' : '❌'}
                    </div>
                    <div className="text-sm text-gray-600">{t('sec.compliance.encryption', 'Verschlüsselung')}</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">{t('sec.compliance.right_to_erasure', 'Right to Erasure')}:</span>
                    <span className={`text-sm font-medium ${complianceReport.gdpr_compliance.right_to_erasure.implemented ? 'text-green-600' : 'text-red-600'}`}>
                      {complianceReport.gdpr_compliance.right_to_erasure.implemented ? t('sec.common.implemented', 'Implementiert') : t('sec.common.not_implemented', 'Nicht implementiert')}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">{t('sec.compliance.data_portability', 'Data Portability')}:</span>
                    <span className={`text-sm font-medium ${complianceReport.gdpr_compliance.data_portability.implemented ? 'text-green-600' : 'text-red-600'}`}>
                      {complianceReport.gdpr_compliance.data_portability.implemented ? t('sec.common.implemented', 'Implementiert') : t('sec.common.not_implemented', 'Nicht implementiert')}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">{t('sec.compliance.consent_management', 'Consent Management')}:</span>
                    <span className={`text-sm font-medium ${complianceReport.gdpr_compliance.consent_management.implemented ? 'text-green-600' : 'text-red-600'}`}>
                      {complianceReport.gdpr_compliance.consent_management.implemented ? t('sec.common.implemented', 'Implementiert') : t('sec.common.not_implemented', 'Nicht implementiert')}
                    </span>
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-200">
                  <div className="text-sm text-gray-600 mb-2">{t('sec.compliance.certifications', 'Zertifizierungen')}:</div>
                  <div className="flex flex-wrap gap-2">
                    {complianceReport.certifications?.map((cert: string, index: number) => (
                      <span key={index} className="px-2 py-1 bg-primary-100 text-primary-700 rounded text-xs">
                        {cert}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">{t('sec.compliance.empty', 'Keine Compliance-Daten verfügbar')}</div>
            )}
          </div>
        </div>

        {/* Data Retention & Security */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Data Retention */}
          <div className="bg-card p-6 rounded-lg shadow border border-border">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Database className="h-5 w-5 text-indigo-600" />
              {t('sec.retention.title', 'Data Retention Compliance')}
            </h3>

            {complianceReport?.data_retention_periods ? (
              <div className="space-y-3">
                {Object.entries(complianceReport.data_retention_periods).map(([dataType, days]: [string, any]) => (
                  <div key={dataType} className="flex justify-between items-center p-3 bg-muted rounded border border-border">
                    <span className="font-medium text-gray-900">{dataType.replace('_', ' ')}</span>
                    <span className="text-sm text-gray-600">{days} {t('sec.retention.days', 'Tage')}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">{t('sec.retention.empty', 'Keine Retention-Daten verfügbar')}</div>
            )}
          </div>

          {/* Security Overview */}
          <div className="bg-card p-6 rounded-lg shadow border border-border">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Lock className="h-5 w-5 text-red-600" />
              {t('sec.security.title', 'Security Overview')}
            </h3>

            {securityReport ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-red-50 rounded">
                    <div className="text-xl font-bold text-red-600">{securityReport.failed_login_attempts}</div>
                    <div className="text-sm text-red-800">{t('sec.security.failed_logins', 'Failed Logins')}</div>
                  </div>
                  <div className="text-center p-3 bg-orange-50 rounded">
                    <div className="text-xl font-bold text-orange-600">{securityReport.suspicious_activities}</div>
                    <div className="text-sm text-orange-800">{t('sec.security.suspicious_activities', 'Suspicious Activities')}</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">{t('sec.security.rate_limited_ips', 'Rate Limited IPs')}:</span>
                    <span className="font-semibold">{securityReport.rate_limited_ips}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">{t('sec.security.incidents', 'Security Incidents')}:</span>
                    <span className="font-semibold">{securityReport.security_incidents}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">{t('sec.security.compliance_status', 'Compliance Status')}:</span>
                    <span className={`font-semibold ${getComplianceStatusColor(securityReport.compliance_status)}`}>
                      {securityReport.compliance_status}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">{t('sec.security.empty', 'Keine Security-Daten verfügbar')}</div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 bg-card p-6 rounded-lg shadow border border-border">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Key className="h-5 w-5 text-purple-600" />
            {t('sec.quick_actions.title', 'Security & Compliance Actions')}
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <button className="flex flex-col items-center p-4 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors">
              <Download className="h-8 w-8 text-primary-600 mb-2" />
              <span className="text-sm font-medium text-primary-800">{t('sec.quick_actions.audit_export', 'Audit Export')}</span>
            </button>

            <button className="flex flex-col items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors">
              <CheckCircle className="h-8 w-8 text-green-600 mb-2" />
              <span className="text-sm font-medium text-green-800">{t('sec.quick_actions.compliance_report', 'Compliance Report')}</span>
            </button>

            <button className="flex flex-col items-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors">
              <Eye className="h-8 w-8 text-purple-600 mb-2" />
              <span className="text-sm font-medium text-purple-800">{t('sec.quick_actions.integrity_check', 'Integrity Check')}</span>
            </button>

            <button className="flex flex-col items-center p-4 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors">
              <Shield className="h-8 w-8 text-orange-600 mb-2" />
              <span className="text-sm font-medium text-orange-800">{t('sec.quick_actions.security_scan', 'Security Scan')}</span>
            </button>

            <button className="flex flex-col items-center p-4 bg-red-50 rounded-lg hover:bg-red-100 transition-colors">
              <AlertTriangle className="h-8 w-8 text-red-600 mb-2" />
              <span className="text-sm font-medium text-red-800">{t('sec.quick_actions.incident_report', 'Incident Report')}</span>
            </button>

            <button className="flex flex-col items-center p-4 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors">
              <FileText className="h-8 w-8 text-indigo-600 mb-2" />
              <span className="text-sm font-medium text-indigo-800">{t('sec.quick_actions.gdpr_status', 'GDPR Status')}</span>
            </button>
          </div>
        </div>

        {/* Retention Violations */}
        {complianceReport?.retention_compliance?.retention_violations && Object.keys(complianceReport.retention_compliance.retention_violations).length > 0 && (
          <div className="mt-8 bg-card p-6 rounded-lg shadow border border-border">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              {t('sec.retention.violations.title', 'Retention-Verletzungen')}
            </h3>

            <div className="space-y-4">
              {Object.entries(complianceReport.retention_compliance.retention_violations).map(([dataType, violations]: [string, any]) => (
                <div key={dataType} className="p-4 border border-red-200 rounded-lg bg-red-50">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-medium text-red-800">{dataType.replace('_', ' ')}</span>
                    <span className="text-sm text-red-600">{violations.length} {t('sec.retention.violations.count', 'Verletzungen')}</span>
                  </div>
                  <div className="space-y-1">
                    {violations.slice(0, 3).map((violation: any, index: number) => (
                      <div key={index} className="text-sm text-red-700">
                        • {violation.age_days} {t('sec.retention.violations.days_old', 'Tage alt')} • {formatTimestamp(violation.timestamp)}
                      </div>
                    ))}
                    {violations.length > 3 && (
                      <div className="text-sm text-red-600">... {t('sec.retention.violations.more', 'und')} {violations.length - 3} {t('sec.retention.violations.more_suffix', 'weitere')}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SecurityComplianceDashboard;
