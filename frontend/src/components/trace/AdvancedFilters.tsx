'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Filter, X, Calendar, DollarSign, Layers } from 'lucide-react';

interface AdvancedFiltersProps {
  onFilterChange: (filters: TraceFilters) => void;
  onReset: () => void;
}

export interface TraceFilters {
  startDate?: string;
  endDate?: string;
  minAmount?: number;
  maxAmount?: number;
  chains?: string[];
  eventTypes?: string[];
  riskLevels?: string[];
  excludeLabels?: string[];
}

export function AdvancedFilters({ onFilterChange, onReset }: AdvancedFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [filters, setFilters] = useState<TraceFilters>({});

  const chains = ['ethereum', 'bitcoin', 'polygon', 'arbitrum', 'optimism', 'solana'];
  const eventTypes = ['transfer', 'token_transfer', 'dex_swap', 'bridge', 'contract_call'];
  const riskLevels = ['low', 'medium', 'high', 'critical'];

  const updateFilter = (key: keyof TraceFilters, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const toggleArrayFilter = (key: 'chains' | 'eventTypes' | 'riskLevels', value: string) => {
    const current = filters[key] || [];
    const newArray = current.includes(value)
      ? current.filter((v) => v !== value)
      : [...current, value];
    updateFilter(key, newArray.length > 0 ? newArray : undefined);
  };

  const handleReset = () => {
    setFilters({});
    onReset();
  };

  const activeFilterCount = Object.keys(filters).filter((key) => {
    const value = filters[key as keyof TraceFilters];
    return value !== undefined && (Array.isArray(value) ? value.length > 0 : true);
  }).length;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Filter className="w-5 h-5" />
              Advanced Filters
              {activeFilterCount > 0 && (
                <Badge variant="secondary">{activeFilterCount} aktiv</Badge>
              )}
            </CardTitle>
            <CardDescription>Verfeinern Sie Ihre Trace-Suche</CardDescription>
          </div>
          <div className="flex gap-2">
            {activeFilterCount > 0 && (
              <Button size="sm" variant="outline" onClick={handleReset}>
                <X className="w-4 h-4 mr-1" />
                Reset
              </Button>
            )}
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? 'Einklappen' : 'Erweitern'}
            </Button>
          </div>
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="space-y-6">
          {/* Date Range */}
          <div className="space-y-3">
            <Label className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              Zeitraum
            </Label>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="startDate" className="text-xs text-muted-foreground">
                  Von
                </Label>
                <Input
                  id="startDate"
                  type="date"
                  value={filters.startDate || ''}
                  onChange={(e) => updateFilter('startDate', e.target.value || undefined)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="endDate" className="text-xs text-muted-foreground">
                  Bis
                </Label>
                <Input
                  id="endDate"
                  type="date"
                  value={filters.endDate || ''}
                  onChange={(e) => updateFilter('endDate', e.target.value || undefined)}
                />
              </div>
            </div>
          </div>

          {/* Amount Range */}
          <div className="space-y-3">
            <Label className="flex items-center gap-2">
              <DollarSign className="w-4 h-4" />
              Betragsspanne (USD)
            </Label>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="minAmount" className="text-xs text-muted-foreground">
                  Min
                </Label>
                <Input
                  id="minAmount"
                  type="number"
                  placeholder="0"
                  value={filters.minAmount || ''}
                  onChange={(e) =>
                    updateFilter('minAmount', e.target.value ? parseFloat(e.target.value) : undefined)
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="maxAmount" className="text-xs text-muted-foreground">
                  Max
                </Label>
                <Input
                  id="maxAmount"
                  type="number"
                  placeholder="∞"
                  value={filters.maxAmount || ''}
                  onChange={(e) =>
                    updateFilter('maxAmount', e.target.value ? parseFloat(e.target.value) : undefined)
                  }
                />
              </div>
            </div>
          </div>

          {/* Chains */}
          <div className="space-y-3">
            <Label className="flex items-center gap-2">
              <Layers className="w-4 h-4" />
              Blockchains
            </Label>
            <div className="flex flex-wrap gap-2">
              {chains.map((chain) => (
                <Badge
                  key={chain}
                  variant={filters.chains?.includes(chain) ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => toggleArrayFilter('chains', chain)}
                >
                  {chain}
                </Badge>
              ))}
            </div>
          </div>

          {/* Event Types */}
          <div className="space-y-3">
            <Label>Transaction Types</Label>
            <div className="flex flex-wrap gap-2">
              {eventTypes.map((type) => (
                <Badge
                  key={type}
                  variant={filters.eventTypes?.includes(type) ? 'default' : 'outline'}
                  className="cursor-pointer"
                  onClick={() => toggleArrayFilter('eventTypes', type)}
                >
                  {type.replace('_', ' ')}
                </Badge>
              ))}
            </div>
          </div>

          {/* Risk Levels */}
          <div className="space-y-3">
            <Label>Risk Levels</Label>
            <div className="flex flex-wrap gap-2">
              {riskLevels.map((level) => (
                <Badge
                  key={level}
                  variant={filters.riskLevels?.includes(level) ? 'default' : 'outline'}
                  className={`cursor-pointer ${
                    filters.riskLevels?.includes(level)
                      ? level === 'critical'
                        ? 'bg-red-600'
                        : level === 'high'
                        ? 'bg-orange-500'
                        : level === 'medium'
                        ? 'bg-yellow-500'
                        : 'bg-green-500'
                      : ''
                  }`}
                  onClick={() => toggleArrayFilter('riskLevels', level)}
                >
                  {level}
                </Badge>
              ))}
            </div>
          </div>

          {/* Active Filters Summary */}
          {activeFilterCount > 0 && (
            <div className="pt-4 border-t">
              <p className="text-sm font-medium mb-2">Aktive Filter:</p>
              <div className="text-xs text-muted-foreground space-y-1">
                {filters.startDate && <p>• Von: {new Date(filters.startDate).toLocaleDateString()}</p>}
                {filters.endDate && <p>• Bis: {new Date(filters.endDate).toLocaleDateString()}</p>}
                {filters.minAmount && <p>• Min Betrag: ${filters.minAmount.toLocaleString()}</p>}
                {filters.maxAmount && <p>• Max Betrag: ${filters.maxAmount.toLocaleString()}</p>}
                {filters.chains && filters.chains.length > 0 && (
                  <p>• Chains: {filters.chains.join(', ')}</p>
                )}
                {filters.eventTypes && filters.eventTypes.length > 0 && (
                  <p>• Types: {filters.eventTypes.join(', ')}</p>
                )}
                {filters.riskLevels && filters.riskLevels.length > 0 && (
                  <p>• Risk: {filters.riskLevels.join(', ')}</p>
                )}
              </div>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
