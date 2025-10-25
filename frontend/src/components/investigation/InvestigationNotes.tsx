/**
 * Investigation Notes Component
 * ==============================
 * 
 * Enhanced note-taking for forensic investigations (Chainalysis-Style).
 * 
 * Features:
 * - Rich text editing with Markdown support
 * - Evidence linking (attach to graph nodes/transactions)
 * - Collaborative editing with real-time sync
 * - Export to PDF with chain-of-custody
 * - Search and categorization
 * - Timestamped audit trail
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import {
  FileText, Plus, Save, Download, Link as LinkIcon,
  Clock, User, Tag, Search, Filter, Archive, Eye, EyeOff
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Note {
  id: string;
  case_id: string;
  title: string;
  content: string;
  category: 'observation' | 'hypothesis' | 'evidence' | 'conclusion' | 'general';
  tags: string[];
  linked_addresses: string[];
  linked_transactions: string[];
  author: string;
  created_at: string;
  updated_at: string;
  is_archived: boolean;
  attachments: Array<{
    type: 'address' | 'transaction' | 'graph_node';
    id: string;
    label: string;
  }>;
}

interface InvestigationNotesProps {
  caseId: string;
  currentAddress?: string;
  onLinkAddress?: (address: string) => void;
}

const CATEGORIES = [
  { value: 'observation', label: 'Observation', color: 'bg-blue-100 text-blue-700' },
  { value: 'hypothesis', label: 'Hypothesis', color: 'bg-purple-100 text-purple-700' },
  { value: 'evidence', label: 'Evidence', color: 'bg-red-100 text-red-700' },
  { value: 'conclusion', label: 'Conclusion', color: 'bg-green-100 text-green-700' },
  { value: 'general', label: 'General', color: 'bg-gray-100 text-gray-700' }
];

export default function InvestigationNotes({
  caseId,
  currentAddress,
  onLinkAddress
}: InvestigationNotesProps) {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [editingNote, setEditingNote] = useState<Note | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [showArchived, setShowArchived] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    category: 'observation' as Note['category'],
    tags: [] as string[],
    linked_addresses: [] as string[],
    linked_transactions: [] as string[]
  });

  // Fetch notes
  const { data: notes = [], isLoading } = useQuery({
    queryKey: ['investigation-notes', caseId, showArchived, categoryFilter],
    queryFn: async () => {
      const params = new URLSearchParams({
        case_id: caseId,
        include_archived: String(showArchived)
      });
      if (categoryFilter) {
        params.set('category', categoryFilter);
      }
      
      const response = await axios.get(`${API_BASE_URL}/api/v1/case/${caseId}/notes?${params}`);
      return response.data as Note[];
    }
  });

  // Create/Update note
  const saveMutation = useMutation({
    mutationFn: async (note: Partial<Note>) => {
      if (editingNote) {
        const response = await axios.put(
          `${API_BASE_URL}/api/v1/case/${caseId}/notes/${editingNote.id}`,
          note
        );
        return response.data;
      } else {
        const response = await axios.post(
          `${API_BASE_URL}/api/v1/case/${caseId}/notes`,
          { ...note, case_id: caseId }
        );
        return response.data;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investigation-notes', caseId] });
      resetForm();
    }
  });

  // Delete note
  const deleteMutation = useMutation({
    mutationFn: async (noteId: string) => {
      await axios.delete(`${API_BASE_URL}/api/v1/case/${caseId}/notes/${noteId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investigation-notes', caseId] });
    }
  });

  // Archive/Unarchive
  const archiveMutation = useMutation({
    mutationFn: async ({ noteId, archive }: { noteId: string; archive: boolean }) => {
      await axios.patch(`${API_BASE_URL}/api/v1/case/${caseId}/notes/${noteId}`, {
        is_archived: archive
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investigation-notes', caseId] });
    }
  });

  const resetForm = () => {
    setFormData({
      title: '',
      content: '',
      category: 'observation',
      tags: [],
      linked_addresses: [],
      linked_transactions: []
    });
    setIsCreating(false);
    setEditingNote(null);
  };

  const handleSave = () => {
    saveMutation.mutate(formData);
  };

  const handleEdit = (note: Note) => {
    setEditingNote(note);
    setFormData({
      title: note.title,
      content: note.content,
      category: note.category,
      tags: note.tags,
      linked_addresses: note.linked_addresses,
      linked_transactions: note.linked_transactions
    });
    setIsCreating(true);
  };

  const handleLinkCurrentAddress = () => {
    if (currentAddress && !formData.linked_addresses.includes(currentAddress)) {
      setFormData(prev => ({
        ...prev,
        linked_addresses: [...prev.linked_addresses, currentAddress]
      }));
    }
  };

  const handleAddTag = (tag: string) => {
    if (tag && !formData.tags.includes(tag)) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tag]
      }));
    }
  };

  const handleExportPDF = useCallback(async () => {
    // Would generate PDF with all notes
    const response = await axios.post(
      `${API_BASE_URL}/api/v1/case/${caseId}/notes/export`,
      { format: 'pdf', include_archived: showArchived },
      { responseType: 'blob' }
    );
    
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `investigation_notes_${caseId}_${Date.now()}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  }, [caseId, showArchived]);

  // Filter notes by search
  const filteredNotes = notes.filter(note => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        note.title.toLowerCase().includes(query) ||
        note.content.toLowerCase().includes(query) ||
        note.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }
    return true;
  });

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <FileText className="h-6 w-6 text-primary-600" />
          <h2 className="text-2xl font-bold text-gray-900">Investigation Notes</h2>
          <span className="text-sm text-gray-500">({filteredNotes.length})</span>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowArchived(!showArchived)}
            className="px-3 py-2 text-sm border rounded-md hover:bg-gray-50 flex items-center gap-2"
          >
            {showArchived ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
            {showArchived ? 'Hide Archived' : 'Show Archived'}
          </button>
          
          <button
            onClick={handleExportPDF}
            className="px-3 py-2 text-sm bg-gray-100 rounded-md hover:bg-gray-200 flex items-center gap-2"
            disabled={notes.length === 0}
          >
            <Download className="h-4 w-4" />
            Export PDF
          </button>
          
          <button
            onClick={() => setIsCreating(true)}
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            New Note
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search notes..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <select
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
            value={categoryFilter || ''}
            onChange={(e) => setCategoryFilter(e.target.value || null)}
          >
            <option value="">All Categories</option>
            {CATEGORIES.map(cat => (
              <option key={cat.value} value={cat.value}>{cat.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Create/Edit Form */}
      {isCreating && (
        <div className="border border-gray-200 rounded-lg p-6 mb-6 bg-gray-50">
          <h3 className="text-lg font-semibold mb-4">
            {editingNote ? 'Edit Note' : 'New Note'}
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Note title..."
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                value={formData.category}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  category: e.target.value as Note['category']
                }))}
              >
                {CATEGORIES.map(cat => (
                  <option key={cat.value} value={cat.value}>{cat.label}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Content
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm"
                rows={10}
                value={formData.content}
                onChange={(e) => setFormData(prev => ({ ...prev, content: e.target.value }))}
                placeholder="Markdown supported...

**Bold**, *italic*, `code`

- Bullet points
- Lists

1. Numbered
2. Lists"
              />
              <p className="text-xs text-gray-500 mt-1">Markdown syntax supported</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tags
              </label>
              <div className="flex flex-wrap gap-2 mb-2">
                {formData.tags.map((tag, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-primary-100 text-primary-700 rounded text-sm"
                  >
                    <Tag className="h-3 w-3" />
                    {tag}
                    <button
                      onClick={() => setFormData(prev => ({
                        ...prev,
                        tags: prev.tags.filter((_, idx) => idx !== i)
                      }))}
                      className="ml-1 hover:text-primary-900"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                placeholder="Add tag and press Enter..."
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleAddTag((e.target as HTMLInputElement).value);
                    (e.target as HTMLInputElement).value = '';
                  }
                }}
              />
            </div>
            
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Linked Addresses ({formData.linked_addresses.length})
                </label>
                {currentAddress && (
                  <button
                    onClick={handleLinkCurrentAddress}
                    className="text-xs text-primary-600 hover:text-primary-700 flex items-center gap-1"
                  >
                    <LinkIcon className="h-3 w-3" />
                    Link Current Address
                  </button>
                )}
              </div>
              <div className="space-y-1">
                {formData.linked_addresses.map((addr, i) => (
                  <div key={i} className="flex items-center justify-between text-sm bg-white px-3 py-2 rounded border">
                    <code className="text-xs">{addr}</code>
                    <button
                      onClick={() => setFormData(prev => ({
                        ...prev,
                        linked_addresses: prev.linked_addresses.filter((_, idx) => idx !== i)
                      }))}
                      className="text-red-600 hover:text-red-700"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="flex items-center gap-3 pt-4">
              <button
                onClick={handleSave}
                disabled={!formData.title || !formData.content || saveMutation.isPending}
                className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 flex items-center gap-2"
              >
                <Save className="h-4 w-4" />
                {saveMutation.isPending ? 'Saving...' : editingNote ? 'Update' : 'Save'}
              </button>
              
              <button
                onClick={resetForm}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Notes List */}
      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading notes...</div>
      ) : filteredNotes.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-3" />
          <p>No notes yet. Create your first investigation note!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredNotes.map((note) => {
            const category = CATEGORIES.find(c => c.value === note.category);
            
            return (
              <div
                key={note.id}
                className={`border rounded-lg p-4 hover:shadow-md transition-shadow ${
                  note.is_archived ? 'bg-gray-50 opacity-75' : 'bg-white'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{note.title}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded ${category?.color}`}>
                        {category?.label}
                      </span>
                      {note.is_archived && (
                        <span className="text-xs px-2 py-0.5 rounded bg-gray-200 text-gray-600">
                          Archived
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <User className="h-3 w-3" />
                        {note.author}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(note.created_at).toLocaleString()}
                      </span>
                      {note.updated_at !== note.created_at && (
                        <span className="text-xs text-gray-400">
                          (edited {new Date(note.updated_at).toLocaleString()})
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleEdit(note)}
                      className="text-sm text-primary-600 hover:text-primary-700"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => archiveMutation.mutate({
                        noteId: note.id,
                        archive: !note.is_archived
                      })}
                      className="text-sm text-gray-600 hover:text-gray-700"
                    >
                      {note.is_archived ? 'Unarchive' : 'Archive'}
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('Delete this note?')) {
                          deleteMutation.mutate(note.id);
                        }
                      }}
                      className="text-sm text-red-600 hover:text-red-700"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                
                <div className="prose prose-sm max-w-none mb-3">
                  <pre className="whitespace-pre-wrap font-sans text-sm text-gray-700 bg-gray-50 p-3 rounded">
                    {note.content}
                  </pre>
                </div>
                
                {note.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-3">
                    {note.tags.map((tag, i) => (
                      <span
                        key={i}
                        className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}
                
                {note.linked_addresses.length > 0 && (
                  <div className="border-t pt-3">
                    <div className="text-xs font-medium text-gray-700 mb-2">
                      Linked Addresses ({note.linked_addresses.length})
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {note.linked_addresses.slice(0, 5).map((addr, i) => (
                        <button
                          key={i}
                          onClick={() => onLinkAddress?.(addr)}
                          className="text-xs font-mono px-2 py-1 bg-primary-50 text-primary-700 rounded hover:bg-primary-100"
                        >
                          {addr.slice(0, 10)}...{addr.slice(-8)}
                        </button>
                      ))}
                      {note.linked_addresses.length > 5 && (
                        <span className="text-xs text-gray-500">
                          +{note.linked_addresses.length - 5} more
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
