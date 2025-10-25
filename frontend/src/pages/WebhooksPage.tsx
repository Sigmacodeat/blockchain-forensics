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
import { Checkbox } from '@/components/ui/checkbox';
import { Webhook, Plus, Trash2, Send, CheckCircle2, XCircle, Clock, Eye } from 'lucide-react';
import { format } from 'date-fns';

interface WebhookEndpoint {
  id: string;
  url: string;
  events: string[];
  is_active: boolean;
  secret: string;
  created_at: string;
  last_triggered_at?: string;
  success_count: number;
  failure_count: number;
}

interface WebhookDelivery {
  id: string;
  webhook_id: string;
  event_type: string;
  status: 'success' | 'failed' | 'pending';
  response_code?: number;
  response_body?: string;
  created_at: string;
  delivered_at?: string;
}

const AVAILABLE_EVENTS = [
  { value: 'trace.completed', label: 'Trace abgeschlossen', description: 'Wird ausgelöst wenn ein Trace fertig ist' },
  { value: 'trace.failed', label: 'Trace fehlgeschlagen', description: 'Wird bei Trace-Fehler ausgelöst' },
  { value: 'case.created', label: 'Case erstellt', description: 'Neuer Case wurde angelegt' },
  { value: 'case.updated', label: 'Case aktualisiert', description: 'Case-Status hat sich geändert' },
  { value: 'alert.triggered', label: 'Alert ausgelöst', description: 'Risk-Alert wurde ausgelöst' },
  { value: 'risk.high', label: 'High Risk erkannt', description: 'Adresse mit hohem Risiko-Score' },
  { value: 'sanctions.hit', label: 'Sanctions Hit', description: 'Sanktionierte Adresse gefunden' },
  { value: 'mixer.detected', label: 'Mixer erkannt', description: 'Mixer-Aktivität entdeckt' },
];

export default function WebhooksPage() {
  const qc = useQueryClient();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [selectedWebhook, setSelectedWebhook] = useState<WebhookEndpoint | null>(null);
  const [webhookUrl, setWebhookUrl] = useState('');
  const [selectedEvents, setSelectedEvents] = useState<string[]>(['trace.completed']);

  // Fetch webhooks
  const { data: webhooks, isLoading } = useQuery<WebhookEndpoint[]>({
    queryKey: ['webhooks'],
    queryFn: async () => {
      const res = await api.get('/api/v1/webhooks');
      return res.data.data || [];
    },
  });

  // Fetch webhook deliveries
  const { data: deliveries } = useQuery<WebhookDelivery[]>({
    queryKey: ['webhookDeliveries', selectedWebhook?.id],
    queryFn: async () => {
      if (!selectedWebhook) return [];
      const res = await api.get(`/api/v1/webhooks/${selectedWebhook.id}/deliveries`);
      return res.data.data || [];
    },
    enabled: !!selectedWebhook,
  });

  // Create webhook
  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post('/api/v1/webhooks', {
        url: webhookUrl,
        events: selectedEvents,
      });
      return res.data;
    },
    onSuccess: () => {
      setWebhookUrl('');
      setSelectedEvents(['trace.completed']);
      setCreateDialogOpen(false);
      qc.invalidateQueries({ queryKey: ['webhooks'] });
    },
  });

  // Delete webhook
  const deleteMutation = useMutation({
    mutationFn: async (webhookId: string) => {
      await api.delete(`/api/v1/webhooks/${webhookId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['webhooks'] });
    },
  });

  // Test webhook
  const testMutation = useMutation({
    mutationFn: async (webhookId: string) => {
      await api.post(`/api/v1/webhooks/${webhookId}/test`);
    },
  });

  // Toggle webhook status
  const toggleMutation = useMutation({
    mutationFn: async ({ id, is_active }: { id: string; is_active: boolean }) => {
      await api.patch(`/api/v1/webhooks/${id}`, { is_active: !is_active });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['webhooks'] });
    },
  });

  const toggleEvent = (event: string) => {
    setSelectedEvents((prev) =>
      prev.includes(event) ? prev.filter((e) => e !== event) : [...prev, event]
    );
  };

  const handleCreate = () => {
    createMutation.mutate();
  };

  const handleViewDetails = (webhook: WebhookEndpoint) => {
    setSelectedWebhook(webhook);
    setDetailsDialogOpen(true);
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        <h1 className="text-3xl font-bold">Webhooks</h1>
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
          <Webhook className="w-8 h-8" /> Webhooks
        </h1>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Webhook erstellen
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Webhook-Endpunkte</CardTitle>
          <CardDescription>
            Erhalte Echtzeit-Benachrichtigungen über Events in deinem Account
          </CardDescription>
        </CardHeader>
        <CardContent>
          {webhooks && webhooks.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>URL</TableHead>
                  <TableHead>Events</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Erfolgsrate</TableHead>
                  <TableHead>Zuletzt ausgelöst</TableHead>
                  <TableHead className="text-right">Aktionen</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {webhooks.map((webhook) => (
                  <TableRow key={webhook.id}>
                    <TableCell>
                      <code className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
                        {webhook.url.length > 50 ? webhook.url.slice(0, 50) + '...' : webhook.url}
                      </code>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {webhook.events.slice(0, 2).map((event) => (
                          <Badge key={event} variant="secondary" className="text-xs">
                            {event}
                          </Badge>
                        ))}
                        {webhook.events.length > 2 && (
                          <Badge variant="outline" className="text-xs">
                            +{webhook.events.length - 2}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleMutation.mutate({ id: webhook.id, is_active: webhook.is_active })}
                      >
                        {webhook.is_active ? (
                          <Badge variant="default" className="flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Aktiv
                          </Badge>
                        ) : (
                          <Badge variant="secondary" className="flex items-center gap-1">
                            <XCircle className="w-3 h-3" /> Inaktiv
                          </Badge>
                        )}
                      </Button>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {webhook.success_count + webhook.failure_count > 0 ? (
                          <>
                            <span className="text-green-600 font-medium">{webhook.success_count}</span>
                            <span className="text-muted-foreground"> / </span>
                            <span className="text-red-600">{webhook.failure_count}</span>
                            <span className="text-muted-foreground ml-1">
                              ({Math.round((webhook.success_count / (webhook.success_count + webhook.failure_count)) * 100)}%)
                            </span>
                          </>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {webhook.last_triggered_at
                        ? format(new Date(webhook.last_triggered_at), 'dd.MM.yyyy HH:mm')
                        : 'Nie'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="sm" onClick={() => handleViewDetails(webhook)}>
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => testMutation.mutate(webhook.id)}
                          disabled={testMutation.isPending}
                        >
                          <Send className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => deleteMutation.mutate(webhook.id)}
                          disabled={deleteMutation.isPending}
                        >
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-12">
              <Webhook className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-4">Noch keine Webhooks konfiguriert</p>
              <Button onClick={() => setCreateDialogOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Ersten Webhook erstellen
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Neuen Webhook erstellen</DialogTitle>
            <DialogDescription>
              Konfiguriere einen Webhook-Endpunkt für Echtzeit-Benachrichtigungen
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="url">Webhook-URL</Label>
              <Input
                id="url"
                type="url"
                placeholder="https://yourdomain.com/webhooks/blockchain-forensics"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
              />
              <p className="text-sm text-muted-foreground mt-1">
                Die URL muss HTTPS verwenden und öffentlich erreichbar sein
              </p>
            </div>

            <div>
              <Label>Events</Label>
              <div className="space-y-3 mt-2 border rounded-lg p-3 max-h-80 overflow-y-auto">
                {AVAILABLE_EVENTS.map((event) => (
                  <div key={event.value} className="flex items-start space-x-2">
                    <Checkbox
                      id={event.value}
                      checked={selectedEvents.includes(event.value)}
                      onCheckedChange={() => toggleEvent(event.value)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <Label
                        htmlFor={event.value}
                        className="text-sm font-medium cursor-pointer"
                      >
                        {event.label}
                      </Label>
                      <p className="text-xs text-muted-foreground">{event.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Abbrechen
            </Button>
            <Button
              onClick={handleCreate}
              disabled={createMutation.isPending || !webhookUrl || selectedEvents.length === 0}
            >
              Webhook erstellen
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Details Dialog */}
      <Dialog open={detailsDialogOpen} onOpenChange={setDetailsDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Webhook-Details</DialogTitle>
            <DialogDescription>Delivery-Historie und Konfiguration</DialogDescription>
          </DialogHeader>

          {selectedWebhook && (
            <div className="space-y-4 py-4">
              <div>
                <Label>URL</Label>
                <code className="block text-sm font-mono bg-gray-100 px-3 py-2 rounded mt-1">
                  {selectedWebhook.url}
                </code>
              </div>

              <div>
                <Label>Signing Secret</Label>
                <code className="block text-sm font-mono bg-gray-100 px-3 py-2 rounded mt-1">
                  {selectedWebhook.secret}
                </code>
                <p className="text-xs text-muted-foreground mt-1">
                  Nutze diesen Secret um Webhook-Requests zu verifizieren
                </p>
              </div>

              <div>
                <Label>Events</Label>
                <div className="flex flex-wrap gap-1 mt-2">
                  {selectedWebhook.events.map((event) => (
                    <Badge key={event} variant="secondary">
                      {event}
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <Label>Delivery-Historie</Label>
                {deliveries && deliveries.length > 0 ? (
                  <Table className="mt-2">
                    <TableHeader>
                      <TableRow>
                        <TableHead>Event</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Response</TableHead>
                        <TableHead>Zeit</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {deliveries.slice(0, 10).map((delivery) => (
                        <TableRow key={delivery.id}>
                          <TableCell>
                            <Badge variant="outline">{delivery.event_type}</Badge>
                          </TableCell>
                          <TableCell>
                            {delivery.status === 'success' ? (
                              <Badge variant="default" className="flex items-center gap-1 w-fit">
                                <CheckCircle2 className="w-3 h-3" /> Erfolg
                              </Badge>
                            ) : delivery.status === 'failed' ? (
                              <Badge variant="destructive" className="flex items-center gap-1 w-fit">
                                <XCircle className="w-3 h-3" /> Fehler
                              </Badge>
                            ) : (
                              <Badge variant="secondary" className="flex items-center gap-1 w-fit">
                                <Clock className="w-3 h-3" /> Ausstehend
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {delivery.response_code || '-'}
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {format(new Date(delivery.created_at), 'dd.MM.yyyy HH:mm:ss')}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <p className="text-sm text-muted-foreground mt-2">Noch keine Deliveries</p>
                )}
              </div>
            </div>
          )}

          <DialogFooter>
            <Button onClick={() => setDetailsDialogOpen(false)}>Schließen</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
