import React, { useState } from 'react';
import { Plus, Trash2, Link, TrendingUp, Users, DollarSign, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface CustomEntity {
  entity_id: string;
  name: string;
  entity_type: string;
  addresses: any[];
  labels: string[];
  description?: string;
  stats: {
    total_addresses: number;
    total_transactions: number;
    total_value_usd: number;
    unique_counterparties: number;
    risk_score: number;
  };
}

const CustomEntitiesManager: React.FC = () => {
  const [entities, setEntities] = useState<CustomEntity[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newEntityName, setNewEntityName] = useState('');

  const fetchEntities = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/custom-entities/entities`,
        {
          headers: { Authorization: token ? `Bearer ${token}` : '' },
        }
      );

      if (response.data.success) {
        setEntities(response.data.entities);
      }
    } catch (err: any) {
      console.error('Failed to fetch entities:', err);
    } finally {
      setLoading(false);
    }
  };

  const createEntity = async () => {
    if (!newEntityName.trim()) return;

    setCreating(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/custom-entities/entities`,
        {
          name: newEntityName,
          entity_type: 'custom',
          addresses: [],
          labels: [],
        },
        {
          headers: { Authorization: token ? `Bearer ${token}` : '' },
        }
      );

      if (response.data.success) {
        setEntities([...entities, response.data.entity]);
        setNewEntityName('');
      }
    } catch (err: any) {
      console.error('Failed to create entity:', err);
    } finally {
      setCreating(false);
    }
  };

  React.useEffect(() => {
    fetchEntities();
  }, []);

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary via-purple-500 to-blue-500 bg-clip-text text-transparent">
            Custom Entities Manager
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage groups of up to 1M addresses per entity
          </p>
        </div>
      </div>

      {/* Create Entity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Create New Entity
          </CardTitle>
          <CardDescription>
            Group related addresses for investigations and tracking
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="Entity name..."
              value={newEntityName}
              onChange={(e) => setNewEntityName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && createEntity()}
              disabled={creating}
            />
            <Button onClick={createEntity} disabled={creating || !newEntityName.trim()}>
              {creating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="mr-2 h-4 w-4" />
                  Create
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Entities List */}
      {loading ? (
        <div className="flex justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : entities.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center text-muted-foreground">
            No entities yet. Create your first entity above.
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <AnimatePresence>
            {entities.map((entity) => (
              <motion.div
                key={entity.entity_id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
              >
                <Card className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg">{entity.name}</CardTitle>
                        <CardDescription className="mt-1">
                          {entity.entity_type}
                        </CardDescription>
                      </div>
                      {entity.stats.risk_score > 0.7 && (
                        <Badge variant="destructive">High Risk</Badge>
                      )}
                    </div>

                    {/* Labels */}
                    {entity.labels.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {entity.labels.map((label, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {label}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </CardHeader>

                  <CardContent className="space-y-3">
                    {/* Stats */}
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <div className="font-semibold">
                            {entity.stats.total_addresses.toLocaleString()}
                          </div>
                          <div className="text-xs text-muted-foreground">Addresses</div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <div className="font-semibold">
                            {entity.stats.total_transactions.toLocaleString()}
                          </div>
                          <div className="text-xs text-muted-foreground">Transactions</div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <DollarSign className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <div className="font-semibold">
                            ${entity.stats.total_value_usd.toLocaleString()}
                          </div>
                          <div className="text-xs text-muted-foreground">Total Value</div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Link className="h-4 w-4 text-muted-foreground" />
                        <div>
                          <div className="font-semibold">
                            {entity.stats.unique_counterparties.toLocaleString()}
                          </div>
                          <div className="text-xs text-muted-foreground">Counterparties</div>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 pt-2 border-t">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1"
                        onClick={() => {
                          // Navigate to entity detail
                          window.location.href = `/custom-entities/${entity.entity_id}`;
                        }}
                      >
                        View Details
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={async () => {
                          if (confirm(`Delete entity "${entity.name}"?`)) {
                            try {
                              const token = localStorage.getItem('token');
                              await axios.delete(
                                `${API_BASE_URL}/api/v1/custom-entities/entities/${entity.entity_id}`,
                                {
                                  headers: { Authorization: token ? `Bearer ${token}` : '' },
                                }
                              );
                              setEntities(entities.filter(e => e.entity_id !== entity.entity_id));
                            } catch (err) {
                              console.error('Delete failed:', err);
                            }
                          }
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
};

export default CustomEntitiesManager;
