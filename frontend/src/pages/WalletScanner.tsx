import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Key,
  Shield,
  AlertTriangle,
  Search,
  DollarSign,
  Activity,
  Eye,
  EyeOff,
  CheckCircle,
  Upload,
} from 'lucide-react';
import {
  useScanSeedPhrase,
  useScanPrivateKey,
  useBulkScan,
  useScanAddresses,
  formatBalance,
  getRiskColor,
  getActivityColor,
} from '@/hooks/useWalletScanner';
import type { WalletScanResult } from '@/hooks/useWalletScanner';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import RiskCopilot from '@/components/RiskCopilot';

export default function WalletScanner() {
  const [activeTab, setActiveTab] = useState<'seed' | 'private' | 'bulk' | 'addresses'>('seed');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-purple-50 to-blue-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <div className="flex items-center justify-center mb-4">
              <Key className="w-16 h-16 mr-4" />
              <h1 className="text-4xl font-bold">Wallet Scanner</h1>
            </div>
            <p className="text-xl text-blue-100 max-w-3xl mx-auto">
              🔍 Multi-Chain Wallet Analysis & Asset Recovery Tool
            </p>
            <p className="text-sm text-blue-200 mt-2">
              Professional Wallet Analysis • Zero Storage Policy
            </p>
            <div className="mt-6 max-w-3xl mx-auto text-left bg-white/10 rounded-lg p-4 backdrop-blur">
              <h3 className="font-semibold mb-2">So nutzen Sie den Wallet Scanner</h3>
              <ol className="list-decimal list-inside text-sm text-blue-100 space-y-1">
                <li><strong>Empfohlen:</strong> Wählen Sie den Tab <em>Addresses (Zero-Trust)</em>.</li>
                <li>Fügen Sie eine oder mehrere <em>öffentliche</em> Adressen ein (z.B. 0x… oder bc1q…).</li>
                <li>Klicken Sie auf <em>Scan</em> – wir analysieren Chains, Risiko und Verbindungen.</li>
              </ol>
            </div>
          </motion.div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Security Notice */}
        <Card className="p-4 mb-8 bg-green-50 dark:bg-green-900/20 border-green-200">
          <div className="flex items-start gap-3">
            <Shield className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-green-900 dark:text-green-100 mb-1">
                🔒 Security Guarantee
              </h4>
              <ul className="text-sm text-green-800 dark:text-green-200 space-y-1">
                <li>• Seeds/Keys processed <strong>in-memory only</strong> - never stored</li>
                <li>• End-to-end encrypted transmission</li>
                <li>• Audit logs without credentials</li>
                <li>• SOC 2 Type II compliant infrastructure</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-auto">
            <TabsTrigger value="seed" title="Nur bei Eigenprüfung nötig – bevorzugen Sie Adressen (Zero-Trust)" className="flex items-center gap-2">
              <Key className="w-4 h-4" />
              Seed Phrase
            </TabsTrigger>
            <TabsTrigger value="private" title="Nur in Ausnahmefällen – bevorzugen Sie Adressen (Zero-Trust)" className="flex items-center gap-2">
              <Shield className="w-4 h-4" />
              Private Key
            </TabsTrigger>
            <TabsTrigger value="addresses" title="Empfohlen: Sicher & einfach – nur öffentliche Adressen" className="flex items-center gap-2">
              <Search className="w-4 h-4" />
              Addresses (Zero-Trust)
            </TabsTrigger>
            <TabsTrigger value="bulk" title="Viele Adressen per CSV prüfen" className="flex items-center gap-2">
              <Upload className="w-4 h-4" />
              Bulk Scan
            </TabsTrigger>
          </TabsList>

          <TabsContent value="seed">
            <SeedPhraseScanner />
          </TabsContent>

          <TabsContent value="private">
            <PrivateKeyScanner />
          </TabsContent>

          <TabsContent value="addresses">
            <AddressesScanner />
          </TabsContent>

          <TabsContent value="bulk">
            <BulkScanner />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

// Zero-Trust Addresses Scanner
function AddressesScanner() {
  const [rows, setRows] = useState<Array<{ chain: string; address: string }>>([
    { chain: 'ethereum', address: '' },
  ]);
  const [checkHistory, setCheckHistory] = useState(true);
  const [checkIllicit, setCheckIllicit] = useState(true);

  const { mutate: scan, data: result, isPending, error } = useScanAddresses();

  const canScan = rows.some(r => r.address.trim().length > 0);

  const handleScan = () => {
    if (!canScan) return;
    scan({
      addresses: rows.filter(r => r.address.trim()),
      check_history: checkHistory,
      check_illicit: checkIllicit,
    });
  };

  const setRow = (idx: number, next: Partial<{ chain: string; address: string }>) => {
    setRows(prev => prev.map((r, i) => (i === idx ? { ...r, ...next } : r)));
  };

  const addRow = () => setRows(prev => [...prev, { chain: 'ethereum', address: '' }]);
  const removeRow = (idx: number) => setRows(prev => prev.filter((_, i) => i !== idx));

  const chains = [
    'ethereum', 'bitcoin', 'polygon', 'arbitrum', 'optimism', 'base',
    'avalanche', 'bsc', 'fantom', 'solana'
  ];

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Search className="w-5 h-5 text-green-600" />
          Scan Addresses (Zero-Trust)
        </h3>

        <div className="space-y-3">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            <strong>Empfohlen:</strong> Sie prüfen nur <em>öffentliche</em> Adressen – keine Seeds oder Private Keys. Das ist die sicherste und einfachste Methode.
          </p>
          {rows.map((row, idx) => (
            <div key={idx} className="grid grid-cols-1 md:grid-cols-12 gap-2 items-center">
              <div className="md:col-span-3">
                <label className="block text-xs text-slate-500 mb-1">Chain</label>
                <select
                  value={row.chain}
                  onChange={(e) => setRow(idx, { chain: e.target.value })}
                  className="w-full p-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800"
                >
                  {chains.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
                <p className="text-[11px] text-slate-500 mt-1">Wählen Sie die Blockchain der Adresse.</p>
              </div>
              <div className="md:col-span-8">
                <label className="block text-xs text-slate-500 mb-1">Address</label>
                <input
                  value={row.address}
                  onChange={(e) => setRow(idx, { address: e.target.value })}
                  placeholder="0x... oder bc1q..."
                  className="w-full p-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 font-mono"
                />
                <p className="text-[11px] text-slate-500 mt-1">Fügen Sie die <em>öffentliche</em> Adresse ein (z.B. 0x… für EVM, bc1q… für Bitcoin).</p>
              </div>
              <div className="md:col-span-1 flex justify-end">
                <button
                  onClick={() => removeRow(idx)}
                  className="px-3 py-2 text-sm rounded border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700"
                  aria-label="Zeile entfernen"
                >
                  −
                </button>
              </div>
            </div>
          ))}

          <div className="flex items-center gap-2">
            <button
              onClick={addRow}
              className="px-3 py-2 text-sm rounded border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700"
            >
              + Adresse hinzufügen
            </button>
          </div>

          <div className="space-y-2 mt-2">
            <label className="flex items-center gap-2">
              <input type="checkbox" className="rounded" checked={checkHistory} onChange={(e) => setCheckHistory(e.target.checked)} />
              <span className="text-sm">Check transaction history</span>
            </label>
            <p className="text-[11px] text-slate-500 -mt-1 ml-6">Analysiert frühere Transaktionen – kann länger dauern, liefert aber mehr Details.</p>
            <label className="flex items-center gap-2">
              <input type="checkbox" className="rounded" checked={checkIllicit} onChange={(e) => setCheckIllicit(e.target.checked)} />
              <span className="text-sm">Check for illicit connections</span>
            </label>
            <p className="text-[11px] text-slate-500 -mt-1 ml-6">Prüft Verbindungen zu sanktionierten, betrugsnahen oder Mixer-Adressen.</p>
          </div>

          <Button
            onClick={handleScan}
            disabled={isPending || !canScan}
            className="w-full mt-2"
            size="lg"
          >
            {isPending ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Scanning...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Scan Addresses
              </>
            )}
          </Button>
        </div>
      </Card>

      {/* Error */}
      {error && (
        <Card className="p-4 bg-red-50 dark:bg-red-900/20 border-red-200">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">Error: {error.message}</span>
          </div>
        </Card>
      )}

      {/* Results */}
      {result && <ScanResults result={result} />}
    </div>
  );
}

// Seed Phrase Scanner
function SeedPhraseScanner() {
  const [seedPhrase, setSeedPhrase] = useState('');
  const [selectedChains, setSelectedChains] = useState(['ethereum', 'bitcoin', 'polygon']);
  const [showSeed, setShowSeed] = useState(false);
  const [checkHistory, setCheckHistory] = useState(true);
  const [checkIllicit, setCheckIllicit] = useState(true);

  const { mutate: scan, data: result, isPending, error } = useScanSeedPhrase();

  const handleScan = () => {
    if (!seedPhrase) return;
    scan({
      seed_phrase: seedPhrase,
      chains: selectedChains,
      check_history: checkHistory,
      check_illicit: checkIllicit,
    });
  };

  const chains = [
    'ethereum', 'bitcoin', 'polygon', 'arbitrum', 'optimism', 'base',
    'avalanche', 'bsc', 'fantom', 'solana'
  ];

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Key className="w-5 h-5 text-purple-600" />
          Scan BIP39 Seed Phrase
        </h3>

        <div className="space-y-4">
          {/* Seed Phrase Input */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Seed Phrase (12 or 24 words) *
              </label>
              <button
                onClick={() => setShowSeed(!showSeed)}
                className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
              >
                {showSeed ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                {showSeed ? 'Hide' : 'Show'}
              </button>
            </div>
            <Textarea
              placeholder="word1 word2 word3..."
              value={seedPhrase}
              onChange={(e) => setSeedPhrase(e.target.value)}
              rows={3}
              className={`font-mono ${!showSeed ? 'text-security-disc' : ''}`}
            />
            <p className="text-xs text-slate-500 mt-1">
              {seedPhrase.split(' ').filter(w => w).length} words entered
            </p>
          </div>

          {/* Chain Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Chains to Scan
            </label>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
              {chains.map((chain) => (
                <label
                  key={chain}
                  className={`flex items-center gap-2 p-2 rounded border cursor-pointer transition-colors ${
                    selectedChains.includes(chain)
                      ? 'bg-primary-50 border-primary-500 text-primary-700'
                      : 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-600'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedChains.includes(chain)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedChains([...selectedChains, chain]);
                      } else {
                        setSelectedChains(selectedChains.filter((c) => c !== chain));
                      }
                    }}
                    className="rounded"
                  />
                  <span className="text-sm capitalize">{chain}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Options */}
          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={checkHistory}
                onChange={(e) => setCheckHistory(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm text-slate-700 dark:text-slate-300">
                Check transaction history
              </span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={checkIllicit}
                onChange={(e) => setCheckIllicit(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm text-slate-700 dark:text-slate-300">
                Check for illicit connections
              </span>
            </label>
          </div>

          {/* Scan Button */}
          <Button
            onClick={handleScan}
            disabled={isPending || !seedPhrase || selectedChains.length === 0}
            className="w-full"
            size="lg"
          >
            {isPending ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Scanning...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Scan Wallet
              </>
            )}
          </Button>
        </div>
      </Card>

      {/* Error */}
      {error && (
        <Card className="p-4 bg-red-50 dark:bg-red-900/20 border-red-200">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">Error: {error.message}</span>
          </div>
        </Card>
      )}

      {/* Results */}
      {result && <ScanResults result={result} />}
    </div>
  );
}

// Private Key Scanner
function PrivateKeyScanner() {
  const [privateKey, setPrivateKey] = useState('');
  const [chain, setChain] = useState('ethereum');
  const [showKey, setShowKey] = useState(false);
  const [checkHistory, setCheckHistory] = useState(true);
  const [checkIllicit, setCheckIllicit] = useState(true);

  const { mutate: scan, data: result, isPending, error } = useScanPrivateKey();

  const handleScan = () => {
    if (!privateKey) return;
    scan({
      private_key: privateKey,
      chain,
      check_history: checkHistory,
      check_illicit: checkIllicit,
    });
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-600" />
          Scan Private Key
        </h3>

        <div className="space-y-4">
          {/* Private Key Input */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                Private Key (hex format) *
              </label>
              <button
                onClick={() => setShowKey(!showKey)}
                className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                {showKey ? 'Hide' : 'Show'}
              </button>
            </div>
            <Textarea
              placeholder="0x1234567890abcdef..."
              value={privateKey}
              onChange={(e) => setPrivateKey(e.target.value)}
              rows={3}
              className={`font-mono ${!showKey ? 'text-security-disc' : ''}`}
            />
          </div>

          {/* Chain Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Chain
            </label>
            <select
              value={chain}
              onChange={(e) => setChain(e.target.value)}
              className="w-full p-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800"
            >
              <option value="ethereum">Ethereum</option>
              <option value="polygon">Polygon</option>
              <option value="arbitrum">Arbitrum</option>
              <option value="optimism">Optimism</option>
              <option value="base">Base</option>
            </select>
          </div>

          {/* Options */}
          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={checkHistory}
                onChange={(e) => setCheckHistory(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm text-slate-700 dark:text-slate-300">
                Check transaction history
              </span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={checkIllicit}
                onChange={(e) => setCheckIllicit(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm text-slate-700 dark:text-slate-300">
                Check for illicit connections
              </span>
            </label>
          </div>

          {/* Scan Button */}
          <Button
            onClick={handleScan}
            disabled={isPending || !privateKey}
            className="w-full"
            size="lg"
          >
            {isPending ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Scanning...
              </>
            ) : (
              <>
                <Search className="w-4 h-4 mr-2" />
                Scan Wallet
              </>
            )}
          </Button>
        </div>
      </Card>

      {/* Error */}
      {error && (
        <Card className="p-4 bg-red-50 dark:bg-red-900/20 border-red-200">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">Error: {error.message}</span>
          </div>
        </Card>
      )}

      {/* Results */}
      {result && <ScanResults result={result} />}
    </div>
  );
}

// Bulk Scanner
function BulkScanner() {
  const [fileName, setFileName] = useState<string>("");
  const [parseError, setParseError] = useState<string>("");
  const { mutate: scanAddresses, data: result, isPending, error } = useScanAddresses();

  const onFile = async (file: File) => {
    setParseError("");
    setFileName(file.name);
    try {
      const text = await file.text();
      const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
      if (lines.length === 0) throw new Error("Empty CSV");
      const header = lines[0].toLowerCase();
      if (!header.includes("chain") || !header.includes("address")) {
        throw new Error("CSV header must contain 'chain,address'");
      }
      const rows = lines.slice(1)
        .map(l => l.split(",").map(s => s.trim()))
        .filter(parts => parts.length >= 2 && parts[0] && parts[1])
        .map(parts => ({ chain: parts[0], address: parts[1] }));
      if (rows.length === 0) throw new Error("No valid rows found");
      scanAddresses({ addresses: rows, check_history: false, check_illicit: true });
    } catch (e: any) {
      setParseError(e?.message || "Failed to parse CSV");
    }
  };

  return (
    <div className="space-y-4">
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Upload className="w-5 h-5 text-orange-600" />
          Bulk Wallet Scan
        </h3>
        <div className="space-y-3">
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void onFile(f);
            }}
            aria-label="Upload CSV with chain,address"
          />
          {fileName && (
            <div className="text-sm text-slate-600 dark:text-slate-300">Selected: {fileName}</div>
          )}
          {parseError && (
            <Card className="p-3 bg-red-50 dark:bg-red-900/20 border-red-200">
              <div className="text-sm text-red-700 dark:text-red-300">{parseError}</div>
            </Card>
          )}
          <div>
            <Button disabled className="opacity-50 cursor-not-allowed">Use CSV with columns: chain,address</Button>
          </div>
        </div>
      </Card>

      {/* Error */}
      {error && (
        <Card className="p-4 bg-red-50 dark:bg-red-900/20 border-red-200">
          <div className="flex items-center gap-2 text-red-700 dark:text-red-300">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">Error: {error.message}</span>
          </div>
        </Card>
      )}

      {/* Results */}
      {isPending && (
        <Card className="p-4">
          <div className="text-sm">Scanning addresses...</div>
        </Card>
      )}
      {result && <ScanResults result={result as any} />}
    </div>
  );
}

// Scan Results Component
interface ScanResultsProps {
  result: WalletScanResult;
}

function ScanResults({ result }: ScanResultsProps) {
  const navigate = useNavigate();
  
  const downloadCSV = () => {
    const scanId = result.scan_id || 'scan';
    window.open(`/api/v1/wallet-scanner/report/${scanId}/csv`, '_blank');
  };
  
  const downloadPDF = () => {
    const scanId = result.scan_id || 'scan';
    window.open(`/api/v1/wallet-scanner/report/${scanId}/pdf`, '_blank');
  };
  
  const downloadEvidence = async () => {
    const scanId = result.scan_id || 'scan';
    const resp = await fetch(`/api/v1/wallet-scanner/report/${scanId}/evidence`);
    const data = await resp.json();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evidence-${scanId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Summary */}
      <Card className={`p-6 border-l-4 ${getRiskBorderColor(result.risk_level)}`}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <DollarSign className="w-6 h-6 text-green-600" />
              <h3 className="text-2xl font-bold">
                {formatBalance(result.total_balance_usd)}
              </h3>
              <Badge className={getRiskColor(result.risk_level)}>
                {result.risk_level.toUpperCase()}
              </Badge>
              <Badge className={getActivityColor(result.activity_level)}>
                {result.activity_level}
              </Badge>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <StatBox
            icon={<Activity className="w-5 h-5" />}
            label="Transactions"
            value={result.total_transactions}
          />
          <StatBox
            icon={<Key className="w-5 h-5" />}
            label="Addresses"
            value={result.addresses.length}
          />
          <StatBox
            icon={<Shield className="w-5 h-5" />}
            label="Risk Score"
            value={`${(result.risk_score * 100).toFixed(0)}%`}
          />
          <StatBox
            icon={<CheckCircle className="w-5 h-5" />}
            label="Type"
            value={result.wallet_type}
          />
        </div>

        {/* Export Buttons */}
        <div className="flex flex-wrap gap-2 mb-4">
          <Button variant="outline" size="sm" onClick={downloadCSV}>
            Export CSV
          </Button>
          <Button variant="outline" size="sm" onClick={downloadPDF}>
            Export PDF
          </Button>
          <Button variant="outline" size="sm" onClick={downloadEvidence}>
            Download Evidence (JSON)
          </Button>
        </div>

        {/* Recommendations */}
        {result.recommendations.length > 0 && (
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200">
            <h4 className="font-semibold mb-2 text-blue-900 dark:text-blue-100">
              💡 Recommendations
            </h4>
            <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
              {result.recommendations.map((rec, idx) => (
                <li key={idx}>• {rec}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Warnings */}
        {result.warnings.length > 0 && (
          <div className="mt-4 p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200">
            <h4 className="font-semibold mb-2 text-orange-900 dark:text-orange-100 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Warnings
            </h4>
            <ul className="text-sm text-orange-800 dark:text-orange-200 space-y-1">
              {result.warnings.map((warn, idx) => (
                <li key={idx}>⚠️ {warn}</li>
              ))}
            </ul>
          </div>
        )}
      </Card>

      {/* Address Details */}
      <div className="space-y-4">
        <h4 className="font-semibold text-lg">Addresses ({result.addresses.length})</h4>
        {result.addresses.map((addr, idx) => (
          <Card key={idx} className="p-4">
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <code className="text-sm font-mono text-slate-700 dark:text-slate-300">
                  {addr.address}
                </code>
                <Badge className="ml-2 text-xs">{addr.chain}</Badge>
              </div>
              <Badge className={getRiskColor(addr.risk_level)}>
                {addr.risk_level}
              </Badge>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-slate-500">Balance</p>
                <p className="font-semibold">
                  {formatBalance(addr.balance.native_balance_usd)}
                </p>
              </div>
              <div>
                <p className="text-slate-500">Transactions</p>
                <p className="font-semibold">{addr.transaction_count}</p>
              </div>
              <div>
                <p className="text-slate-500">Tokens</p>
                <p className="font-semibold">{addr.balance.tokens.length}</p>
              </div>
              <div>
                <p className="text-slate-500">Illicit Links</p>
                <p className="font-semibold">{addr.illicit_connections.length}</p>
              </div>
            </div>
            {/* RiskCopilot compact */}
            <div className="mt-3">
              <RiskCopilot address={addr.address} chain={addr.chain} variant="compact" />
            </div>
            {/* Actions */}
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                onClick={() => navigate(`/address/${addr.address}`)}
                className="px-3 py-2 text-xs rounded border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700"
                aria-label="Open Address Analysis"
              >
                Open Address
              </button>
              <button
                onClick={() => navigate(`/investigator?address=${encodeURIComponent(addr.address)}&chain=${encodeURIComponent(addr.chain)}`)}
                className="px-3 py-2 text-xs rounded border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700"
                aria-label="Open in Investigator Graph"
              >
                Open in Investigator
              </button>
            </div>
          </Card>
        ))}
      </div>
    </motion.div>
  );
}

interface StatBoxProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
}

function StatBox({ icon, label, value }: StatBoxProps) {
  return (
    <div className="flex items-center gap-2">
      <div className="text-slate-400">{icon}</div>
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="font-semibold text-slate-900 dark:text-white">{value}</p>
      </div>
    </div>
  );
}

function getRiskBorderColor(level: string): string {
  const colors: Record<string, string> = {
    critical: 'border-red-500',
    high: 'border-orange-500',
    medium: 'border-yellow-500',
    low: 'border-green-500',
  };
  return colors[level] || 'border-slate-300';
}
