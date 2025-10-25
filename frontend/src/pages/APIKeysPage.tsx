import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Key, Plus, Copy, Trash2, Eye, EyeOff, AlertCircle, CheckCircle2 } from 'lucide-react';
import { format } from 'date-fns';

interface APIKey {
  id: string;
  name: string;
  key_preview: string;
  scopes: string[];
  created_at: string;
  last_used_at?: string;
  expires_at?: string;
  is_active: boolean;
}

const AVAILABLE_SCOPES = [
  { value: 'read:traces', label: 'Traces lesen' },
  { value: 'write:traces', label: 'Traces erstellen' },
  { value: 'read:cases', label: 'Cases lesen' },
  { value: 'write:cases', label: 'Cases erstellen/bearbeiten' },
  { value: 'read:risk', label: 'Risk-Scores lesen' },
  { value: 'read:labels', label: 'Labels lesen' },
  { value: 'read:graph', label: 'Graph-Daten lesen' },
  { value: 'write:webhooks', label: 'Webhooks verwalten' },
  { value: 'admin', label: 'Admin-Zugriff (alle Rechte)' },
];

export default function APIKeysPage() {
  const qc = useQueryClient();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [selectedScopes, setSelectedScopes] = useState<string[]>(['read:traces']);
  const [expiresIn, setExpiresIn] = useState<string>('30');
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [showKey, setShowKey] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Fetch API keys
  const { data: keys, isLoading } = useQuery<APIKey[]>({
    queryKey: ['apiKeys'],
    queryFn: async () => {
      const res = await api.get('/api/v1/keys');
      return res.data.data || [];
    },
  });

  // Create API key
  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/v1/keys', {
        name: newKeyName,
        scopes: selectedScopes,
        expires_in_days: expiresIn === 'never' ? null : parseInt(expiresIn),
      });
      return res.data;
    },
    onSuccess: (data) => {
      setCreatedKey(data.key);
      setNewKeyName('');
      setSelectedScopes(['read:traces']);
      setExpiresIn('30');
      qc.invalidateQueries({ queryKey: ['apiKeys'] });
    },
  });

  // Revoke API key
  const revokeMutation = useMutation({
    mutationFn: async (keyId: string) => {
      await api.delete(`/api/v1/keys/${keyId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['apiKeys'] });
    },
  });

  const handleCopy = (text: string, id?: string) => {
    navigator.clipboard.writeText(text);
    if (id) {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const toggleScope = (scope: string) => {
    setSelectedScopes((prev) =>
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope]
    );
  };

  const handleCreate = () => {
    createMutation.mutate();
  };

  const handleCloseCreatedDialog = () => {
    setCreatedKey(null);
    setCreateDialogOpen(false);
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        <h1 className="text-3xl font-bold">API Keys</h1>
        <Card>
          <CardHeader>
            <div className="animate-pulse space-y-2">
              <div className="h-5 bg-gray-200 rounded w-1/3" />
              <div className="h-4 bg-gray-100 rounded w-2/3" />
            </div>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Key className="w-8 h-8" /> API Keys
        </h1>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Neuen Key erstellen
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Deine API Keys</CardTitle>
          <CardDescription>
            Verwalte API-Keys für programmatischen Zugriff auf die Blockchain-Forensics API
          </CardDescription>
        </CardHeader>
        <CardContent>
          {keys && keys.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Key</TableHead>
                  <TableHead>Scopes</TableHead>
                  <TableHead>Erstellt</TableHead>
                  <TableHead>Zuletzt verwendet</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Aktionen</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {keys.map((key) => (
                  <TableRow key={key.id}>
                    <TableCell className="font-medium">{key.name}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <code className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
                          {key.key_preview}...
                        </code>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCopy(key.key_preview, key.id)}
                        >
                          {copiedId === key.id ? (
                            <CheckCircle2 className="w-4 h-4 text-green-600" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {key.scopes.slice(0, 2).map((scope) => (
                          <Badge key={scope} variant="secondary" className="text-xs">
                            {scope}
                          </Badge>
                        ))}
                        {key.scopes.length > 2 && (
                          <Badge variant="outline" className="text-xs">
                            +{key.scopes.length - 2}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {format(new Date(key.created_at), 'dd.MM.yyyy')}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {key.last_used_at ? format(new Date(key.last_used_at), 'dd.MM.yyyy HH:mm') : 'Nie'}
                    </TableCell>
                    <TableCell>
                      {key.is_active ? (
                        <Badge variant="default">Aktiv</Badge>
                      ) : (
                        <Badge variant="destructive">Inaktiv</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => revokeMutation.mutate(key.id)}
                        disabled={revokeMutation.isPending}
                      >
                        <Trash2 className="w-4 h-4 text-red-600" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-12">
              <Key className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">Noch keine API-Keys erstellt</p>
              <Button onClick={() => setCreateDialogOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Ersten Key erstellen
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Neuen API-Key erstellen</DialogTitle>
            <DialogDescription>
              Erstelle einen neuen API-Key mit spezifischen Berechtigungen
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                placeholder="z.B. Production API Key"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
              />
            </div>

            <div>
              <Label>Berechtigungen (Scopes)</Label>
              <div className="space-y-2 mt-2 border rounded-lg p-3 max-h-64 overflow-y-auto">
                {AVAILABLE_SCOPES.map((scope) => (
                  <div key={scope.value} className="flex items-center space-x-2">
                    <Checkbox
                      id={scope.value}
                      checked={selectedScopes.includes(scope.value)}
                      onCheckedChange={() => toggleScope(scope.value)}
                    />
                    <Label
                      htmlFor={scope.value}
                      className="text-sm font-normal cursor-pointer flex-1"
                    >
                      {scope.label}
                    </Label>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <Label htmlFor="expires">Gültigkeit</Label>
              <Select value={expiresIn} onValueChange={setExpiresIn}>
                <SelectTrigger id="expires">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7">7 Tage</SelectItem>
                  <SelectItem value="30">30 Tage</SelectItem>
                  <SelectItem value="90">90 Tage</SelectItem>
                  <SelectItem value="365">1 Jahr</SelectItem>
                  <SelectItem value="never">Niemals ablaufen</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5" />
              <div className="text-sm text-amber-800">
                <p className="font-medium">Wichtig</p>
                <p>Der API-Key wird nur einmal angezeigt. Speichere ihn sicher!</p>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Abbrechen
            </Button>
            <Button
              onClick={handleCreate}
              disabled={createMutation.isPending || !newKeyName || selectedScopes.length === 0}
            >
              Key erstellen
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Created Key Dialog */}
      <Dialog open={!!createdKey} onOpenChange={handleCloseCreatedDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>API-Key erfolgreich erstellt</DialogTitle>
            <DialogDescription>
              Kopiere deinen neuen API-Key. Er wird nur einmal angezeigt!
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div>
              <Label>Dein neuer API-Key</Label>
              <div className="flex items-center gap-2 mt-2">
                <Input
                  type={showKey ? 'text' : 'password'}
                  value={createdKey || ''}
                  readOnly
                  className="font-mono"
                />
                <Button variant="ghost" size="icon" onClick={() => setShowKey(!showKey)}>
                  {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </Button>
                <Button variant="outline" onClick={() => createdKey && handleCopy(createdKey)}>
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
              <div className="text-sm text-red-800">
                <p className="font-medium">Wichtig</p>
                <p>
                  Dieser Key wird nur einmal angezeigt. Speichere ihn sicher, z.B. in einem
                  Passwort-Manager.
                </p>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button onClick={handleCloseCreatedDialog}>Verstanden</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
