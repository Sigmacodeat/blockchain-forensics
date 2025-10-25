'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { api } from '@/lib/api';
import { Clock, User, FileText, AlertCircle } from 'lucide-react';

interface TimelineEvent {
  id: string;
  type: 'address_added' | 'note_added' | 'status_changed' | 'evidence_added' | 'alert_triggered';
  title: string;
  description: string;
  timestamp: string;
  user?: string;
  metadata?: Record<string, any>;
}

interface CaseTimelineProps {
  caseId: string;
}

export function CaseTimeline({ caseId }: CaseTimelineProps) {
  const { data: events, isLoading } = useQuery<TimelineEvent[]>({
    queryKey: ['caseTimeline', caseId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/cases/${caseId}/timeline`);
      return response.data;
    },
  });

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'address_added':
        return <User className="w-4 h-4" />;
      case 'note_added':
        return <FileText className="w-4 h-4" />;
      case 'alert_triggered':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case 'alert_triggered':
        return 'border-red-200 bg-red-50';
      case 'address_added':
        return 'border-blue-200 bg-blue-50';
      case 'evidence_added':
        return 'border-green-200 bg-green-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
    );
  }

  if (!events || events.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6 text-center text-sm text-muted-foreground">
          <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Noch keine Timeline-Events für diesen Case</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="relative space-y-4">
      {/* Timeline Line */}
      <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-border" />

      {events.map((event) => (
        <div key={event.id} className="relative pl-16">
          {/* Timeline Dot */}
          <div className="absolute left-4 top-4 w-4 h-4 rounded-full bg-primary border-2 border-background" />

          <Card className={getEventColor(event.type)}>
            <CardContent className="pt-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  {getEventIcon(event.type)}
                  <h4 className="font-semibold text-sm">{event.title}</h4>
                </div>
                <Badge variant="secondary" className="text-xs">
                  {event.type.replace('_', ' ')}
                </Badge>
              </div>

              <p className="text-sm text-muted-foreground mb-2">{event.description}</p>

              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{new Date(event.timestamp).toLocaleString('de-DE')}</span>
                {event.user && (
                  <span className="flex items-center gap-1">
                    <User className="w-3 h-3" />
                    {event.user}
                  </span>
                )}
              </div>

              {event.metadata && Object.keys(event.metadata).length > 0 && (
                <div className="mt-3 pt-3 border-t">
                  <details className="text-xs">
                    <summary className="cursor-pointer font-medium">Details anzeigen</summary>
                    <pre className="mt-2 p-2 bg-black/5 rounded overflow-x-auto">
                      {JSON.stringify(event.metadata, null, 2)}
                    </pre>
                  </details>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      ))}
    </div>
  );
}
