import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, AlertTriangle, CheckCircle, XCircle, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';

interface AddressData {
  address: string;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  labels: string[];
  cluster_id?: string;
  cluster_size?: number;
  first_seen?: string;
  last_seen?: string;
  tx_count?: number;
  balance?: string;
  confidence?: number;
}

interface RiskBadgeProps {
  score: number;
  level: string;
}

const RiskBadge: React.FC<RiskBadgeProps> = ({ score, level }) => {
  const colors = {
    low: 'bg-green-100 text-green-800 border-green-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    high: 'bg-orange-100 text-orange-800 border-orange-200',
    critical: 'bg-red-100 text-red-800 border-red-200',
  };

  const icons = {
    low: <CheckCircle className="w-4 h-4" />,
    medium: <AlertTriangle className="w-4 h-4" />,
    high: <AlertTriangle className="w-4 h-4" />,
    critical: <XCircle className="w-4 h-4" />,
  };

  return (
    <Badge className={`${colors[level as keyof typeof colors]} flex items-center gap-1 px-3 py-1 border`}>
      {icons[level as keyof typeof icons]}
      <span className="font-semibold">{level.toUpperCase()}</span>
      <span className="text-xs ml-1">({Math.round(score * 100)}%)</span>
    </Badge>
  );
};

export function AddressLookup() {
  const [address, setAddress] = useState('');
  const [searchAddress, setSearchAddress] = useState('');
  const navigate = useNavigate();

  const { data, isLoading, error } = useQuery<AddressData>({
    queryKey: ['address', searchAddress],
    queryFn: async () => {
      const response = await api.get(`/api/v1/enrich/${searchAddress}`);
      return response.data;
    },
    enabled: !!searchAddress && searchAddress.length > 10,
    retry: 1,
  });

  const handleSearch = () => {
    if (address.trim().length > 10) {
      setSearchAddress(address.trim());
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            Address Lookup
          </CardTitle>
          <CardDescription>
            Suche nach Blockchain-Adressen für Risk-Scoring und Forensik-Analysen
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="0x... oder bc1... eingeben"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              onKeyPress={handleKeyPress}
              className="font-mono"
              aria-label="Blockchain-Adresse eingeben"
              aria-describedby="address-help"
            />
            <Button
              onClick={handleSearch}
              disabled={!address.trim() || isLoading}
              aria-label="Adresse suchen"
              aria-busy={isLoading}
              title="Suche nach Adresse starten"
            >
              {isLoading ? 'Suche...' : 'Suchen'}
            </Button>
          </div>
          <p id="address-help" className="sr-only">Gültige Formate: EVM (0x...) oder Bitcoin (bc1...). Drücken Sie Enter oder klicken Sie auf Suchen.</p>
        </CardContent>
      </Card>

      {isLoading && (
        <Card>
          <CardContent className="pt-6 space-y-4">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <div className="flex gap-2">
              <Skeleton className="h-10 w-32" />
              <Skeleton className="h-10 w-32" />
            </div>
          </CardContent>
        </Card>
      )}

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6" role="alert" aria-live="polite">
            <div className="flex items-center gap-2 text-red-800">
              <XCircle className="w-5 h-5" aria-hidden />
              <span>Fehler beim Laden der Adresse. Bitte überprüfen Sie das Format.</span>
            </div>
            <div className="mt-4 flex gap-2">
              <Button variant="outline" onClick={handleSearch} aria-label="Erneut versuchen">Erneut versuchen</Button>
              <Button variant="ghost" onClick={() => setAddress('')} aria-label="Eingabe löschen">Eingabe löschen</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {data && (
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="font-mono text-sm break-all">
                  {data.address}
                </CardTitle>
                <CardDescription className="mt-2">
                  Forensik-Analyse für diese Adresse
                </CardDescription>
              </div>
              <RiskBadge score={data.risk_score} level={data.risk_level} />
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Labels */}
            {data.labels && data.labels.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-2">Labels:</h4>
                <div className="flex flex-wrap gap-2">
                  {data.labels.map((label, idx) => {
                    const isDefi = typeof label === 'string' && label.toLowerCase().startsWith('defi:');
                    const pretty = isDefi ? label.replace(/^defi:/i, '') : label;
                    const classes = isDefi
                      ? 'bg-violet-100 text-violet-800 border-violet-200'
                      : '';
                    return (
                      <Badge key={idx} variant="outline" className={classes}>
                        {isDefi ? 'DeFi: ' : ''}{pretty}
                      </Badge>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {data.tx_count !== undefined && (
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Transaktionen</p>
                  <p className="text-2xl font-bold">{data.tx_count.toLocaleString()}</p>
                </div>
              )}
              {data.balance && (
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Balance</p>
                  <p className="text-2xl font-bold">{parseFloat(data.balance).toFixed(4)}</p>
                </div>
              )}
              {data.cluster_size && (
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Cluster Size</p>
                  <p className="text-2xl font-bold">{data.cluster_size}</p>
                </div>
              )}
              {data.confidence !== undefined && (
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Confidence</p>
                  <p className="text-2xl font-bold">{Math.round(data.confidence * 100)}%</p>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex flex-wrap gap-3 pt-4 border-t">
              <Button
                onClick={() => navigate(`/trace?source=${data.address}`)}
                className="flex items-center gap-2"
                aria-label="Funds tracen"
              >
                <TrendingUp className="w-4 h-4" aria-hidden />
                Funds Tracen
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate(`/investigator?address=${data.address}`)}
                aria-label="Investigation starten"
              >
                Investigation starten
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate(`/correlation?address=${data.address}`)}
                aria-label="Cluster-Analyse starten"
              >
                Cluster-Analyse
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
