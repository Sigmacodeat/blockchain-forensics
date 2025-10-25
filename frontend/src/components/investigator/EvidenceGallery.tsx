'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { api } from '@/lib/api';
import { Upload, Image as ImageIcon, FileText, Download, Trash2, Plus } from 'lucide-react';

interface Evidence {
  id: string;
  type: 'screenshot' | 'document' | 'note';
  title: string;
  description?: string;
  url?: string;
  content?: string;
  created_at: string;
}

interface EvidenceGalleryProps {
  caseId: string;
}

export function EvidenceGallery({ caseId }: EvidenceGalleryProps) {
  const queryClient = useQueryClient();
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [newEvidence, setNewEvidence] = useState({
    type: 'note' as Evidence['type'],
    title: '',
    description: '',
    content: '',
  });

  const { data: evidence, isLoading } = useQuery<Evidence[]>({
    queryKey: ['evidence', caseId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/cases/${caseId}/evidence`);
      return response.data;
    },
  });

  const addEvidenceMutation = useMutation({
    mutationFn: async (data: typeof newEvidence) => {
      const response = await api.post(`/api/v1/cases/${caseId}/evidence`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence', caseId] });
      setIsAddOpen(false);
      setNewEvidence({ type: 'note', title: '', description: '', content: '' });
    },
  });

  const deleteEvidenceMutation = useMutation({
    mutationFn: async (evidenceId: string) => {
      await api.delete(`/api/v1/cases/${caseId}/evidence/${evidenceId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence', caseId] });
    },
  });

  const handleAddEvidence = () => {
    if (!newEvidence.title.trim()) return;
    addEvidenceMutation.mutate(newEvidence);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // In production würde hier der Upload zur API erfolgen
    alert(`File upload in Entwicklung: ${file.name}`);
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-48 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Add Button */}
      <div className="flex justify-end">
        <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
          <DialogTrigger asChild>
            <Button className="flex items-center gap-2">
              <Plus className="w-4 h-4" />
              Beweis hinzufügen
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Neuen Beweis hinzufügen</DialogTitle>
              <DialogDescription>
                Fügen Sie einen Screenshot, Dokument oder eine Notiz hinzu
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="evidence-type">Typ</Label>
                <select
                  id="evidence-type"
                  className="w-full p-2 border rounded-md"
                  value={newEvidence.type}
                  onChange={(e) =>
                    setNewEvidence({ ...newEvidence, type: e.target.value as Evidence['type'] })
                  }
                >
                  <option value="note">Notiz</option>
                  <option value="screenshot">Screenshot</option>
                  <option value="document">Dokument</option>
                </select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="evidence-title">Titel *</Label>
                <Input
                  id="evidence-title"
                  placeholder="z.B. Transaction Hash Screenshot"
                  value={newEvidence.title}
                  onChange={(e) => setNewEvidence({ ...newEvidence, title: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="evidence-description">Beschreibung</Label>
                <Textarea
                  id="evidence-description"
                  placeholder="Zusätzliche Details..."
                  value={newEvidence.description}
                  onChange={(e) => setNewEvidence({ ...newEvidence, description: e.target.value })}
                  rows={2}
                />
              </div>

              {newEvidence.type === 'note' && (
                <div className="space-y-2">
                  <Label htmlFor="evidence-content">Inhalt</Label>
                  <Textarea
                    id="evidence-content"
                    placeholder="Notiz-Inhalt..."
                    value={newEvidence.content}
                    onChange={(e) => setNewEvidence({ ...newEvidence, content: e.target.value })}
                    rows={4}
                  />
                </div>
              )}

              {(newEvidence.type === 'screenshot' || newEvidence.type === 'document') && (
                <div className="space-y-2">
                  <Label htmlFor="file-upload">Datei hochladen</Label>
                  <Input
                    id="file-upload"
                    type="file"
                    accept={newEvidence.type === 'screenshot' ? 'image/*' : '*'}
                    onChange={handleFileUpload}
                  />
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsAddOpen(false)}>
                Abbrechen
              </Button>
              <Button
                onClick={handleAddEvidence}
                disabled={!newEvidence.title.trim() || addEvidenceMutation.isPending}
              >
                {addEvidenceMutation.isPending ? 'Speichert...' : 'Hinzufügen'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Evidence Grid */}
      {!evidence || evidence.length === 0 ? (
        <Card>
          <CardContent className="pt-6 text-center text-sm text-muted-foreground">
            <Upload className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>Noch keine Beweise hinzugefügt</p>
            <p className="text-xs mt-1">Fügen Sie Screenshots, Dokumente oder Notizen hinzu</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {evidence.map((item) => (
            <Card key={item.id} className="overflow-hidden">
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {item.type === 'screenshot' && <ImageIcon className="w-4 h-4" />}
                    {item.type === 'document' && <FileText className="w-4 h-4" />}
                    {item.type === 'note' && <FileText className="w-4 h-4" />}
                    <h4 className="font-semibold text-sm">{item.title}</h4>
                  </div>
                  <div className="flex gap-1">
                    {item.url && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => window.open(item.url, '_blank')}
                      >
                        <Download className="w-3 h-3" />
                      </Button>
                    )}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => deleteEvidenceMutation.mutate(item.id)}
                    >
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>

                {item.description && (
                  <p className="text-xs text-muted-foreground mb-3">{item.description}</p>
                )}

                {item.type === 'note' && item.content && (
                  <div className="p-2 bg-muted rounded text-xs whitespace-pre-wrap mb-3">
                    {item.content}
                  </div>
                )}

                {item.url && item.type === 'screenshot' && (
                  <div className="mb-3 rounded overflow-hidden border">
                    <img
                      src={item.url}
                      alt={item.title}
                      className="w-full h-32 object-cover"
                    />
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <Badge variant="secondary" className="text-xs">
                    {item.type}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    {new Date(item.created_at).toLocaleDateString('de-DE')}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
