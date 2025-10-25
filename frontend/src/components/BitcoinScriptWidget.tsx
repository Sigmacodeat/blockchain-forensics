// Bitcoin Script Analysis Widget
// Kleines React-Komponente für TX-Script-Details in Case-Views oder TX-Inspektionen

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Loader2, AlertTriangle, CheckCircle } from 'lucide-react';

interface ScriptAnalysis {
  success: boolean;
  txid?: string;
  input_count?: number;
  output_count?: number;
  inputs?: Array<{
    script_asm: string;
    script_hex: string;
    risk_hints: string[];
  }>;
  outputs?: Array<{
    n: number;
    type: string;
    risk_hints: string[];
  }>;
  message?: string;
}

interface BitcoinScriptWidgetProps {
  txid: string;
  onClose?: () => void;
}

export const BitcoinScriptWidget: React.FC<BitcoinScriptWidgetProps> = ({ txid, onClose }) => {
  const [analysis, setAnalysis] = useState<ScriptAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (txid) {
      analyzeScript();
    }
  }, [txid]);

  const analyzeScript = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/v1/bitcoin-script/analyze/${txid}`);
      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError('Failed to analyze script');
      console.error('Script analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="w-full max-w-md">
        <CardContent className="flex items-center justify-center p-6">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          Analyzing script...
        </CardContent>
      </Card>
    );
  }

  if (error || !analysis) {
    return (
      <Card className="w-full max-w-md">
        <CardContent className="p-6">
          <AlertTriangle className="h-6 w-6 text-red-500 mb-2" />
          <p className="text-sm text-red-700">{error || 'No analysis available'}</p>
        </CardContent>
      </Card>
    );
  }

  if (!analysis.success) {
    return (
      <Card className="w-full max-w-md">
        <CardContent className="p-6">
          <AlertTriangle className="h-6 w-6 text-yellow-500 mb-2" />
          <p className="text-sm">{analysis.message || 'Analysis failed'}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center text-lg">
          <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
          Bitcoin Script Analysis - {txid.slice(0, 16)}...
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <span className="text-sm font-medium">Inputs:</span>
            <span className="ml-2">{analysis.input_count || 0}</span>
          </div>
          <div>
            <span className="text-sm font-medium">Outputs:</span>
            <span className="ml-2">{analysis.output_count || 0}</span>
          </div>
        </div>

        {analysis.outputs && analysis.outputs.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium mb-2">Output Scripts:</h4>
            <div className="space-y-2">
              {analysis.outputs.map((out, idx) => (
                <div key={idx} className="border rounded p-2">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs font-mono">vout {out.n}</span>
                    <Badge variant={out.type === 'p2pkh' ? 'default' : 'secondary'}>
                      {out.type}
                    </Badge>
                  </div>
                  {out.risk_hints.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {out.risk_hints.map((hint, hidx) => (
                        <Badge key={hidx} variant="destructive" className="text-xs">
                          {hint}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {analysis.inputs && analysis.inputs.some(inp => inp.risk_hints.length > 0) && (
          <div>
            <h4 className="text-sm font-medium mb-2">Input Risks:</h4>
            <div className="space-y-1">
              {analysis.inputs.filter(inp => inp.risk_hints.length > 0).map((inp, idx) => (
                <div key={idx} className="text-xs text-red-600">
                  Input {idx}: {inp.risk_hints.join(', ')}
                </div>
              ))}
            </div>
          </div>
        )}

        {onClose && (
          <div className="mt-4 flex justify-end">
            <Button variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default BitcoinScriptWidget;
