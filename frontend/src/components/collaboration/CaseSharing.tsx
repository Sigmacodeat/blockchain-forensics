'use client';

import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { api } from '@/lib/api';
import { Share2, Users, MessageSquare, Plus, Trash2, Eye, Edit } from 'lucide-react';

interface CaseCollaborator {
  id: string;
  user_id: string;
  email: string;
  role: 'owner' | 'editor' | 'viewer';
  added_at: string;
}

interface CaseComment {
  id: string;
  user_id: string;
  user_email: string;
  content: string;
  created_at: string;
}

interface CaseSharingProps {
  caseId: string;
}

export function CaseSharing({ caseId }: CaseSharingProps) {
  const queryClient = useQueryClient();
  const [isShareOpen, setIsShareOpen] = useState(false);
  const [isCommentsOpen, setIsCommentsOpen] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserRole, setNewUserRole] = useState<'editor' | 'viewer'>('viewer');
  const [newComment, setNewComment] = useState('');

  // Fetch collaborators
  const { data: collaborators } = useQuery<CaseCollaborator[]>({
    queryKey: ['collaborators', caseId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/cases/${caseId}/collaborators`);
      return response.data;
    },
  });

  // Fetch comments
  const { data: comments } = useQuery<CaseComment[]>({
    queryKey: ['comments', caseId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/cases/${caseId}/comments`);
      return response.data;
    },
  });

  // Add collaborator
  const addCollaboratorMutation = useMutation({
    mutationFn: async ({ email, role }: { email: string; role: string }) => {
      const response = await api.post(`/api/v1/cases/${caseId}/collaborators`, { email, role });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collaborators', caseId] });
      setNewUserEmail('');
      setIsShareOpen(false);
    },
  });

  // Remove collaborator
  const removeCollaboratorMutation = useMutation({
    mutationFn: async (collaboratorId: string) => {
      await api.delete(`/api/v1/cases/${caseId}/collaborators/${collaboratorId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collaborators', caseId] });
    },
  });

  // Add comment
  const addCommentMutation = useMutation({
    mutationFn: async (content: string) => {
      const response = await api.post(`/api/v1/cases/${caseId}/comments`, { content });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', caseId] });
      setNewComment('');
    },
  });

  const handleAddCollaborator = () => {
    if (!newUserEmail.trim()) return;
    addCollaboratorMutation.mutate({ email: newUserEmail, role: newUserRole });
  };

  const handleAddComment = () => {
    if (!newComment.trim()) return;
    addCommentMutation.mutate(newComment);
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'owner':
        return <Users className="w-4 h-4" />;
      case 'editor':
        return <Edit className="w-4 h-4" />;
      case 'viewer':
        return <Eye className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getRoleBadge = (role: string) => {
    const colors = {
      owner: 'bg-purple-100 text-purple-800',
      editor: 'bg-blue-100 text-blue-800',
      viewer: 'bg-gray-100 text-gray-800',
    };
    return colors[role as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="flex gap-2">
      {/* Share Dialog */}
      <Dialog open={isShareOpen} onOpenChange={setIsShareOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" className="flex items-center gap-2">
            <Share2 className="w-4 h-4" />
            Share ({collaborators?.length || 0})
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Case teilen</DialogTitle>
            <DialogDescription>
              Laden Sie Teammitglieder ein, um gemeinsam an diesem Case zu arbeiten
            </DialogDescription>
          </DialogHeader>

          {/* Add new collaborator */}
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2 space-y-2">
                <Label htmlFor="email">E-Mail</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="colleague@example.com"
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="role">Rolle</Label>
                <Select value={newUserRole} onValueChange={(value: any) => setNewUserRole(value)}>
                  <SelectTrigger id="role">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="viewer">Viewer</SelectItem>
                    <SelectItem value="editor">Editor</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button
              onClick={handleAddCollaborator}
              disabled={!newUserEmail.trim() || addCollaboratorMutation.isPending}
              className="w-full"
            >
              <Plus className="w-4 h-4 mr-2" />
              {addCollaboratorMutation.isPending ? 'Wird hinzugefügt...' : 'Hinzufügen'}
            </Button>
          </div>

          {/* Collaborators list */}
          <div className="space-y-2 max-h-60 overflow-y-auto">
            <Label>Aktuelle Collaborators:</Label>
            {collaborators && collaborators.length > 0 ? (
              collaborators.map((collab) => (
                <div
                  key={collab.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {getRoleIcon(collab.role)}
                    <div>
                      <p className="text-sm font-medium">{collab.email}</p>
                      <p className="text-xs text-muted-foreground">
                        Hinzugefügt: {new Date(collab.added_at).toLocaleDateString('de-DE')}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getRoleBadge(collab.role)}>{collab.role}</Badge>
                    {collab.role !== 'owner' && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => removeCollaboratorMutation.mutate(collab.id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">
                Noch keine Collaborators
              </p>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Comments Dialog */}
      <Dialog open={isCommentsOpen} onOpenChange={setIsCommentsOpen}>
        <DialogTrigger asChild>
          <Button variant="outline" className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4" />
            Comments ({comments?.length || 0})
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Case Comments</DialogTitle>
            <DialogDescription>Team-Diskussion zu diesem Case</DialogDescription>
          </DialogHeader>

          {/* Comments list */}
          <div className="space-y-3 max-h-96 overflow-y-auto py-4">
            {comments && comments.length > 0 ? (
              comments.map((comment) => (
                <div key={comment.id} className="p-3 border rounded-lg space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{comment.user_email}</span>
                    <span className="text-xs text-muted-foreground">
                      {new Date(comment.created_at).toLocaleString('de-DE')}
                    </span>
                  </div>
                  <p className="text-sm">{comment.content}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">
                Noch keine Kommentare. Starten Sie die Diskussion!
              </p>
            )}
          </div>

          {/* Add comment */}
          <div className="space-y-3 border-t pt-4">
            <Textarea
              placeholder="Kommentar hinzufügen..."
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              rows={3}
            />
            <Button
              onClick={handleAddComment}
              disabled={!newComment.trim() || addCommentMutation.isPending}
              className="w-full"
            >
              {addCommentMutation.isPending ? 'Wird gepostet...' : 'Kommentar posten'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
