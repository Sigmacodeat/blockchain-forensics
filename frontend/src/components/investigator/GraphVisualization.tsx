import React, { useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Globe,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Download,
  Eye,
  Search,
} from 'lucide-react';
import InvestigatorGraph from '@/components/InvestigatorGraph';
import { LocalGraph, GraphControls } from './types';
import { Button } from '@/components/ui/button';

interface GraphVisualizationProps {
  localGraph: LocalGraph | null;
  graphLoading: boolean;
  selectedAddress: string;
  highlightedPath?: string[];
  freezeLayout: boolean;
  lastSnapshotHash: string | null;
  breadcrumbs: string[];
  onNodeClick: (node: any) => void;
  onReady: (controls: GraphControls) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onZoomToFit: () => void;
  onClearPath: () => void;
  onExportPNG: () => void;
  onExportPDF: () => void;
  onSaveSnapshot: () => void;
  onOpenVerify: () => void;
  onAskAssistant: () => void;
  onBreadcrumbClick: (index: number) => void;
  graphControls: GraphControls | null;
}

export const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  localGraph,
  graphLoading,
  selectedAddress,
  highlightedPath,
  freezeLayout,
  lastSnapshotHash,
  breadcrumbs,
  onNodeClick,
  onReady,
  onZoomIn,
  onZoomOut,
  onZoomToFit,
  onClearPath,
  onExportPNG,
  onExportPDF,
  onSaveSnapshot,
  onOpenVerify,
  onAskAssistant,
  onBreadcrumbClick,
  graphControls,
}) => {
  const { t } = useTranslation();
  const graphContainerRef = useRef<HTMLDivElement>(null);
  const liveRegionRef = useRef<HTMLDivElement>(null);

  const memoNodes = React.useMemo(
    () => (localGraph?.nodes ? localGraph.nodes : {}),
    [localGraph]
  );
  const memoLinks = React.useMemo(
    () => (localGraph?.links ? localGraph.links : []),
    [localGraph]
  );

  return (
    <div className="bg-card text-foreground rounded-xl shadow-lg border border-border overflow-hidden">
      <div className="p-6 border-b border-border">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Globe className="h-5 w-5 text-primary-600 dark:text-primary-400" />
            Network Graph
          </h3>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={onOpenVerify} aria-label="Verify Snapshot" className="flex items-center gap-1.5">
              <Eye className="h-3.5 w-3.5" />
              Verify
            </Button>
            <Button variant="ghost" size="sm" onClick={onZoomIn} aria-label="Zoom in">
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={onZoomOut} aria-label="Zoom out">
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={onZoomToFit} aria-label="Reset view">
              <RotateCcw className="h-4 w-4" />
            </Button>
            {highlightedPath && (
              <Button variant="outline" size="sm" onClick={onClearPath}>
                Clear Path
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={onExportPNG} aria-label="Export graph as PNG" className="flex items-center gap-1.5">
              <Download className="h-3.5 w-3.5" />
              PNG
            </Button>
            <Button variant="outline" size="sm" onClick={onAskAssistant} aria-label="Ask Assistant">
              AI Assistant
            </Button>
            <Button variant="outline" size="sm" onClick={onSaveSnapshot} aria-label="Save snapshot JSON" className="flex items-center gap-1.5">
              <Download className="h-3.5 w-3.5" />
              Snapshot
            </Button>
            <Button variant="outline" size="sm" onClick={onExportPDF} aria-label="Export PDF" className="flex items-center gap-1.5">
              <Download className="h-3.5 w-3.5" />
              PDF
            </Button>
          </div>
        </div>

        {/* Evidence Hash (last snapshot) */}
        {lastSnapshotHash && (
          <div
            className="p-3 rounded-lg mb-4 border border-border bg-muted/50"
            role="status"
            aria-live="polite"
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-medium">
                Evidence SHA-256:
              </span>
            </div>
            <div className="flex items-center gap-2">
              <code className="font-mono text-xs break-all flex-1">
                {lastSnapshotHash}
              </code>
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigator.clipboard?.writeText(lastSnapshotHash || '')}
                aria-label="Copy SHA-256 hash"
              >
                Copy
              </Button>
            </div>
          </div>
        )}

        {/* Breadcrumbs */}
        {breadcrumbs.length > 0 && (
          <div
            className="flex flex-wrap items-center gap-2"
            aria-label="Breadcrumbs for selected path"
            role="navigation"
          >
            {breadcrumbs.map((addr, idx) => (
              <React.Fragment key={`${addr}-${idx}`}>
                {idx > 0 && (
                  <span className="text-slate-400 dark:text-slate-600" aria-hidden="true">
                    /
                  </span>
                )}
                <Button
                  variant={idx === breadcrumbs.length - 1 ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => onBreadcrumbClick(idx)}
                  title={addr}
                  aria-label={`Go to breadcrumb ${idx + 1} for address ${addr}`}
                  className="font-mono"
                >
                  {addr.slice(0, 10)}...{addr.slice(-6)}
                </Button>
              </React.Fragment>
            ))}
          </div>
        )}
      </div>

      {graphLoading ? (
        <div className="h-96 flex items-center justify-center p-6">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400 mx-auto mb-4"></div>
            <p className="text-muted-foreground">
              {t('investigator.graph.loading', 'Loading graph data...')}
            </p>
          </div>
        </div>
      ) : localGraph ? (
        <>
          <div ref={graphContainerRef} tabIndex={0} className="h-[32rem] bg-background overflow-hidden">
            <InvestigatorGraph
              nodes={memoNodes}
              links={memoLinks}
              selectedAddress={selectedAddress}
              onNodeClick={onNodeClick}
              onEdgeClick={() => {}}
              onReady={onReady}
              highlightPath={highlightedPath}
              disableAutoFit={freezeLayout}
            />
          </div>
          <div ref={liveRegionRef} className="sr-only" aria-live="polite" />
        </>
      ) : (
        <div className="h-96 flex items-center justify-center p-6">
          <div className="text-center">
            <Search className="h-16 w-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
            <p className="text-slate-600 dark:text-slate-400 text-lg font-medium mb-2">
              {t('investigator.graph.enter_address', 'Enter an address above to explore the network')}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-500">
              Start by searching for an Ethereum or Bitcoin address
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
