/**
 * VASP Compliance Dashboard
 * ==========================
 * 
 * Dashboard for VASP directory management and Travel Rule compliance.
 * Features:
 * - VASP Directory (1,500+ VASPs)
 * - Travel Rule evaluation
 * - VASP-to-VASP messaging
 * - Compliance statistics
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Building2,
  Shield,
  MessageSquare,
  Search,
  Plus,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  Globe,
  FileCheck,
} from 'lucide-react';

import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';

interface VASPStats {
  total_vasps: number;
  active_vasps: number;
  verified_vasps: number;
  by_type: Record<string, number>;
  by_jurisdiction: Record<string, number>;
  by_compliance_level: Record<string, number>;
  travel_rule_enabled: number;
  travel_rule_messages_total: number;
  travel_rule_messages_24h: number;
}

interface VASP {
  id: string;
  name: string;
  legal_name?: string;
  type: string;
  jurisdiction: string[];
  status: string;
  compliance_level: string;
  travel_rule_protocols: string[];
  supported_chains: string[];
  verified: boolean;
}

const VASPCompliance: React.FC = () => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'directory' | 'travel-rule' | 'screening'>('directory');
  const [searchQuery, setSearchQuery] = useState('');
  const [stats, setStats] = useState<VASPStats | null>(null);
  const [vasps, setVasps] = useState<VASP[]>([]);
  const [loading, setLoading] = useState(false);
  const [dirSearched, setDirSearched] = useState(false);
  // Directory filters
  const [dirFilters, setDirFilters] = useState({
    type: '',
    jurisdiction: '',
    status: '',
    compliance_level: '',
    blockchain: '',
    verified_only: false,
  });
  const [page, setPage] = useState(0);
  const [limit, setLimit] = useState(20);
  const [canNext, setCanNext] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [addSubmitting, setAddSubmitting] = useState(false);
  const [addForm, setAddForm] = useState({
    name: '',
    legal_name: '',
    type: '', // e.g. 'EXCHANGE'
    jurisdiction: '', // comma-separated e.g. 'US,DE'
    website: '',
    email: '',
    lei: '',
    registration_number: '',
    compliance_level: 'UNKNOWN', // e.g. 'FULL','PARTIAL','MINIMAL','UNKNOWN','NON_COMPLIANT'
    travel_rule_protocols: '', // comma-separated e.g. 'OPENVASP,TRISA'
    supported_chains: '', // comma-separated e.g. 'ethereum,bitcoin'
  });
  const [detailsId, setDetailsId] = useState<string | null>(null);
  const [detailsData, setDetailsData] = useState<any | null>(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const VASP_TYPES = ['EXCHANGE','CUSTODIAL_WALLET','OTC','BROKER','BANK','PSP','OTHER'];
  const VASP_STATUSES = ['ACTIVE','INACTIVE','SUSPENDED','PENDING','DELISTED'];
  const COMPLIANCE_LEVELS = ['FULL','PARTIAL','MINIMAL','UNKNOWN','NON_COMPLIANT'];
  const TR_PROTOCOLS = ['OPENVASP','TRISA','OTHER'];
  const TR_STATUSES = ['PENDING','SENT','ACCEPTED','REJECTED','FAILED'];
  const CHAIN_OPTIONS = ['ethereum','bitcoin','polygon','bsc','arbitrum','optimism'];

  // Travel Rule form state
  const [trForm, setTrForm] = useState({
    from_address: '',
    to_address: '',
    blockchain: 'ethereum',
    asset: 'ETH',
    amount: '',
    amount_usd: ''
  });
  const [trSubmitting, setTrSubmitting] = useState(false);
  const [trResult, setTrResult] = useState<any | null>(null);

  // Travel Rule messaging state
  const [msgForm, setMsgForm] = useState({
    originating_vasp_id: '',
    beneficiary_vasp_id: '',
    transaction_hash: '',
    blockchain: 'ethereum',
    asset: 'ETH',
    amount: '',
    amount_usd: '',
    protocol: 'OPENVASP',
    originator_json: '{"name":"","account_reference":""}',
    beneficiary_json: '{"name":"","account_reference":""}',
  });
  const [msgSubmitting, setMsgSubmitting] = useState(false);
  const [createdMessage, setCreatedMessage] = useState<any | null>(null);

  const [listFilters, setListFilters] = useState({
    originating_vasp_id: '',
    beneficiary_vasp_id: '',
    status: '',
    blockchain: ''
  });
  const [messages, setMessages] = useState<any[]>([]);
  const [listLoading, setListLoading] = useState(false);

  const [sendId, setSendId] = useState('');
  const [sendResult, setSendResult] = useState<any | null>(null);
  const [ackId, setAckId] = useState('');
  const [ackAccept, setAckAccept] = useState(true);
  const [ackResult, setAckResult] = useState<any | null>(null);
  const [msgDetailsId, setMsgDetailsId] = useState('');
  const [msgDetailsLoading, setMsgDetailsLoading] = useState(false);
  const [msgDetails, setMsgDetails] = useState<any | null>(null);

  // Screening form state
  const [screenForm, setScreenForm] = useState({
    address: '',
    blockchain: 'ethereum'
  });
  const [screenSubmitting, setScreenSubmitting] = useState(false);
  const [screenResult, setScreenResult] = useState<any | null>(null);

  // Multi-screening state (Sanctions multi-list)
  const [multiScreenForm, setMultiScreenForm] = useState({
    addresses: '', // comma-separated
    sources: 'ofac,un,eu,uk'
  });
  const [multiScreenSubmitting, setMultiScreenSubmitting] = useState(false);
  const [multiScreenResult, setMultiScreenResult] = useState<any[] | null>(null);

  // Simple validity flags
  const trValid = trForm.from_address && trForm.to_address && trForm.blockchain && trForm.asset && trForm.amount;
  const screenValid = screenForm.address && screenForm.blockchain;
  const msgValid = msgForm.originating_vasp_id && msgForm.beneficiary_vasp_id && msgForm.blockchain && msgForm.asset && msgForm.amount;
  const addValid = addForm.name && addForm.type && addForm.compliance_level;
  const multiScreenValid = multiScreenForm.addresses.trim().split(',').filter(Boolean).length > 0;

  // Render helpers (compact summaries)
  const renderTravelRuleSummary = (res: any) => {
    if (!res || typeof res !== 'object') return null;
    const requires = res.requires_travel_rule ?? res.requires ?? res.required;
    const threshold = res.threshold_usd ?? res.threshold ?? undefined;
    const reasons: string[] = res.reasons || res.notes || [];
    const parties = res.parties || {};
    return (
      <div className="mb-3 grid grid-cols-1 md:grid-cols-3 gap-3">
        <Card className="p-3 bg-card border border-border">
          <div className="flex items-center gap-2 text-sm">
            {requires ? <AlertTriangle className="h-4 w-4 text-red-600"/> : <CheckCircle className="h-4 w-4 text-green-600"/>}
            <span className="font-semibold">Travel Rule</span>
          </div>
          <div className="mt-1 text-sm text-slate-700 dark:text-slate-300">{requires ? 'Required' : 'Not required'}</div>
        </Card>
        <Card className="p-3 bg-card border border-border">
          <div className="flex items-center gap-2 text-sm">
            <Shield className="h-4 w-4 text-primary-600"/>
            <span className="font-semibold">Threshold (USD)</span>
          </div>
          <div className="mt-1 text-sm text-slate-700 dark:text-slate-300">{threshold !== undefined ? String(threshold) : 'n/a'}</div>
        </Card>
        <Card className="p-3 bg-card border border-border">
          <div className="flex items-center gap-2 text-sm">
            <Building2 className="h-4 w-4 text-slate-600"/>
            <span className="font-semibold">Parties</span>
          </div>
          <div className="mt-1 text-xs text-slate-700 dark:text-slate-300">
            {Object.keys(parties).length ? Object.keys(parties).join(', ') : 'n/a'}
          </div>
        </Card>
        {Array.isArray(reasons) && reasons.length > 0 && (
          <div className="md:col-span-3">
            <Card className="p-3 bg-card border border-border">
              <div className="text-sm font-semibold mb-1">Reasons</div>
              <ul className="text-xs list-disc pl-5 text-slate-700 dark:text-slate-300">
                {reasons.slice(0,5).map((r, i)=> (<li key={i}>{String(r)}</li>))}
              </ul>
            </Card>
          </div>
        )}
      </div>
    );
  };

  const multiScreenAddresses = async () => {
    setMultiScreenSubmitting(true);
    setMultiScreenResult(null);
    try {
      const addrs = multiScreenForm.addresses.split(',').map(a => a.trim()).filter(Boolean);
      const sources = multiScreenForm.sources.split(',').map(s => s.trim()).filter(Boolean);
      const payload = { addresses: addrs, sources };
      const res = await fetch('/api/v1/sanctions/screen/multi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) setMultiScreenResult(await res.json()); else setMultiScreenResult([{ error: await res.text() } as any]);
    } catch (e: any) {
      setMultiScreenResult([{ error: e?.message || 'Failed to multi-screen' } as any]);
    } finally {
      setMultiScreenSubmitting(false);
    }
  };

  const renderScreeningSummary = (res: any) => {
    if (!res || typeof res !== 'object') return null;
    const belongs = res.belongs_to_vasp ?? res.is_vasp ?? false;
    const vaspName = res.vasp_name || res.vasp || res.name;
    const compliance = res.compliance_level || res.level || 'unknown';
    return (
      <div className="mb-3 grid grid-cols-1 md:grid-cols-3 gap-3">
        <Card className="p-3 bg-card border border-border">
          <div className="flex items-center gap-2 text-sm">
            {belongs ? <CheckCircle className="h-4 w-4 text-green-600"/> : <AlertTriangle className="h-4 w-4 text-yellow-600"/>}
            <span className="font-semibold">Association</span>
          </div>
          <div className="mt-1 text-sm text-slate-700 dark:text-slate-300">{belongs ? 'Known VASP' : 'Unknown'}</div>
        </Card>
        <Card className="p-3 bg-card border border-border">
          <div className="flex items-center gap-2 text-sm">
            <Building2 className="h-4 w-4 text-slate-600"/>
            <span className="font-semibold">VASP</span>
          </div>
          <div className="mt-1 text-sm text-slate-700 dark:text-slate-300">{vaspName || 'n/a'}</div>
        </Card>
        <Card className="p-3 bg-card border border-border">
          <div className="flex items-center gap-2 text-sm">
            <Shield className="h-4 w-4 text-primary-600"/>
            <span className="font-semibold">Compliance</span>
          </div>
          <div className="mt-1 text-sm text-slate-700 dark:text-slate-300 capitalize">{String(compliance).replace('_',' ')}</div>
        </Card>
      </div>
    );
  };

  const renderMessageSummary = (msg: any) => {
    if (!msg || typeof msg !== 'object') return null;
    const status = msg.status || msg.tr_status || 'UNKNOWN';
    const chain = msg.blockchain || 'n/a';
    const asset = msg.asset || 'n/a';
    const amount = msg.amount !== undefined ? msg.amount : 'n/a';
    const from = msg.originating_vasp_id || msg.sender || 'n/a';
    const to = msg.beneficiary_vasp_id || msg.receiver || 'n/a';
    return (
      <div className="mb-3 grid grid-cols-1 md:grid-cols-3 gap-3">
        <Card className="p-3 bg-card border border-border">
          <div className="text-sm font-semibold">Status</div>
          <div className="mt-1 text-sm text-slate-700 dark:text-slate-300">{String(status)}</div>
        </Card>
        <Card className="p-3 bg-card border border-border">
          <div className="text-sm font-semibold">Asset</div>
          <div className="mt-1 text-sm text-slate-700 dark:text-slate-300">{asset} on {chain}</div>
        </Card>
        <Card className="p-3 bg-card border border-border">
          <div className="text-sm font-semibold">Amount</div>
          <div className="mt-1 text-sm text-slate-700 dark:text-slate-300">{String(amount)}</div>
        </Card>
        <div className="md:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-3">
          <Card className="p-3 bg-card border border-border">
            <div className="text-sm font-semibold">Originating VASP</div>
            <div className="mt-1 text-sm text-slate-700 dark:text-slate-300">{from}</div>
          </Card>
          <Card className="p-3 bg-card border border-border">
            <div className="text-sm font-semibold">Beneficiary VASP</div>
            <div className="mt-1 text-sm text-slate-700 dark:text-slate-300">{to}</div>
          </Card>
        </div>
      </div>
    );
  };

  // Load statistics
  React.useEffect(() => {
    loadStatistics();
    // Initialize filters from URL once
    try {
      const usp = new URLSearchParams(window.location.search);
      const nameQ = usp.get('name') || '';
      const typeQ = usp.get('type') || '';
      const jurisQ = usp.get('jurisdiction') || '';
      const statusQ = usp.get('status') || '';
      const compQ = usp.get('compliance_level') || '';
      const chainQ = usp.get('blockchain') || '';
      const verifiedQ = (usp.get('verified_only') || '').toLowerCase() === 'true';
      const skipQ = parseInt(usp.get('skip') || '0', 10);
      const limitQ = parseInt(usp.get('limit') || '20', 10);
      if (!Number.isNaN(skipQ)) setPage(Math.max(0, Math.floor(skipQ / Math.max(1, limitQ))));
      if (!Number.isNaN(limitQ) && limitQ > 0) setLimit(limitQ);
      if (nameQ || typeQ || jurisQ || statusQ || compQ || chainQ || verifiedQ || skipQ || limitQ) {
        setSearchQuery(nameQ);
        setDirFilters({
          type: typeQ,
          jurisdiction: jurisQ,
          status: statusQ,
          compliance_level: compQ,
          blockchain: chainQ,
          verified_only: verifiedQ,
        });
      }
    } catch {}
    // Auto-load directory once on mount
    setTimeout(() => { searchVASPs(); }, 0);
  }, []);

  const loadStatistics = async () => {
    try {
      const response = await fetch('/api/v1/vasp/statistics');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to load statistics:', error);
    }
  };

  const openDetails = async (id: string) => {
    setDetailsId(id);
    setDetailsData(null);
    setDetailsLoading(true);
    try {
      const res = await fetch(`/api/v1/vasp/directory/${encodeURIComponent(id)}`);
      if (res.ok) setDetailsData(await res.json()); else setDetailsData({ error: await res.text() });
    } catch (e: any) {
      setDetailsData({ error: e?.message || 'Failed to load details' });
    } finally {
      setDetailsLoading(false);
    }
  };

  const addVASP = async () => {
    setAddSubmitting(true);
    try {
      const payload = {
        name: addForm.name,
        legal_name: addForm.legal_name || undefined,
        type: addForm.type || undefined,
        jurisdiction: addForm.jurisdiction ? addForm.jurisdiction.split(',').map(s=>s.trim()).filter(Boolean) : [],
        website: addForm.website || undefined,
        email: addForm.email || undefined,
        lei: addForm.lei || undefined,
        registration_number: addForm.registration_number || undefined,
        compliance_level: addForm.compliance_level || 'UNKNOWN',
        travel_rule_protocols: addForm.travel_rule_protocols ? addForm.travel_rule_protocols.split(',').map(s=>s.trim()).filter(Boolean) : [],
        supported_chains: addForm.supported_chains ? addForm.supported_chains.split(',').map(s=>s.trim()).filter(Boolean) : [],
      } as any;
      const res = await fetch('/api/v1/vasp/directory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        setShowAdd(false);
        setAddForm({
          name: '', legal_name: '', type: '', jurisdiction: '', website: '', email: '', lei: '', registration_number: '',
          compliance_level: 'UNKNOWN', travel_rule_protocols: '', supported_chains: ''
        });
        // refresh list if visible
        if (activeTab === 'directory') await searchVASPs();
      } else {
        const err = await res.text();
        alert(`Failed to add VASP: ${err}`);
      }
    } catch (e: any) {
      alert(`Failed to add VASP: ${e?.message || 'Unknown error'}`);
    } finally {
      setAddSubmitting(false);
    }
  };

  const createTravelRuleMessage = async () => {
    setMsgSubmitting(true);
    setCreatedMessage(null);
    try {
      let originator: any = {};
      let beneficiary: any = {};
      try { originator = JSON.parse(msgForm.originator_json || '{}'); } catch {}
      try { beneficiary = JSON.parse(msgForm.beneficiary_json || '{}'); } catch {}
      const payload = {
        originating_vasp_id: msgForm.originating_vasp_id,
        beneficiary_vasp_id: msgForm.beneficiary_vasp_id,
        transaction_hash: msgForm.transaction_hash || undefined,
        blockchain: msgForm.blockchain,
        asset: msgForm.asset,
        amount: Number(msgForm.amount || 0),
        amount_usd: msgForm.amount_usd ? Number(msgForm.amount_usd) : undefined,
        protocol: msgForm.protocol,
        originator,
        beneficiary,
      };
      const res = await fetch('/api/v1/vasp/travel-rule/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        setCreatedMessage(data);
      } else {
        setCreatedMessage({ error: await res.text() });
      }
    } catch (e: any) {
      setCreatedMessage({ error: e?.message || 'Failed to create message' });
    } finally {
      setMsgSubmitting(false);
    }
  };

  const listTravelRuleMessages = async () => {
    setListLoading(true);
    setMessages([]);
    try {
      const p = new URLSearchParams();
      if (listFilters.originating_vasp_id) p.append('originating_vasp_id', listFilters.originating_vasp_id);
      if (listFilters.beneficiary_vasp_id) p.append('beneficiary_vasp_id', listFilters.beneficiary_vasp_id);
      if (listFilters.status) p.append('status', listFilters.status);
      if (listFilters.blockchain) p.append('blockchain', listFilters.blockchain);
      const res = await fetch(`/api/v1/vasp/travel-rule/messages?${p.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data);
      } else {
        setMessages([{ error: await res.text() } as any]);
      }
    } catch (e: any) {
      setMessages([{ error: e?.message || 'Failed to list messages' } as any]);
    } finally {
      setListLoading(false);
    }
  };

  const sendTravelRuleMessage = async () => {
    setSendResult(null);
    try {
      const res = await fetch(`/api/v1/vasp/travel-rule/messages/${encodeURIComponent(sendId)}/send`, { method: 'POST' });
      if (res.ok) setSendResult(await res.json()); else setSendResult({ error: await res.text() });
    } catch (e: any) { setSendResult({ error: e?.message || 'Failed to send message' }); }
  };

  const acknowledgeTravelRuleMessage = async () => {
    setAckResult(null);
    try {
      const res = await fetch(`/api/v1/vasp/travel-rule/messages/${encodeURIComponent(ackId)}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ accept: !!ackAccept })
      });
      if (res.ok) setAckResult(await res.json()); else setAckResult({ error: await res.text() });
    } catch (e: any) { setAckResult({ error: e?.message || 'Failed to acknowledge message' }); }
  };

  const getTravelRuleMessageDetails = async () => {
    setMsgDetails(null);
    setMsgDetailsLoading(true);
    try {
      const res = await fetch(`/api/v1/vasp/travel-rule/messages/${encodeURIComponent(msgDetailsId)}`);
      if (res.ok) setMsgDetails(await res.json()); else setMsgDetails({ error: await res.text() });
    } catch (e: any) { setMsgDetails({ error: e?.message || 'Failed to get message' }); }
    finally { setMsgDetailsLoading(false); }
  };

  const evaluateTravelRule = async () => {
    setTrSubmitting(true);
    setTrResult(null);
    try {
      const payload = {
        from_address: trForm.from_address,
        to_address: trForm.to_address,
        blockchain: trForm.blockchain,
        asset: trForm.asset,
        amount: Number(trForm.amount || 0),
        amount_usd: trForm.amount_usd ? Number(trForm.amount_usd) : undefined,
      };
      const res = await fetch('/api/v1/vasp/travel-rule/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        setTrResult(data);
      } else {
        setTrResult({ error: await res.text() });
      }
    } catch (e: any) {
      setTrResult({ error: e?.message || 'Failed to evaluate Travel Rule' });
    } finally {
      setTrSubmitting(false);
    }
  };

  const screenAddress = async () => {
    setScreenSubmitting(true);
    setScreenResult(null);
    try {
      const payload = {
        address: screenForm.address,
        blockchain: screenForm.blockchain,
      };
      const res = await fetch('/api/v1/vasp/screen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const data = await res.json();
        setScreenResult(data);
      } else {
        setScreenResult({ error: await res.text() });
      }
    } catch (e: any) {
      setScreenResult({ error: e?.message || 'Failed to screen address' });
    } finally {
      setScreenSubmitting(false);
    }
  };

  const searchVASPs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('name', searchQuery);
      if (dirFilters.type) params.append('type', dirFilters.type);
      if (dirFilters.jurisdiction) params.append('jurisdiction', dirFilters.jurisdiction);
      if (dirFilters.status) params.append('status', dirFilters.status);
      if (dirFilters.compliance_level) params.append('compliance_level', dirFilters.compliance_level);
      if (dirFilters.blockchain) params.append('blockchain', dirFilters.blockchain);
      if (dirFilters.verified_only) params.append('verified_only', 'true');
      const skip = Math.max(0, page) * Math.max(1, limit);
      params.append('skip', String(skip));
      params.append('limit', String(limit));
      
      const response = await fetch(`/api/v1/vasp/directory?${params}`);
      if (response.ok) {
        const data = await response.json();
        setVasps(data);
        setDirSearched(true);
        setCanNext(Array.isArray(data) && data.length === limit);
      }
      // Push filters into URL for deep links
      const qs = params.toString();
      const newUrl = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
      window.history.replaceState(null, '', newUrl);
    } catch (error) {
      console.error('Failed to search VASPs:', error);
    } finally {
      setLoading(false);
    }
  };

  const getComplianceBadge = (level: string) => {
    const config: Record<string, { color: string; icon: React.ReactNode }> = {
      full: { color: 'green', icon: <CheckCircle className="h-3 w-3" /> },
      partial: { color: 'yellow', icon: <AlertTriangle className="h-3 w-3" /> },
      minimal: { color: 'orange', icon: <AlertTriangle className="h-3 w-3" /> },
      unknown: { color: 'gray', icon: <AlertTriangle className="h-3 w-3" /> },
      non_compliant: { color: 'red', icon: <AlertTriangle className="h-3 w-3" /> },
    };
    
    const { color, icon } = config[level] || config.unknown;
    
    return (
      <Badge variant={color as any} className="flex items-center gap-1">
        {icon}
        <span className="capitalize">{level.replace('_', ' ')}</span>
      </Badge>
    );
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
              <Shield className="h-8 w-8 text-primary-600" />
              VASP Compliance
            </h1>
            <p className="text-slate-600 dark:text-slate-400 mt-1">
              Travel Rule & VASP Directory Management
            </p>
          </div>
          
          <Button onClick={()=>setShowAdd(true)} className="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white">
            <Plus className="h-4 w-4" />
            Add VASP
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-6 bg-card border border-border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Total VASPs</p>
                <p className="text-3xl font-bold text-slate-900 dark:text-white mt-1">
                  {stats.total_vasps.toLocaleString()}
                </p>
              </div>
              <Building2 className="h-10 w-10 text-primary-600 opacity-50" />
            </div>
            <div className="mt-4 flex items-center gap-2 text-sm">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span className="text-slate-600 dark:text-slate-400">
                {stats.verified_vasps} verified
              </span>
            </div>
          </Card>

          <Card className="p-6 bg-card border border-border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Active VASPs</p>
                <p className="text-3xl font-bold text-slate-900 dark:text-white mt-1">
                  {stats.active_vasps.toLocaleString()}
                </p>
              </div>
              <TrendingUp className="h-10 w-10 text-green-600 opacity-50" />
            </div>
            <div className="mt-4 flex items-center gap-2 text-sm">
              <span className="text-slate-600 dark:text-slate-400">
                {((stats.active_vasps / stats.total_vasps) * 100).toFixed(1)}% active
              </span>
            </div>
          </Card>

          <Card className="p-6 bg-card border border-border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Travel Rule</p>
                <p className="text-3xl font-bold text-slate-900 dark:text-white mt-1">
                  {stats.travel_rule_enabled.toLocaleString()}
                </p>
              </div>
              <MessageSquare className="h-10 w-10 text-blue-600 opacity-50" />
            </div>
            <div className="mt-4 flex items-center gap-2 text-sm">
              <span className="text-slate-600 dark:text-slate-400">
                {stats.travel_rule_messages_24h} messages (24h)
              </span>
            </div>
          </Card>

          <Card className="p-6 bg-card border border-border">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400">Jurisdictions</p>
                <p className="text-3xl font-bold text-slate-900 dark:text-white mt-1">
                  {Object.keys(stats.by_jurisdiction).length}
                </p>
              </div>
              <Globe className="h-10 w-10 text-purple-600 opacity-50" />
            </div>
            <div className="mt-4 flex items-center gap-2 text-sm">
              <span className="text-slate-600 dark:text-slate-400">
                Global coverage
              </span>
            </div>
          </Card>
        </div>
      )}

      {/* Screening Tab */}
      {activeTab === 'screening' && (
        <div>
          <Card className="p-6 bg-white dark:bg-slate-800 mb-6">
            <div className="text-center mb-6">
              <Search className="h-16 w-16 text-primary-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Address Screening</h3>
              <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
                Screen single or multiple addresses against sanctions lists (OFAC, UN, EU, UK).
              </p>
            </div>

            {/* Single address screening (existing) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <Input placeholder="Address" value={screenForm.address} onChange={(e)=>setScreenForm({...screenForm, address: e.target.value})} />
              <div>
                <label className="block text-xs text-slate-500 mb-1">Blockchain</label>
                <select className="w-full p-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200" value={screenForm.blockchain} onChange={(e)=>setScreenForm({...screenForm, blockchain: e.target.value})}>
                  {CHAIN_OPTIONS.map(c=> (<option key={c} value={c}>{c}</option>))}
                </select>
              </div>
              <div className="flex items-end">
                <Button onClick={screenAddress} disabled={screenSubmitting || !screenValid} className="bg-primary-600 hover:bg-primary-700 text-white disabled:opacity-70 w-full">
                  {screenSubmitting ? 'Screening…' : 'Screen Address'}
                </Button>
              </div>
            </div>
            {screenResult && (
              <div className="mt-4 p-4 rounded-md bg-slate-50 dark:bg-slate-900/40 overflow-auto">
                <pre className="text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap break-words">{JSON.stringify(screenResult, null, 2)}</pre>
              </div>
            )}
          </Card>

          {/* Multi-screening via sanctions */}
          <Card className="p-6 bg-white dark:bg-slate-800">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Multi Screening (Sanctions)</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <textarea className="w-full min-h-[120px] p-3 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200 text-sm" placeholder="Addresses (comma-separated)" value={multiScreenForm.addresses} onChange={(e)=>setMultiScreenForm({...multiScreenForm, addresses: e.target.value})} />
              <Input placeholder="Sources (comma-separated e.g. ofac,un,eu,uk)" value={multiScreenForm.sources} onChange={(e)=>setMultiScreenForm({...multiScreenForm, sources: e.target.value})} />
            </div>
            <div className="mt-4 flex items-center">
              <Button onClick={multiScreenAddresses} disabled={multiScreenSubmitting || !multiScreenValid} className="bg-primary-600 hover:bg-primary-700 text-white disabled:opacity-70">
                {multiScreenSubmitting ? 'Screening…' : 'Screen Multiple'}
              </Button>
            </div>
            {multiScreenResult && (
              <div className="mt-4 p-4 rounded-md bg-slate-50 dark:bg-slate-900/40 overflow-auto">
                <pre className="text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap break-words">{JSON.stringify(multiScreenResult, null, 2)}</pre>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Add VASP Modal */}
      {showAdd && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-2xl bg-white dark:bg-slate-900 rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4">Add VASP</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input placeholder="Name" value={addForm.name} onChange={(e)=>setAddForm({...addForm, name: e.target.value})} />
              <Input placeholder="Legal Name (optional)" value={addForm.legal_name} onChange={(e)=>setAddForm({...addForm, legal_name: e.target.value})} />
              <div>
                <label className="block text-xs text-slate-500 mb-1">Type</label>
                <select className="w-full p-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200"
                        value={addForm.type}
                        onChange={(e)=>setAddForm({...addForm, type: e.target.value})}>
                  <option value="">Select Type</option>
                  {VASP_TYPES.map(v=> (<option key={v} value={v}>{v}</option>))}
                </select>
              </div>
              <Input placeholder="Jurisdiction (comma-separated e.g. US,DE)" value={addForm.jurisdiction} onChange={(e)=>setAddForm({...addForm, jurisdiction: e.target.value})} />
              <Input placeholder="Website" value={addForm.website} onChange={(e)=>setAddForm({...addForm, website: e.target.value})} />
              <Input placeholder="Email" value={addForm.email} onChange={(e)=>setAddForm({...addForm, email: e.target.value})} />
              <Input placeholder="LEI (optional)" value={addForm.lei} onChange={(e)=>setAddForm({...addForm, lei: e.target.value})} />
              <Input placeholder="Registration Number (optional)" value={addForm.registration_number} onChange={(e)=>setAddForm({...addForm, registration_number: e.target.value})} />
              <div>
                <label className="block text-xs text-slate-500 mb-1">Compliance Level</label>
                <select className="w-full p-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200"
                        value={addForm.compliance_level}
                        onChange={(e)=>setAddForm({...addForm, compliance_level: e.target.value})}>
                  {COMPLIANCE_LEVELS.map(v=> (<option key={v} value={v}>{v}</option>))}
                </select>
              </div>
              <Input placeholder="Travel Rule Protocols (comma-separated e.g. OPENVASP,TRISA)" value={addForm.travel_rule_protocols} onChange={(e)=>setAddForm({...addForm, travel_rule_protocols: e.target.value})} />
              <Input placeholder="Supported Chains (comma-separated e.g. ethereum,bitcoin)" value={addForm.supported_chains} onChange={(e)=>setAddForm({...addForm, supported_chains: e.target.value})} />
            </div>
            <div className="mt-2 text-xs text-slate-500">
              {!addValid && 'Please fill Name, Type and Compliance Level.'}
            </div>
            <div className="mt-4 flex items-center justify-end gap-2">
              <Button variant="outline" onClick={()=>setShowAdd(false)}>Cancel</Button>
              <Button onClick={addVASP} disabled={addSubmitting || !addValid} className="bg-primary-600 hover:bg-primary-700 text-white disabled:opacity-70">{addSubmitting ? 'Adding…' : 'Add VASP'}</Button>
            </div>
          </div>
        </div>
      )}

      {/* VASP Details Modal */}
      {detailsId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-3xl bg-white dark:bg-slate-900 rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">VASP Details</h3>
              <Button variant="outline" onClick={()=>{setDetailsId(null); setDetailsData(null);}}>Close</Button>
            </div>
            <div className="min-h-[120px] p-3 rounded-md bg-slate-50 dark:bg-slate-900/40 overflow-auto">
              {detailsLoading ? (
                <p className="text-sm text-slate-600 dark:text-slate-400">Loading…</p>
              ) : (
                <pre className="text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap break-words">{JSON.stringify(detailsData, null, 2)}</pre>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex gap-2 border-b border-slate-200 dark:border-slate-700">
          <button
            onClick={() => setActiveTab('directory')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'directory'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <div className="flex items-center gap-2">
              <Building2 className="h-4 w-4" />
              VASP Directory
            </div>
          </button>
          
          <button
            onClick={() => setActiveTab('travel-rule')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'travel-rule'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <div className="flex items-center gap-2">
              <FileCheck className="h-4 w-4" />
              Travel Rule
            </div>
          </button>
          
          <button
            onClick={() => setActiveTab('screening')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'screening'
                ? 'text-primary-600 border-b-2 border-primary-600'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <div className="flex items-center gap-2">
              <Search className="h-4 w-4" />
              Address Screening
            </div>
          </button>
        </div>
      </div>

      {/* VASP Directory Tab */}
      {activeTab === 'directory' && (
        <div className="max-w-7xl mx-auto">
          <Card className="p-6 bg-white dark:bg-slate-800 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <Input placeholder="Search by name" value={searchQuery} onChange={(e)=>setSearchQuery(e.target.value)} onKeyPress={(e)=> e.key==='Enter' && searchVASPs()} />
              <div>
                <label className="block text-xs text-slate-500 mb-1">Type</label>
                <select className="w-full p-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200"
                        value={dirFilters.type}
                        onChange={(e)=>setDirFilters({...dirFilters, type: e.target.value})}>
                  <option value="">Any</option>
                  {VASP_TYPES.map(v=> (<option key={v} value={v}>{v}</option>))}
                </select>
              </div>
              <Input placeholder="Jurisdiction (e.g. US)" value={dirFilters.jurisdiction} onChange={(e)=>setDirFilters({...dirFilters, jurisdiction: e.target.value})} />
              <div>
                <label className="block text-xs text-slate-500 mb-1">Status</label>
                <select className="w-full p-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200"
                        value={dirFilters.status}
                        onChange={(e)=>setDirFilters({...dirFilters, status: e.target.value})}>
                  <option value="">Any</option>
                  {VASP_STATUSES.map(v=> (<option key={v} value={v}>{v}</option>))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">Compliance Level</label>
                <select className="w-full p-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200"
                        value={dirFilters.compliance_level}
                        onChange={(e)=>setDirFilters({...dirFilters, compliance_level: e.target.value})}>
                  <option value="">Any</option>
                  {COMPLIANCE_LEVELS.map(v=> (<option key={v} value={v}>{v}</option>))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">Blockchain</label>
                <select className="w-full p-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200" value={dirFilters.blockchain} onChange={(e)=>setDirFilters({...dirFilters, blockchain: e.target.value})}>
                  <option value="">Any</option>
                  {CHAIN_OPTIONS.map(c=> (<option key={c} value={c}>{c}</option>))}
                </select>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                <input type="checkbox" checked={dirFilters.verified_only} onChange={(e)=>setDirFilters({...dirFilters, verified_only: e.target.checked})} />
                Verified only
              </label>
              <div className="flex items-center gap-2">
                <Button
                  onClick={searchVASPs}
                  disabled={loading}
                  aria-busy={loading}
                  className="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white disabled:opacity-70"
                >
                  <Search className="h-4 w-4" />
                  {loading ? 'Searching…' : 'Search'}
                </Button>
                <Button variant="outline" onClick={()=>{setDirFilters({type:'',jurisdiction:'',status:'',compliance_level:'',blockchain:'',verified_only:false}); setSearchQuery(''); setPage(0);}}>Reset</Button>
              </div>
            </div>
            <div className="mt-4 flex items-center justify-between gap-2 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-slate-600 dark:text-slate-400">Rows per page</span>
                <select className="p-1 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200"
                        value={limit}
                        onChange={(e)=>{ setLimit(parseInt(e.target.value,10)||20); setPage(0); }}>
                  {[10,20,50,100].map(n=> (<option key={n} value={n}>{n}</option>))}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" disabled={page<=0 || loading} onClick={()=>{ setPage(p=>Math.max(0, p-1)); setTimeout(searchVASPs, 0); }}>Prev</Button>
                <span className="text-slate-600 dark:text-slate-400">Page {page+1}</span>
                <Button variant="outline" disabled={!canNext || loading} onClick={()=>{ setPage(p=>p+1); setTimeout(searchVASPs, 0); }}>Next</Button>
              </div>
            </div>
          </Card>

          {/* VASP List */}
          <div className="grid gap-4">
            {vasps.map((vasp) => (
              <Card key={vasp.id} className="p-6 bg-white dark:bg-slate-800 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                        {vasp.name}
                      </h3>
                      {vasp.verified && (
                        <Badge variant="success" className="flex items-center gap-1">
                          <CheckCircle className="h-3 w-3" />
                          Verified
                        </Badge>
                      )}
                    </div>
                    
                    {vasp.legal_name && (
                      <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                        {vasp.legal_name}
                      </p>
                    )}
                    
                    <div className="flex flex-wrap gap-2 mb-3">
                      <Badge variant="secondary" className="capitalize bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                        {vasp.type.replace('_', ' ')}
                      </Badge>
                      
                      {vasp.jurisdiction.map((j) => (
                        <Badge key={j} variant="secondary" className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                          {j}
                        </Badge>
                      ))}
                      
                      {getComplianceBadge(vasp.compliance_level)}
                    </div>
                    
                    <div className="text-sm text-slate-600 dark:text-slate-400">
                      <p className="mb-1">
                        <strong>Chains:</strong> {vasp.supported_chains.join(', ') || 'None'}
                      </p>
                      <p>
                        <strong>Travel Rule:</strong>{' '}
                        {vasp.travel_rule_protocols.length > 0
                          ? vasp.travel_rule_protocols.map(p => p.toUpperCase()).join(', ')
                          : 'Not supported'}
                      </p>
                    </div>
                  </div>
                  
                  <Button variant="outline" size="sm" onClick={()=>openDetails(vasp.id)}>View Details</Button>
                </div>
              </Card>
            ))}
            
            {vasps.length === 0 && !loading && (
              <Card className="p-12 bg-white dark:bg-slate-800 text-center">
                <Building2 className="h-16 w-16 text-slate-400 mx-auto mb-4" />
                <p className="text-slate-600 dark:text-slate-400">
                  No VASPs found. Try searching or add a new VASP.
                </p>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Travel Rule Tab */}
      {activeTab === 'travel-rule' && (
        <div className="max-w-7xl mx-auto">
          <Card className="p-6 bg-white dark:bg-slate-800 mb-6">
            <div className="text-center mb-6">
              <MessageSquare className="h-16 w-16 text-primary-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Travel Rule Evaluation</h3>
              <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
                Evaluate transactions for Travel Rule compliance (OpenVASP, TRISA, ...)
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input placeholder="From Address" value={trForm.from_address} onChange={(e)=>setTrForm({...trForm, from_address: e.target.value})} />
              <Input placeholder="To Address" value={trForm.to_address} onChange={(e)=>setTrForm({...trForm, to_address: e.target.value})} />
              <div>
                <label className="block text-xs text-slate-500 mb-1">Blockchain</label>
                <select className="w-full p-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200" value={trForm.blockchain} onChange={(e)=>setTrForm({...trForm, blockchain: e.target.value})}>
                  {CHAIN_OPTIONS.map(c=> (<option key={c} value={c}>{c}</option>))}
                </select>
              </div>
              <Input placeholder="Asset (e.g. ETH)" value={trForm.asset} onChange={(e)=>setTrForm({...trForm, asset: e.target.value})} />
              <Input placeholder="Amount" value={trForm.amount} onChange={(e)=>setTrForm({...trForm, amount: e.target.value})} />
              <Input placeholder="Amount USD (optional)" value={trForm.amount_usd} onChange={(e)=>setTrForm({...trForm, amount_usd: e.target.value})} />
            </div>
            <div className="mt-4 flex items-center justify-center">
              <Button onClick={evaluateTravelRule} disabled={trSubmitting || !trValid} className="bg-primary-600 hover:bg-primary-700 text-white disabled:opacity-70">
                {trSubmitting ? 'Evaluating…' : 'Evaluate Transaction'}
              </Button>
            </div>
            {!trValid && (
              <p className="mt-2 text-xs text-slate-500">Please fill From/To/Blockchain/Asset/Amount.</p>
            )}
            {trResult && (
              <div className="mt-6 p-4 rounded-md bg-slate-50 dark:bg-slate-900/40 text-left overflow-auto">
                {renderTravelRuleSummary(trResult)}
                <pre className="text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap break-words">{JSON.stringify(trResult, null, 2)}</pre>
              </div>
            )}
          </Card>

          {/* Create Travel Rule Message */}
          <Card className="p-6 bg-white dark:bg-slate-800 mb-6">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Create Travel Rule Message</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input placeholder="Originating VASP ID" value={msgForm.originating_vasp_id} onChange={(e)=>setMsgForm({...msgForm, originating_vasp_id: e.target.value})} />
              <Input placeholder="Beneficiary VASP ID" value={msgForm.beneficiary_vasp_id} onChange={(e)=>setMsgForm({...msgForm, beneficiary_vasp_id: e.target.value})} />
              <Input placeholder="Transaction Hash (optional)" value={msgForm.transaction_hash} onChange={(e)=>setMsgForm({...msgForm, transaction_hash: e.target.value})} />
              <div>
                <label className="block text-xs text-slate-500 mb-1">Blockchain</label>
                <select className="w-full p-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200" value={msgForm.blockchain} onChange={(e)=>setMsgForm({...msgForm, blockchain: e.target.value})}>
                  {CHAIN_OPTIONS.map(c=> (<option key={c} value={c}>{c}</option>))}
                </select>
              </div>
              <Input placeholder="Asset" value={msgForm.asset} onChange={(e)=>setMsgForm({...msgForm, asset: e.target.value})} />
              <Input placeholder="Amount" value={msgForm.amount} onChange={(e)=>setMsgForm({...msgForm, amount: e.target.value})} />
              <Input placeholder="Amount USD (optional)" value={msgForm.amount_usd} onChange={(e)=>setMsgForm({...msgForm, amount_usd: e.target.value})} />
              <div>
                <label className="block text-xs text-slate-500 mb-1">Protocol</label>
                <select className="w-full p-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200"
                        value={msgForm.protocol}
                        onChange={(e)=>setMsgForm({...msgForm, protocol: e.target.value})}>
                  {TR_PROTOCOLS.map(v=> (<option key={v} value={v}>{v}</option>))}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <textarea className="w-full min-h-[120px] p-3 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200 text-sm" placeholder='Originator JSON (e.g. {"name":"","account_reference":""})' value={msgForm.originator_json} onChange={(e)=>setMsgForm({...msgForm, originator_json: e.target.value})} />
              <textarea className="w-full min-h-[120px] p-3 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200 text-sm" placeholder='Beneficiary JSON (e.g. {"name":"","account_reference":""})' value={msgForm.beneficiary_json} onChange={(e)=>setMsgForm({...msgForm, beneficiary_json: e.target.value})} />
            </div>
            <div className="mt-4 flex items-center">
              <Button onClick={createTravelRuleMessage} disabled={msgSubmitting || !msgValid} className="bg-primary-600 hover:bg-primary-700 text-white disabled:opacity-70">
                {msgSubmitting ? 'Creating…' : 'Create Message'}
              </Button>
            </div>
            {!msgValid && (
              <p className="mt-2 text-xs text-slate-500">Please fill Originating/Beneficiary VASP IDs, Blockchain, Asset, Amount.</p>
            )}
            {createdMessage && (
              <div className="mt-4 p-4 rounded-md bg-slate-50 dark:bg-slate-900/40 overflow-auto">
                <pre className="text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap break-words">{JSON.stringify(createdMessage, null, 2)}</pre>
              </div>
            )}
          </Card>

          {/* List / Send / Acknowledge */}
          <Card className="p-6 bg-white dark:bg-slate-800">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Messages</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <Input placeholder="Originating VASP ID" value={listFilters.originating_vasp_id} onChange={(e)=>setListFilters({...listFilters, originating_vasp_id: e.target.value})} />
              <Input placeholder="Beneficiary VASP ID" value={listFilters.beneficiary_vasp_id} onChange={(e)=>setListFilters({...listFilters, beneficiary_vasp_id: e.target.value})} />
              <div>
                <label className="block text-xs text-slate-500 mb-1">Status</label>
                <select className="w-full p-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200"
                        value={listFilters.status}
                        onChange={(e)=>setListFilters({...listFilters, status: e.target.value})}>
                  <option value="">Any</option>
                  {TR_STATUSES.map(v=> (<option key={v} value={v}>{v}</option>))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1">Blockchain</label>
                <select className="w-full p-2 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200" value={listFilters.blockchain} onChange={(e)=>setListFilters({...listFilters, blockchain: e.target.value})}>
                  <option value="">Any</option>
                  {CHAIN_OPTIONS.map(c=> (<option key={c} value={c}>{c}</option>))}
                </select>
              </div>
            </div>
            <div className="flex items-center gap-2 mb-6">
              <Button onClick={listTravelRuleMessages} disabled={listLoading} className="bg-primary-600 hover:bg-primary-700 text-white">
                {listLoading ? 'Loading…' : 'List Messages'}
              </Button>
            </div>
            {!listLoading && messages.length === 0 && (
              <Card className="p-8 bg-slate-50 dark:bg-slate-900/40 text-center">
                <MessageSquare className="h-10 w-10 text-slate-400 mx-auto mb-2" />
                <p className="text-slate-600 dark:text-slate-400">No messages found.</p>
              </Card>
            )}

            {messages.length > 0 && (
              <div className="grid gap-3 mb-6">
                {messages.map((m, idx) => (
                  <Card key={m.id || idx} className="p-3 bg-white dark:bg-slate-800">
                    {renderMessageSummary(m)}
                  </Card>
                ))}
              </div>
            )}

            <div>
              <h4 className="font-semibold text-slate-900 dark:text-white mb-2">Message Details</h4>
              <div className="flex gap-2 mb-2 items-center">
                <Input placeholder="Message ID" value={msgDetailsId} onChange={(e)=>setMsgDetailsId(e.target.value)} />
                <Button onClick={getTravelRuleMessageDetails} disabled={!msgDetailsId} className="bg-primary-600 hover:bg-primary-700 text-white disabled:opacity-70">Get</Button>
              </div>
              {msgDetailsLoading ? (
                <p className="text-xs text-slate-500">Loading…</p>
              ) : msgDetails ? (
                <div className="p-2 rounded-md bg-slate-50 dark:bg-slate-900/40 whitespace-pre-wrap break-words">
                  {renderMessageSummary(msgDetails)}
                  <pre className="text-xs text-slate-700 dark:text-slate-300">{JSON.stringify(msgDetails, null, 2)}</pre>
                </div>
              ) : null}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

export default VASPCompliance;
