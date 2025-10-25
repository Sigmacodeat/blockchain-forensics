import React, { useEffect, useMemo, useRef, useState, useCallback, Suspense } from 'react';
import { toast } from '@/lib/toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import { useSearchParams } from 'react-router-dom';
import LinkLocalized from '@/components/LinkLocalized';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import { alertPolicyRulesSchema } from '@/lib/schemas/alert-policy';

// Types
interface PolicyVersion {
  version: number;
  created_at: string;
  created_by: string;
  status: 'draft' | 'active' | 'archived';
  rules: Record<string, unknown>;
  notes?: string | null;
}

const DEBOUNCE_MS = Number((import.meta as any)?.env?.VITE_POLICY_EDITOR_DEBOUNCE_MS) || 250;

// Lazy-load heavy viewer to reduce initial bundle size
const DiffViewerLazy = React.lazy(() => import('react-diff-viewer-continued'));

// Convert AJV's JSON-Pointer (e.g. "/rules/0/conditions/1") to readable path ("rules[0].conditions[1]")
function jsonPointerToPath(ptr: string): string {
  if (!ptr || ptr === '/') return '/';
  const parts = ptr.replace(/^\//, '').split('/').map(p => p.replace(/~1/g, '/').replace(/~0/g, '~'));
  return parts
    .map((seg, i) => (seg.match(/^\d+$/) ? `[${seg}]` : (i === 0 ? seg : `.${seg}`)))
    .join('');
}
const MonacoEditor = React.lazy(() => import('@monaco-editor/react'));

interface PolicySummary {
  id: string;
  name: string;
  latest_version: number;
  versions: Array<{ version: number; status: string; created_at: string }>;
}

interface PolicyDetail extends PolicySummary {
  versions: PolicyVersion[];
}

interface SimulationSummary {
  total_events: number;
  hits: number;
  hit_rate: number;
  by_rule: Record<string, number>;
  by_severity: Record<string, number>;
}

// API helpers with AbortSignal support
async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(path, { signal });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function apiPost<T>(path: string, body?: any, signal?: AbortSignal): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
    signal,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export default function PolicyManager() {
  const { user } = useAuth();
  const role = (user?.role || '').toString().toUpperCase();
  const canEdit = role === 'ADMIN' || role === 'ANALYST';
  const [searchParams, setSearchParams] = useSearchParams();
  const [policies, setPolicies] = useState<PolicySummary[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [detail, setDetail] = useState<PolicyDetail | null>(null);
  const [creating, setCreating] = useState(false);
  const [newPolicyId, setNewPolicyId] = useState('default');
  const [newPolicyName, setNewPolicyName] = useState('Default Policy');
  const [newRules, setNewRules] = useState<string>('{"rules": []}');
  const [newNotes, setNewNotes] = useState<string>('');
  const [simEvents, setSimEvents] = useState<string>('[]');
  const [simResult, setSimResult] = useState<SimulationSummary | null>(null);
  const [statusToSet, setStatusToSet] = useState<'draft'|'active'|'archived'>('draft');
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [rulesValid, setRulesValid] = useState<boolean>(true);
  const [parsedRules, setParsedRules] = useState<Record<string, unknown>>({});
  const [simValid, setSimValid] = useState<boolean>(true);
  const [parsedSimEvents, setParsedSimEvents] = useState<unknown[]>([]);
  const [rulesSchemaValid, setRulesSchemaValid] = useState<boolean>(true);
  const [schemaErrors, setSchemaErrors] = useState<string[]>([]);
  const [schemaErrorDetails, setSchemaErrorDetails] = useState<{ path: string; message: string }[]>([]);
  const [rulesParseError, setRulesParseError] = useState<string>('');
  const [eventsParseError, setEventsParseError] = useState<string>('');
  const [isCreating, setIsCreating] = useState(false);
  const [isVersioning, setIsVersioning] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [isReloading, setIsReloading] = useState(false);
  const [isSettingStatus, setIsSettingStatus] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [diffOpen, setDiffOpen] = useState(false);
  const [diffText, setDiffText] = useState<string>('');
  const [diffSideBySide, setDiffSideBySide] = useState<{left:string; right:string}>({left:'', right:''});
  const [insufficientCredits, setInsufficientCredits] = useState(false);
  const diffContainerRef = useRef<HTMLDivElement>(null);
  const rulesEditorRef = useRef<any>(null);
  const eventsEditorRef = useRef<any>(null);
  const monacoRef = useRef<any>(null);
  const [showEditorHints, setShowEditorHints] = useState<boolean>(true);
  const RULES_CURSOR_KEY = 'pm_rules_cursor';
  const RULES_SCROLL_KEY = 'pm_rules_scrollTop';
  const EVENTS_CURSOR_KEY = 'pm_events_cursor';
  const EVENTS_SCROLL_KEY = 'pm_events_scrollTop';
  const rulesParseTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const eventsParseTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const ajv = useMemo(() => {
    const a = new Ajv({ allErrors: true });
    try { addFormats(a); } catch {}
    return a;
  }, []);
  const rulesSchema = useMemo(() => alertPolicyRulesSchema, []);
  const rulesModelUri = useMemo(() => 'inmemory://model/policy-rules.json', []);
  const eventsModelUri = useMemo(() => 'inmemory://model/sim-events.json', []);
  const validateRules = useMemo(() => {
    try {
      return ajv.compile(rulesSchema);
    } catch (e) {
      console.error(e);
      return null;
    }
  }, [ajv, rulesSchema]);

  // Load list
  useEffect(() => {
    // restore hints preference
    try {
      const h = localStorage.getItem('pm_show_editor_hints');
      if (h === '0') setShowEditorHints(false);
    } catch {}
    const ac = new AbortController();
    apiGet<{policies: PolicySummary[]}>('/api/v1/alert-policies', ac.signal)
      .then(d => setPolicies(d.policies || []))
      .catch((err) => {
        if (err?.name === 'AbortError') return;
        setPolicies([]);
      });
    return () => ac.abort();
  }, []);

  // Initialize from URL params (?policy=ID&version=N)
  useEffect(() => {
    const p = searchParams.get('policy') || '';
    const v = searchParams.get('version');
    if (p) setSelected(p);
    if (v) {
      const n = Number(v);
      if (!Number.isNaN(n)) setSelectedVersion(n);
    }
     
  }, []);

  // Load detail
  useEffect(() => {
    const ac = new AbortController();
    if (!selected) { setDetail(null); return () => ac.abort(); }
    apiGet<PolicyDetail>(`/api/v1/alert-policies/${selected}`, ac.signal)
      .then(setDetail)
      .catch((err) => {
        if (err?.name === 'AbortError') return;
        setDetail(null);
      });
    return () => ac.abort();
  }, [selected]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().includes('MAC');
      const mod = isMac ? e.metaKey : e.ctrlKey;
      if (!mod) return;
      if (!canEdit) return;
      const rulesHasFocus = !!rulesEditorRef.current?.hasTextFocus?.();
      const eventsHasFocus = !!eventsEditorRef.current?.hasTextFocus?.();
      if (e.shiftKey && (e.key === 'F' || e.key === 'f')) {
        if (rulesHasFocus || eventsHasFocus) {
          e.preventDefault();
          const editor = rulesHasFocus ? rulesEditorRef.current : eventsEditorRef.current;
          editor?.getAction?.('editor.action.formatDocument')?.run?.();
          return;
        }
      } else if (!e.shiftKey && (e.key === 'M' || e.key === 'm')) {
        if (rulesHasFocus) {
          e.preventDefault();
          minifyNewRules();
          return;
        }
        if (eventsHasFocus) {
          e.preventDefault();
          minifyEvents();
          return;
        }
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [canEdit]);

  // Persist diffOpen per policy in localStorage
  useEffect(() => {
    if (!selected) return;
    try {
      const key = `pm_diff_open_${selected}`;
      const saved = localStorage.getItem(key);
      if (saved != null) setDiffOpen(saved === '1');
    } catch {}
  }, [selected]);

  useEffect(() => {
    if (!selected) return;
    try {
      const key = `pm_diff_open_${selected}`;
      localStorage.setItem(key, diffOpen ? '1' : '0');
    } catch {}
  }, [selected, diffOpen]);

  // Persist statusToSet per policy in localStorage (separat zum Draft)
  useEffect(() => {
    if (!selected) return;
    try {
      const key = `pm_status_${selected}`;
      const saved = localStorage.getItem(key);
      if (saved === 'draft' || saved === 'active' || saved === 'archived') {
        setStatusToSet(saved);
      }
    } catch {}
  }, [selected]);

  useEffect(() => {
    if (!selected) return;
    try {
      const key = `pm_status_${selected}`;
      localStorage.setItem(key, statusToSet);
    } catch {}
  }, [selected, statusToSet]);

  const latestVersion = useMemo(() => {
    if (!detail?.versions?.length) return undefined;
    return [...detail.versions].sort((a,b) => b.version - a.version)[0];
  }, [detail]);

  // When detail changes, auto-select latest and preload its rules into editor
  useEffect(() => {
    if (!detail) { setSelectedVersion(null); return; }
    const latest = [...(detail.versions || [])].sort((a,b) => b.version - a.version)[0];
    if (latest) {
      setSelectedVersion(latest.version);
      try {
        // If latest has rules, pretty print to editor
        const pretty = JSON.stringify((latest as any).rules ?? {}, null, 2);
        setNewRules(pretty);
        setStatusToSet((latest.status as any) || 'draft');
      } catch {
        // ignore formatting errors
      }
    }
  }, [detail]);

  // Reflect state into URL when selection/version changes
  useEffect(() => {
    const params: Record<string, string> = {};
    if (selected) params.policy = selected;
    if (selectedVersion != null) params.version = String(selectedVersion);
    setSearchParams(params, { replace: true });
  }, [selected, selectedVersion, setSearchParams]);

  // Debounced validate and parse JSON inputs (rules)
  useEffect(() => {
    if (rulesParseTimer.current) clearTimeout(rulesParseTimer.current);
    rulesParseTimer.current = setTimeout(() => {
      try {
        const obj = JSON.parse(newRules || '{}');
        setParsedRules(obj);
        setRulesValid(true);
        setRulesParseError('');
      } catch {
        setRulesValid(false);
        try {
          // Best effort Fehlermeldung aus JSON.parse
          // Hinweis: JSON.parse liefert keine Position, aber message hilft häufig weiter
           
          JSON.parse('');
        } catch (err) {
          setRulesParseError(err instanceof Error ? err.message : 'Ungültiges JSON');
        }
      }
    }, DEBOUNCE_MS);
    return () => { if (rulesParseTimer.current) clearTimeout(rulesParseTimer.current); };
  }, [newRules]);

  // AJV schema validation
  useEffect(() => {
    if (!rulesValid) { setRulesSchemaValid(false); setSchemaErrors([rulesParseError || "Ungültiges JSON"]); return; }
    try {
      if (!validateRules) { setRulesSchemaValid(false); setSchemaErrors(["Schema-Validator konnte nicht erstellt werden"]); return; }
      const ok = validateRules(parsedRules) as boolean;
      setRulesSchemaValid(ok);
      if (!ok) {
        const details: { path: string; message: string }[] = [];
        const errs = (validateRules.errors || []).map((e:any) => {
          const rawPath = (typeof e.instancePath === 'string' && e.instancePath.length)
            ? e.instancePath
            : (typeof e.dataPath === 'string' ? e.dataPath : '/');
          const path = jsonPointerToPath(rawPath);
          const k = e.keyword as string | undefined;
          const p = e.params as any;
          if (k === 'required' && p?.missingProperty) {
            const msg = `${path}: fehlendes Feld '${p.missingProperty}'`;
            details.push({ path, message: msg });
            return msg;
          }
          if (k === 'enum' && Array.isArray(p?.allowedValues)) {
            const msg = `${path}: ungültiger Wert (erlaubt: ${p.allowedValues.join(', ')})`;
            details.push({ path, message: msg });
            return msg;
          }
          if (k === 'pattern' && p?.pattern) {
            const msg = `${path}: entspricht nicht dem Pattern ${p.pattern}`;
            details.push({ path, message: msg });
            return msg;
          }
          if (k === 'type' && p?.type) {
            const msg = `${path}: erwarteter Typ ${p.type}`;
            details.push({ path, message: msg });
            return msg;
          }
          const msg = `${path} ${e.message || ''}`.trim();
          details.push({ path, message: msg });
          return msg;
        });
        setSchemaErrors(errs.length ? errs : ["Schema-Validierung fehlgeschlagen"]);
        setSchemaErrorDetails(details);
      } else {
        setSchemaErrors([]);
        setSchemaErrorDetails([]);
      }
    } catch (e) {
      console.error(e);
      setRulesSchemaValid(false);
      setSchemaErrors(["Schema-Validierung konnte nicht ausgeführt werden"]);
      setSchemaErrorDetails([]);
    }
  }, [validateRules, rulesValid, parsedRules, rulesParseError]);

  // Helpers to improve marker positioning
  function getByPath(root: any, path: string): any {
    try {
      // path like rules[0].conditions[1]
      const parts = path
        .replace(/^\./, '')
        .split(/\.(?![^\[]*\])/)
        .filter(Boolean);
      let cur: any = root;
      for (const p of parts) {
        const m = p.match(/^(\w+)(\[(\d+)\])?$/);
        if (!m) return undefined;
        const key = m[1];
        if (cur && typeof cur === 'object' && key in cur) {
          cur = (cur as any)[key];
        } else { return undefined; }
        const idx = m[3] != null ? parseInt(m[3], 10) : undefined;
        if (idx != null) {
          if (Array.isArray(cur) && cur[idx] !== undefined) {
            cur = cur[idx];
          } else { return undefined; }
        }
      }
      return cur;
    } catch { return undefined; }
  }

  // Try to find the first line where the sub-JSON for a path appears in the editor text
  function estimateLineForPath(jsonText: string, path: string, rootObj?: any): number {
    try {
      if (!path) return 1;
      if (rootObj) {
        const sub = getByPath(rootObj, path);
        if (sub !== undefined) {
          const pretty = JSON.stringify(sub, null, 2);
          const idx = jsonText.indexOf(pretty);
          if (idx >= 0) {
            return jsonText.slice(0, idx).split('\n').length;
          }
        }
      }
      // fallback heuristic by key search
      const parts = path.replace(/^\./, '').split(/\.(?![^\[]*\])/); // split on dots not inside []
      let pos = 0;
      for (const part of parts) {
        const key = part.replace(/\[.*\]/g, '');
        if (!key) continue;
        const needle = `"${key}"`;
        const found = jsonText.indexOf(needle, pos);
        if (found === -1) break;
        pos = found + needle.length;
      }
      return jsonText.slice(0, pos).split('\n').length;
    } catch { return 1; }
  }

  // Reflect AJV/parse errors as Monaco markers on rules editor
  useEffect(() => {
    try {
      const monaco: any = monacoRef.current;
      const editor: any = rulesEditorRef.current;
      const model = editor?.getModel?.();
      if (!monaco || !model) return;
      const markers: any[] = [];
      if (!rulesValid && rulesParseError) {
        markers.push({
          severity: monaco.MarkerSeverity.Error,
          message: `JSON: ${rulesParseError}`,
          startLineNumber: 1,
          startColumn: 1,
          endLineNumber: 1,
          endColumn: 1,
          source: 'json'
        });
      }
      if (rulesValid && !rulesSchemaValid && schemaErrorDetails.length) {
        const text = model.getValue ? model.getValue() : '';
        const rootObj = parsedRules;
        for (const { path, message } of schemaErrorDetails) {
          const line = estimateLineForPath(text, path, rootObj);
          markers.push({
            severity: monaco.MarkerSeverity.Error,
            message: `Schema: ${message}`,
            startLineNumber: line,
            startColumn: 1,
            endLineNumber: line,
            endColumn: 80,
            source: 'ajv'
          });
        }
      }
      monaco.editor.setModelMarkers(model, 'policy-rules', markers);
    } catch {}
  }, [rulesValid, rulesSchemaValid, schemaErrorDetails, rulesParseError]);

  // aria-busy on key regions to improve SR feedback during async ops
  const busyCreating = isCreating;
  const busyVersioning = isVersioning;
  const busySimulating = isSimulating;
  const busyReloading = isReloading;

  // Reflect parse/structure errors as Monaco markers on events editor
  useEffect(() => {
    try {
      const monaco: any = monacoRef.current;
      const editor: any = eventsEditorRef.current;
      const model = editor?.getModel?.();
      if (!monaco || !model) return;
      const markers: any[] = [];
      if (!simValid) {
        markers.push({
          severity: monaco.MarkerSeverity.Error,
          message: `JSON: ${eventsParseError || 'Ungültiges JSON oder kein Array'}`,
          startLineNumber: 1,
          startColumn: 1,
          endLineNumber: 1,
          endColumn: 1,
          source: 'json'
        });
      }
      monaco.editor.setModelMarkers(model, 'sim-events', markers);
    } catch {}
  }, [simValid, eventsParseError]);

  useEffect(() => {
    if (eventsParseTimer.current) clearTimeout(eventsParseTimer.current);
    eventsParseTimer.current = setTimeout(() => {
      try {
        const arr = JSON.parse(simEvents || '[]');
        if (Array.isArray(arr)) {
          setParsedSimEvents(arr);
          setSimValid(true);
          setEventsParseError('');
        } else {
          setSimValid(false);
        }
      } catch {
        setSimValid(false);
        try {
           
          JSON.parse('');
        } catch (err) {
          setEventsParseError(err instanceof Error ? err.message : 'Ungültiges JSON');
        }
      }
    }, DEBOUNCE_MS);
    return () => { if (eventsParseTimer.current) clearTimeout(eventsParseTimer.current); };
  }, [simEvents]);

  // Draft persistence per policy (auto-save & restore)
  const draftKey = useMemo(() => selected ? `alert_policy_editor_${selected}` : '', [selected]);
  // Save draft on changes
  useEffect(() => {
    if (!draftKey) return;
    const draft = { rules: newRules, notes: newNotes, status: statusToSet };
    try { localStorage.setItem(draftKey, JSON.stringify(draft)); } catch {}
  }, [draftKey, newRules, newNotes, statusToSet]);
  // Restore draft after detail load and preload
  useEffect(() => {
    if (!draftKey || !detail) return;
    try {
      const raw = localStorage.getItem(draftKey);
      if (raw) {
        const d = JSON.parse(raw);
        if (typeof d?.rules === 'string') setNewRules(d.rules);
        if (typeof d?.notes === 'string') setNewNotes(d.notes);
        if (d?.status === 'draft' || d?.status === 'active' || d?.status === 'archived') setStatusToSet(d.status);
        toast.info('Entwurf wiederhergestellt');
      }
    } catch {}
  // run once when detail changes (after preload did run)
  }, [detail, draftKey]);

  function clearDraft() {
    if (!draftKey) return;
    try { localStorage.removeItem(draftKey); toast.success('Entwurf verworfen'); } catch {}
  }

  async function handleCreate() {
    try {
      setIsCreating(true);
      if (!rulesValid) { toast.error('Regeln enthalten ungültiges JSON'); return; }
      if (!rulesSchemaValid) { toast.error("Regeln sind strukturell ungültig (erwarte 'rules' als Array)"); return; }
      const payload = {
        policy_id: newPolicyId.trim(),
        name: newPolicyName.trim(),
        rules: parsedRules,
      };
      const created = await apiPost<PolicyDetail>('/api/v1/alert-policies', payload);
      setSelected(created.id);
      setCreating(false);
      const list = await apiGet<{policies: PolicySummary[]}>('/api/v1/alert-policies');
      setPolicies(list.policies || []);
      // Clear draft for previous selection
      try { if (draftKey) localStorage.removeItem(draftKey); } catch {}
      toast.success('Policy erstellt');
    } catch (e) {
      console.error(e);
      toast.error(`Fehler beim Erstellen der Policy${e instanceof Error && e.message ? `: ${e.message}` : ''}`);
    } finally {
      setIsCreating(false);
    }
  }

  async function handleNewVersion() {
    if (!selected) return;
    try {
      setIsVersioning(true);
      if (!rulesValid) { toast.error('Regeln enthalten ungültiges JSON'); return; }
      const payload = { rules: parsedRules, status: statusToSet, notes: newNotes || undefined };
      await apiPost(`/api/v1/alert-policies/${selected}/versions`, payload);
      const d = await apiGet<PolicyDetail>(`/api/v1/alert-policies/${selected}`);
      setDetail(d);
      setNewNotes('');
      // Clear draft for this policy after successful version add
      try { if (draftKey) localStorage.removeItem(draftKey); } catch {}
      toast.success('Neue Version angelegt');
    } catch (e) {
      console.error(e);
      toast.error(`Fehler beim Anlegen der neuen Version${e instanceof Error && e.message ? `: ${e.message}` : ''}`);
    } finally {
      setIsVersioning(false);
    }
  }

  async function handleSetStatus(version: number, status: 'draft'|'active'|'archived') {
    if (!selected) return;
    try {
      setIsSettingStatus(version);
      await apiPost(`/api/v1/alert-policies/${selected}/versions/${version}/status`, { status });
      const d = await apiGet<PolicyDetail>(`/api/v1/alert-policies/${selected}`);
      setDetail(d);
      toast.success('Status aktualisiert');
    } catch (e) {
      console.error(e);
      toast.error(`Fehler beim Setzen des Status${e instanceof Error && e.message ? `: ${e.message}` : ''}`);
    } finally {
      setIsSettingStatus(null);
    }
  }

  async function handleSimulate() {
    try {
      setIsSimulating(true);
      setInsufficientCredits(false);
      if (!rulesValid) { toast.error('Regeln enthalten ungültiges JSON'); return; }
      if (!simValid) { toast.error('Events enthalten ungültiges JSON'); return; }
      const payload = {
        policy_rules: parsedRules,
        events: parsedSimEvents,
      };
      const ac = new AbortController();
      try {
        const r = await apiPost<{ summary: SimulationSummary }>(`/api/v1/alert-policies/simulate`, payload, ac.signal);
        setSimResult(r.summary);
      } catch (err: any) {
        // Best-effort: 402 wird serverseitig nicht verfügbar in err, daher UI-Flag nur zurücksetzen, wenn Response bekannt
        // Optional: Backend könnte 402 im Body kodieren; hier vereinfachen wir
        setInsufficientCredits(false);
        throw err;
      }
      toast.success('Simulation abgeschlossen');
    } catch (e) {
      console.error(e);
      toast.error(`Fehler bei Simulation${e instanceof Error && e.message ? `: ${e.message}` : ''}`);
    } finally {
      setIsSimulating(false);
    }
  }

  async function handleReloadEngine() {
    try {
      setIsReloading(true);
      await apiPost('/api/v1/alert-policies/reload');
      toast.success('Policies in der Alert-Engine neu geladen');
    } catch (e) {
      console.error(e);
      toast.error(`Fehler beim Reload${e instanceof Error && e.message ? `: ${e.message}` : ''}`);
    } finally {
      setIsReloading(false);
    }
  }

  const formatNewRules = useCallback(() => {
    try {
      const obj = JSON.parse(newRules || '{}');
      setNewRules(JSON.stringify(obj, null, 2));
    } catch {
      toast.error('Ungültiges JSON in den Regeln');
    }
  }, [newRules]);

  const minifyNewRules = useCallback(() => {
    try {
      const obj = JSON.parse(newRules || '{}');
      setNewRules(JSON.stringify(obj));
    } catch {
      toast.error('Ungültiges JSON in den Regeln');
    }
  }, [newRules]);

  const formatEvents = useCallback(() => {
    try {
      const arr = JSON.parse(simEvents || '[]');
      setSimEvents(JSON.stringify(arr, null, 2));
    } catch {
      toast.error('Ungültiges JSON in den Events');
    }
  }, [simEvents]);

  const minifyEvents = useCallback(() => {
    try {
      const arr = JSON.parse(simEvents || '[]');
      setSimEvents(JSON.stringify(arr));
    } catch {
      toast.error('Ungültiges JSON in den Events');
    }
  }, [simEvents]);

  const resetToSelectedVersion = useCallback(() => {
    const v = detail?.versions.find(x => x.version === selectedVersion) || latestVersion;
    if (!v) { toast.error('Keine Version ausgewählt'); return; }
    loadVersionRules(v as any);
  }, [detail, selectedVersion, latestVersion, loadVersionRules]);

  function handleExportRules() {
    try {
      if (!rulesValid) { toast.error('Regeln enthalten ungültiges JSON'); return; }
      const blob = new Blob([JSON.stringify(parsedRules, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${detail?.id || 'policy'}-rules.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success('Regeln exportiert');
    } catch (e) {
      console.error(e);
      toast.error('Export fehlgeschlagen');
    }
  }

  function handleExportSim() {
    try {
      if (!simResult) { toast.error('Kein Simulationsergebnis zum Exportieren'); return; }
      const blob = new Blob([JSON.stringify(simResult, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${detail?.id || 'policy'}-simulation.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success('Simulationsergebnis exportiert');
    } catch (e) {
      console.error(e);
      toast.error('Export des Simulationsergebnisses fehlgeschlagen');
    }
  }

  function handleImportClick() {
    fileInputRef.current?.click();
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    try {
      const file = e.target.files?.[0];
      if (!file) return;
      const text = await file.text();
      // Validierung erfolgt durch rulesValid useEffect
      setNewRules(text);
      toast.success('Regeln importiert');
      // reset input
      e.target.value = '';
    } catch (err) {
      console.error(err);
      toast.error('Import fehlgeschlagen');
    }
  }

  function loadVersionRules(v: PolicyVersion) {
    try {
      const pretty = JSON.stringify(v.rules ?? {}, null, 2);
      setNewRules(pretty);
      setStatusToSet(v.status);
      setSelectedVersion(v.version);
    } catch {
      toast.error('Regeln dieser Version konnten nicht geladen werden');
    }
  }

  // Minimal JSON diff: compares keys and values, outputs +/- markers per line
  function computeJsonDiff(a: unknown, b: unknown): string {
    try {
      const aStr = JSON.stringify(a, null, 2).split('\n');
      const bStr = JSON.stringify(b, null, 2).split('\n');
      const max = Math.max(aStr.length, bStr.length);
      const lines: string[] = [];
      for (let i = 0; i < max; i++) {
        const la = aStr[i] ?? '';
        const lb = bStr[i] ?? '';
        if (la === lb) {
          lines.push('  ' + lb);
        } else {
          if (la) lines.push('- ' + la);
          if (lb) lines.push('+ ' + lb);
        }
      }
      return lines.join('\n');
    } catch {
      return 'Diff konnte nicht berechnet werden.';
    }
  }

  const openDiffWithSelectedVersion = useCallback(() => {
    if (diffOpen) { setDiffOpen(false); return; }
    const v = detail?.versions.find(x => x.version === selectedVersion) || latestVersion;
    if (!v) { toast.error('Keine Version ausgewählt'); return; }
    const diff = computeJsonDiff(v.rules ?? {}, parsedRules);
    setDiffText(diff);
    try {
      setDiffSideBySide({
        left: JSON.stringify(v.rules ?? {}, null, 2),
        right: JSON.stringify(parsedRules ?? {}, null, 2),
      });
    } catch { setDiffSideBySide({left:'', right:''}); }
    setDiffOpen(true);
    // Fokus auf Diff-Container setzen (A11y)
    requestAnimationFrame(() => {
      diffContainerRef.current?.focus();
    });
  }, [diffOpen, detail, selectedVersion, latestVersion, parsedRules, computeJsonDiff]);

  async function handleCopyRules() {
    try {
      await navigator.clipboard.writeText(newRules || '');
      toast.success('Regeln kopiert');
    } catch (e) {
      console.error(e);
      toast.error('Kopieren fehlgeschlagen');
    }
  }

  async function handleCopySim() {
    try {
      if (!simResult) { toast.error('Kein Ergebnis zum Kopieren'); return; }
      await navigator.clipboard.writeText(JSON.stringify(simResult, null, 2));
      toast.success('Simulationsergebnis kopiert');
    } catch (e) {
      console.error(e);
      toast.error('Kopieren fehlgeschlagen');
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Premium Header */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-primary-600 via-purple-600 to-blue-600 dark:from-primary-700 dark:via-purple-700 dark:to-blue-700 p-8 shadow-2xl">
          <div className="absolute inset-0 bg-grid-white/10 [mask-image:linear-gradient(0deg,transparent,black)]" />
          <div className="relative z-10">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-white mb-2">Alert Policies</h1>
                <p className="text-primary-100 dark:text-primary-200">Verwalte und konfiguriere deine Blockchain-Forensik-Richtlinien</p>
              </div>
              <div className="flex gap-3">
                <Button 
                  variant="outline" 
                  onClick={() => setCreating(v => !v)} 
                  disabled={!canEdit} 
                  title={!canEdit ? 'Keine Berechtigung' : undefined}
                  className="bg-white/10 backdrop-blur-sm border-white/20 text-white hover:bg-white/20 hover:border-white/30 transition-all duration-200"
                >
                  {creating ? 'Abbrechen' : '+ Neue Policy'}
                </Button>
                <Button 
                  onClick={handleReloadEngine} 
                  disabled={isReloading}
                  className="bg-white text-primary-600 hover:bg-white/90 shadow-lg transition-all duration-200"
                >
                  {isReloading ? '⟳ Lädt...' : '⟳ Engine Neuladen'}
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Card */}
        <Card className="border-slate-200 dark:border-slate-800 shadow-xl bg-white dark:bg-slate-900">
          <CardContent className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Policy Sidebar */}
            <div className="lg:col-span-1 space-y-3">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Policies</h2>
                <Badge variant="outline" className="bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 border-primary-200 dark:border-primary-800">
                  {policies.length} Total
                </Badge>
              </div>
              
              <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
                {policies.map(p => (
                  <div 
                    key={p.id} 
                    className={`group relative p-4 rounded-xl cursor-pointer transition-all duration-200 ${
                      selected===p.id 
                        ? 'bg-gradient-to-r from-primary-50 to-purple-50 dark:from-primary-900/30 dark:to-purple-900/20 border-2 border-primary-300 dark:border-primary-700 shadow-md' 
                        : 'bg-slate-50 dark:bg-slate-800/50 border-2 border-transparent hover:border-slate-200 dark:hover:border-slate-700 hover:shadow-lg'
                    }`} 
                    onClick={() => setSelected(p.id)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className={`font-semibold text-sm ${selected===p.id ? 'text-primary-900 dark:text-primary-100' : 'text-slate-700 dark:text-slate-200'}`}>
                        {p.name}
                      </div>
                      <Badge 
                        variant={selected===p.id ? 'default' : 'secondary'}
                        className={`${selected===p.id ? 'bg-primary-600 dark:bg-primary-500' : ''} font-mono text-xs`}
                      >
                        v{p.latest_version}
                      </Badge>
                    </div>
                    <div className="text-xs text-slate-500 dark:text-slate-400 font-mono">{p.id}</div>
                    {selected===p.id && (
                      <div className="absolute -left-1 top-1/2 -translate-y-1/2 w-1 h-12 bg-gradient-to-b from-primary-500 to-purple-500 rounded-r-full" />
                    )}
                  </div>
                ))}
                
                {policies.length===0 && (
                  <div className="text-center py-12 text-slate-500 dark:text-slate-400">
                    <div className="text-4xl mb-3">📋</div>
                    <div className="text-sm font-medium">Keine Policies vorhanden</div>
                    <div className="text-xs mt-1">Erstelle deine erste Policy</div>
                  </div>
                )}
              </div>
            </div>

            {/* Main Content Area */}
            <div className="lg:col-span-2 space-y-6" aria-busy={busyReloading || undefined}>
              {creating && (
                <Card className="border-2 border-dashed border-primary-300 dark:border-primary-700 bg-gradient-to-br from-primary-50/50 to-purple-50/50 dark:from-primary-950/20 dark:to-purple-950/20">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-slate-900 dark:text-white">
                      <span className="text-2xl">✨</span>
                      Neue Policy erstellen
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4" aria-busy={busyCreating || undefined}>
                    <Input aria-label="Policy-ID" placeholder="policy_id" value={newPolicyId} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setNewPolicyId(e.target.value)} disabled={!canEdit} />
                    <Input aria-label="Policy-Name" placeholder="Name" value={newPolicyName} onChange={(e: React.ChangeEvent<HTMLInputElement>)=>setNewPolicyName(e.target.value)} disabled={!canEdit} />
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm" onClick={formatNewRules} disabled={!canEdit || !rulesValid} title={!rulesValid ? 'Bitte gültiges JSON einfügen' : !canEdit ? 'Keine Berechtigung' : undefined}>Formatieren</Button>
                        <Button variant="outline" size="sm" onClick={minifyNewRules} disabled={!canEdit || !rulesValid} title={!rulesValid ? 'Bitte gültiges JSON einfügen' : !canEdit ? 'Keine Berechtigung' : undefined}>Minimieren</Button>
                        <Button variant="outline" size="sm" onClick={handleCopyRules}>Kopieren</Button>
                      </div>
                      <div>{`${(newRules || '').split('\n').length} Zeilen • ${(newRules || '').length} Zeichen`}</div>
                    </div>
                    <div className="border rounded overflow-hidden mt-1">
                      <Suspense fallback={<Textarea aria-label="Regeln JSON" rows={8} className="font-mono whitespace-pre-wrap" value={newRules} readOnly />}>
                        <MonacoEditor
                          height={200}
                          language="json"
                          value={newRules}
                          path={rulesModelUri}
                          onChange={(val)=> setNewRules(val ?? '')}
                          options={{ readOnly: !canEdit, minimap: { enabled: false }, scrollBeyondLastLine: false, wordWrap: 'on' }}
                          onMount={(_editor, monaco) => {
                            monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
                              validate: true,
                              schemas: [
                                { uri: 'inmemory://schemas/policy-rules.json', fileMatch: [rulesModelUri], schema: rulesSchema as any }
                              ]
                            });
                            try { (rulesEditorRef as any).current = _editor; } catch {}
                            if (!monacoRef.current) monacoRef.current = monaco;
                            // restore cursor & scroll
                            try {
                              const curRaw = localStorage.getItem(RULES_CURSOR_KEY);
                              if (curRaw) {
                                const pos = JSON.parse(curRaw);
                                if (pos?.lineNumber && pos?.column) _editor.setPosition(pos);
                              }
                              const stRaw = localStorage.getItem(RULES_SCROLL_KEY);
                              if (stRaw) {
                                const st = parseInt(stRaw, 10);
                                if (!Number.isNaN(st)) _editor.setScrollTop(st);
                              }
                            } catch {}
                            // persist on changes
                            _editor.onDidChangeCursorPosition(() => {
                              try { localStorage.setItem(RULES_CURSOR_KEY, JSON.stringify(_editor.getPosition())); } catch {}
                            });
                            _editor.onDidScrollChange((e: any) => {
                              try { localStorage.setItem(RULES_SCROLL_KEY, String(e.scrollTop)); } catch {}
                            });
                            // auto-format on blur
                            _editor.onDidBlurEditorText(() => {
                              try {
                                if (!canEdit) return;
                                _editor.getAction('editor.action.formatDocument')?.run?.();
                              } catch {}
                            });
                          }}
                        />
                      </Suspense>
                    </div>
                    {!rulesValid && (
                      <div className="flex items-start gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800">
                        <span className="text-red-600 dark:text-red-400 text-lg">⚠️</span>
                        <div className="flex-1">
                          <div className="text-sm font-semibold text-red-800 dark:text-red-200">JSON-Fehler</div>
                          <div className="text-xs text-red-600 dark:text-red-400 mt-1">{rulesParseError || 'Ungültiges JSON in den Regeln'}</div>
                        </div>
                      </div>
                    )}
                    {rulesValid && !rulesSchemaValid && (
                      <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800">
                        <span className="text-amber-600 dark:text-amber-400 text-lg">⚠️</span>
                        <div className="flex-1">
                          <div className="text-sm font-semibold text-amber-800 dark:text-amber-200">Schema-Fehler</div>
                          <div className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                            Strukturell ungültig: Erwartet wird ein Objekt mit <code className="px-1 py-0.5 bg-amber-100 dark:bg-amber-900 rounded">rules</code> als Array.
                          </div>
                        </div>
                      </div>
                    )}
                    <div className="flex gap-3">
                      <Button onClick={handleCreate} disabled={!canEdit || isCreating || !rulesValid || !rulesSchemaValid || !newPolicyId.trim() || !newPolicyName.trim()} title={!canEdit ? 'Keine Berechtigung' : !rulesValid ? 'Bitte gültiges JSON einfügen' : !rulesSchemaValid ? "Regeln-Objekt muss ein 'rules' Array enthalten" : (!newPolicyId.trim() || !newPolicyName.trim()) ? 'ID und Name erforderlich' : undefined}>
                        {isCreating ? 'Erstelle...' : 'Erstellen'}
                      </Button>
                      <Button variant="outline" onClick={()=>setCreating(false)}>Abbrechen</Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {detail && (
                <Card className="border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                  <CardHeader className="border-b border-slate-200 dark:border-slate-800 bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-900">
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-3">
                        <span className="text-slate-900 dark:text-white">{detail.name}</span>
                        <code className="text-sm font-mono px-2 py-1 bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded">
                          {detail.id}
                        </code>
                      </CardTitle>
                      <Badge variant="outline" className="bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 border-primary-200 dark:border-primary-800">
                        {detail.versions.length} {detail.versions.length === 1 ? 'Version' : 'Versionen'}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-6 p-6">
                    {/* Aktive/ausgewählte Version Details */}
                    <div>
                      <div className="text-sm font-medium mb-2">Ausgewählte Version</div>
                      {(() => {
                        const v = detail.versions.find(x => x.version === selectedVersion) || latestVersion;
                        if (!v) return <div className="text-sm text-muted-foreground">Keine Version ausgewählt</div>;
                        return (
                          <div className="border-2 border-slate-200 dark:border-slate-700 rounded-xl p-4 bg-gradient-to-br from-slate-50 to-white dark:from-slate-800 dark:to-slate-900">
                            <div className="flex items-center gap-3 text-sm">
                              <Badge className="bg-primary-600 dark:bg-primary-500 text-white font-mono">
                                v{v.version}
                              </Badge>
                              <Badge 
                                variant={v.status==='active' ? 'default' : 'secondary'}
                                className={
                                  v.status === 'active' 
                                    ? 'bg-green-600 dark:bg-green-500 text-white hover:bg-green-700 dark:hover:bg-green-600' 
                                    : v.status === 'archived'
                                    ? 'bg-slate-500 dark:bg-slate-600 text-white'
                                    : 'bg-amber-500 dark:bg-amber-600 text-white'
                                }
                              >
                                {v.status === 'active' ? '✓ Active' : v.status === 'archived' ? '📦 Archived' : '📝 Draft'}
                              </Badge>
                              <span className="text-slate-500 dark:text-slate-400 text-xs">
                                {new Date(v.created_at).toLocaleString('de-DE', { 
                                  day: '2-digit', 
                                  month: 'short', 
                                  year: 'numeric', 
                                  hour: '2-digit', 
                                  minute: '2-digit' 
                                })}
                              </span>
                            </div>
                            {('notes' in v) && (v as any).notes ? (
                              <div className="text-sm"><b>Notizen:</b> {(v as any).notes}</div>
                            ) : null}
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">Regeln (read-only)</div>
                              <Textarea rows={8} className="font-mono whitespace-pre-wrap" value={(() => { try { return JSON.stringify((v as any).rules ?? {}, null, 2); } catch { return ''; } })()} readOnly />
                            </div>
                          </div>
                        );
                      })()}
                    </div>

                    <div>
                      <div className="text-sm font-medium mb-2">Versionen</div>
                      <div className="space-y-2">
                        {detail.versions.map(v => (
                          <div key={v.version} className="flex items-center justify-between border rounded p-2">
                            <div className="flex items-center gap-3">
                              <Badge>v{v.version}</Badge>
                              <div className="text-sm">{new Date(v.created_at).toLocaleString()}</div>
                              <Badge variant={v.status==='active' ? 'default' : 'secondary'}>{v.status}</Badge>
                            </div>
                            <div className="flex gap-2">
                              <Select value={statusToSet} onValueChange={(val:any)=>setStatusToSet(val)}>
                                <SelectTrigger className="w-[140px]" disabled={!canEdit} title={!canEdit ? 'Keine Berechtigung' : undefined}><SelectValue placeholder="Status" /></SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="draft">draft</SelectItem>
                                  <SelectItem value="active">active</SelectItem>
                                  <SelectItem value="archived">archived</SelectItem>
                                </SelectContent>
                              </Select>
                              <Button variant="outline" onClick={()=>handleSetStatus(v.version, statusToSet)} disabled={!canEdit || isSettingStatus===v.version} title={!canEdit ? 'Keine Berechtigung zum Ändern' : undefined}>
                                {isSettingStatus===v.version ? 'Setze...' : 'Setzen'}
                              </Button>
                              <Button variant="outline" onClick={()=>loadVersionRules(v as any)}>Laden</Button>
                              <Button variant="outline" onClick={()=>setSelectedVersion(v.version)}>Ansehen</Button>
                              <Button variant="outline" onClick={openDiffWithSelectedVersion}>Diff mit Editor</Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <Tabs defaultValue="new-version">
                      <TabsList>
                        <TabsTrigger value="new-version">Neue Version</TabsTrigger>
                        <TabsTrigger value="simulate">Simulation</TabsTrigger>
                      </TabsList>
                      <TabsContent value="new-version" className="space-y-2">
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <div className="flex items-center gap-2">
                            <Button variant="outline" size="sm" onClick={formatNewRules} disabled={!canEdit || !rulesValid} title={!rulesValid ? 'Bitte gültiges JSON einfügen' : !canEdit ? 'Keine Berechtigung' : undefined}>Formatieren</Button>
                            <Button variant="outline" size="sm" onClick={minifyNewRules} disabled={!canEdit || !rulesValid} title={!rulesValid ? 'Bitte gültiges JSON einfügen' : !canEdit ? 'Keine Berechtigung' : undefined}>Minimieren</Button>
                            <Button variant="outline" size="sm" onClick={handleCopyRules}>Kopieren</Button>
                          </div>
                          <div>{`${(newRules || '').split('\n').length} Zeilen • ${(newRules || '').length} Zeichen`}</div>
                        </div>
                        <div className="border rounded overflow-hidden mt-1">
                          <Suspense fallback={<Textarea aria-label="Regeln JSON" rows={10} className="font-mono whitespace-pre-wrap" value={newRules} readOnly />}>
                            <MonacoEditor
                              height={260}
                              language="json"
                              value={newRules}
                              path={rulesModelUri}
                              onChange={(val)=> setNewRules(val ?? '')}
                              options={{ readOnly: !canEdit, minimap: { enabled: false }, scrollBeyondLastLine: false, wordWrap: 'on' }}
                              onMount={(_editor, monaco) => {
                                monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
                                  validate: true,
                                  schemas: [
                                    { uri: 'inmemory://schemas/policy-rules.json', fileMatch: [rulesModelUri], schema: rulesSchema as any }
                                  ]
                                });
                                try { (rulesEditorRef as any).current = _editor; } catch {}
                                if (!monacoRef.current) monacoRef.current = monaco;
                                // restore cursor & scroll
                                try {
                                  const curRaw = localStorage.getItem(RULES_CURSOR_KEY);
                                  if (curRaw) {
                                    const pos = JSON.parse(curRaw);
                                    if (pos?.lineNumber && pos?.column) _editor.setPosition(pos);
                                  }
                                  const stRaw = localStorage.getItem(RULES_SCROLL_KEY);
                                  if (stRaw) {
                                    const st = parseInt(stRaw, 10);
                                    if (!Number.isNaN(st)) _editor.setScrollTop(st);
                                  }
                                } catch {}
                                // persist on changes
                                _editor.onDidChangeCursorPosition(() => {
                                  try { localStorage.setItem(RULES_CURSOR_KEY, JSON.stringify(_editor.getPosition())); } catch {}
                                });
                                _editor.onDidScrollChange((e: any) => {
                                  try { localStorage.setItem(RULES_SCROLL_KEY, String(e.scrollTop)); } catch {}
                                });
                                // auto-format on blur
                                _editor.onDidBlurEditorText(() => {
                                  try {
                                    if (!canEdit) return;
                                    _editor.getAction('editor.action.formatDocument')?.run?.();
                                  } catch {}
                                });
                              }}
                            />
                          </Suspense>
                        </div>
                        {!rulesValid && (
                          <div id="rules-error" className="text-xs text-red-600" aria-live="polite">{rulesParseError || 'Ungültiges JSON in den Regeln'}</div>
                        )}
                        {rulesValid && !rulesSchemaValid && (
                          <div id="rules-error" className="text-xs text-red-600 space-y-1" aria-live="polite">
                            <div>Strukturell ungültig: Erwartet wird ein Objekt mit <code>rules</code> als Array.</div>
                            {schemaErrors.map((e,i)=>(<div key={i}>• {e}</div>))}
                            <div className="mt-2 text-[11px] text-muted-foreground">
                              <div className="font-medium text-[11px] text-foreground">Hinweis</div>
                              <div>Pfadangaben nutzen Punkt/Index-Notation, z.B. <code>rules[0].conditions[1]</code>.</div>
                              <div>Erlaubte <code>conditions.type</code>: <code>address_match</code>, <code>amount_gt</code>, <code>label_in</code>, <code>country_in</code>, <code>bridge_event</code>.</div>
                              <div>Spezifikation siehe interne Doku: <code>Rule_DSL.md</code>.</div>
                            </div>
                          </div>
                        )}
                        {rulesValid && rulesSchemaValid && (
                          <div className="text-xs text-muted-foreground">{`${(newRules || '').split('\n').length} Zeilen • ${(newRules || '').length} Zeichen`}</div>
                        )}
                        {rulesValid && rulesSchemaValid && (
                          <div className="text-xs text-green-600">JSON OK • Schema OK</div>
                        )}
                        <div className="flex items-center gap-2 flex-wrap">
                          <Select value={statusToSet} onValueChange={(val:any)=>setStatusToSet(val)}>
                            <SelectTrigger className="w-[140px]" disabled={!canEdit} title={!canEdit ? 'Keine Berechtigung' : undefined}><SelectValue placeholder="Status" /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="draft">draft</SelectItem>
                              <SelectItem value="active">active</SelectItem>
                              <SelectItem value="archived">archived</SelectItem>
                            </SelectContent>
                          </Select>
                          <Button variant="ghost" size="sm" onClick={() => setShowEditorHints(v=>!v)} title="Editor-Hinweise ein-/ausblenden">{showEditorHints ? 'Hinweise ausblenden' : 'Hinweise einblenden'}</Button>
                          {!rulesEditorRef.current && (
                            <>
                              <Button
                                variant="outline"
                                onClick={() => { formatNewRules(); }}
                                disabled={!canEdit || !rulesValid}
                                title={!rulesValid ? 'Bitte gültiges JSON einfügen' : !canEdit ? 'Keine Berechtigung' : undefined}
                              >JSON formatieren</Button>
                              <Button variant="outline" onClick={minifyNewRules} disabled={!canEdit || !rulesValid} title={!rulesValid ? 'Bitte gültiges JSON einfügen' : !canEdit ? 'Keine Berechtigung' : undefined}>JSON minimieren</Button>
                            </>
                          )}
                          <Button variant="outline" onClick={handleExportRules} disabled={!rulesValid || !rulesSchemaValid} title={!rulesValid ? 'Bitte gültiges JSON einfügen' : !rulesSchemaValid ? "Regeln-Objekt muss ein 'rules' Array enthalten" : undefined}>Exportieren</Button>
                          <Button variant="outline" onClick={handleImportClick} disabled={!canEdit} title={!canEdit ? 'Keine Berechtigung' : undefined}>Importieren</Button>
                          <Button variant="outline" onClick={handleCopyRules}>Kopieren</Button>
                          <Button variant="outline" onClick={clearDraft} disabled={!canEdit} title={!canEdit ? 'Keine Berechtigung' : undefined}>Entwurf verwerfen</Button>
                          <Button variant="outline" onClick={openDiffWithSelectedVersion}>{diffOpen ? 'Diff schließen' : 'Diff anzeigen'}</Button>
                          <Button variant="outline" onClick={resetToSelectedVersion} disabled={!canEdit} title={!canEdit ? 'Keine Berechtigung' : undefined}>Auf ausgewählte Version zurücksetzen</Button>
                          <Button onClick={handleNewVersion} disabled={!canEdit || isVersioning || !rulesValid || !rulesSchemaValid} title={!canEdit ? 'Keine Berechtigung zum Anlegen' : undefined}>
                            {isVersioning ? 'Anlegen...' : 'Version anlegen'}
                          </Button>
                        </div>
                        {rulesEditorRef.current && showEditorHints && (
                          <div className="text-[11px] text-muted-foreground mt-1">Tipp: Formatieren mit <kbd className="px-1 py-0.5 border rounded">Cmd/Ctrl</kbd> + <kbd className="px-1 py-0.5 border rounded">Shift</kbd> + <kbd className="px-1 py-0.5 border rounded">F</kbd> • Minimieren mit <kbd className="px-1 py-0.5 border rounded">Cmd/Ctrl</kbd> + <kbd className="px-1 py-0.5 border rounded">M</kbd></div>
                        )}
                        <input ref={fileInputRef} type="file" accept="application/json,.json" className="hidden" onChange={handleFileChange} />
                        <div>
                          <div className="text-sm text-muted-foreground mb-1">Notizen (optional)</div>
                          <Textarea aria-label="Notizen" rows={3} value={newNotes} onChange={(e: React.ChangeEvent<HTMLTextAreaElement>)=>setNewNotes(e.target.value)} readOnly={!canEdit} />
                        </div>
                        {diffOpen && (
                          <div ref={diffContainerRef} tabIndex={-1} className="mt-2 space-y-2" aria-label="Diff Anzeige" role="region">
                            <div className="text-sm font-medium">Diff (Editor vs. ausgewählte Version)</div>
                            <div className="border rounded">
                              <Suspense fallback={<div className="p-3 text-sm text-muted-foreground">Lade Diff...</div>}>
                                <DiffViewerLazy
                                  oldValue={diffSideBySide.left}
                                  newValue={diffSideBySide.right}
                                  splitView={true}
                                  hideLineNumbers={false}
                                  showDiffOnly={false}
                                />
                              </Suspense>
                            </div>
                            <details>
                              <summary className="text-xs cursor-pointer">Zeilenweiser Diff (Fallback)</summary>
                              <pre className="p-3 bg-muted rounded text-xs font-mono overflow-auto max-h-64 whitespace-pre-wrap">{diffText}</pre>
                              <div className="text-xs text-muted-foreground">'-' entfernt, '+' hinzugefügt, ' ' unverändert</div>
                            </details>
                          </div>
                        )}
                      </TabsContent>
                      <TabsContent value="simulate" className="space-y-2" aria-busy={busySimulating || undefined}>
                        {insufficientCredits && (
                          <div className="p-3 border border-amber-300 bg-amber-50 rounded text-sm">
                            Nicht genügend Credits für die Simulation. <LinkLocalized className="underline" to="/pricing">Jetzt Plan upgraden</LinkLocalized>.
                          </div>
                        )}
                        <div className="flex items-center justify-between text-xs text-muted-foreground">
                          <div className="flex items-center gap-2">
                            <Button variant="outline" size="sm" onClick={formatEvents} disabled={!canEdit || !simValid} title={!canEdit ? 'Keine Berechtigung' : !simValid ? 'Bitte gültiges JSON-Array einfügen' : undefined}>Formatieren</Button>
                            <Button variant="outline" size="sm" onClick={minifyEvents} disabled={!canEdit || !simValid} title={!canEdit ? 'Keine Berechtigung' : !simValid ? 'Bitte gültiges JSON-Array einfügen' : undefined}>Minimieren</Button>
                            <Button variant="outline" size="sm" onClick={handleCopySim} disabled={!simValid}>Kopieren</Button>
                          </div>
                          <div>{`${(simEvents || '').split('\n').length} Zeilen • ${(simEvents || '').length} Zeichen`}</div>
                        </div>
                        <div className="border rounded overflow-hidden mt-1">
                          <Suspense fallback={<Textarea aria-label="Events JSON" rows={10} className="font-mono whitespace-pre-wrap" value={simEvents} readOnly />}> 
                            <MonacoEditor
                              height={260}
                              language="json"
                              value={simEvents}
                              path={eventsModelUri}
                              onChange={(val)=> setSimEvents(val ?? '')}
                              options={{ readOnly: !canEdit, minimap: { enabled: false }, scrollBeyondLastLine: false, wordWrap: 'on' }}
                              onMount={(editor, monaco) => {
                                monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
                                  validate: true,
                                  schemas: [
                                    { uri: 'inmemory://schemas/sim-events.json', fileMatch: [eventsModelUri], schema: { type: 'array' } as any }
                                  ]
                                });
                                try { (eventsEditorRef as any).current = editor; } catch {}
                                if (!monacoRef.current) monacoRef.current = monaco;
                                // restore cursor & scroll
                                try {
                                  const curRaw = localStorage.getItem(EVENTS_CURSOR_KEY);
                                  if (curRaw) {
                                    const pos = JSON.parse(curRaw);
                                    if (pos?.lineNumber && pos?.column) editor.setPosition(pos);
                                  }
                                  const stRaw = localStorage.getItem(EVENTS_SCROLL_KEY);
                                  if (stRaw) {
                                    const st = parseInt(stRaw, 10);
                                    if (!Number.isNaN(st)) editor.setScrollTop(st);
                                  }
                                } catch {}
                                // persist on changes
                                editor.onDidChangeCursorPosition(() => {
                                  try { localStorage.setItem(EVENTS_CURSOR_KEY, JSON.stringify(editor.getPosition())); } catch {}
                                });
                                editor.onDidScrollChange((e: any) => {
                                  try { localStorage.setItem(EVENTS_SCROLL_KEY, String(e.scrollTop)); } catch {}
                                });
                                // auto-format on blur
                                editor.onDidBlurEditorText(() => {
                                  try {
                                    if (!canEdit) return;
                                    editor.getAction('editor.action.formatDocument')?.run?.();
                                  } catch {}
                                });
                              }}
                            />
                          </Suspense>
                        </div>
                        {!simValid && (<div id="events-error" className="text-xs text-red-600" aria-live="polite">{eventsParseError || 'Ungültiges JSON oder kein Array'}</div>)}
                        <div className="flex items-center gap-2 flex-wrap">
                          <Button variant="ghost" size="sm" onClick={() => setShowEditorHints(v=>!v)} title="Editor-Hinweise ein-/ausblenden">{showEditorHints ? 'Hinweise ausblenden' : 'Hinweise einblenden'}</Button>
                          {!eventsEditorRef.current ? (
                            <>
                              <Button variant="outline" onClick={formatEvents} disabled={!canEdit || !simValid} title={!canEdit ? 'Keine Berechtigung' : !simValid ? 'Bitte gültiges JSON-Array einfügen' : undefined}>JSON formatieren</Button>
                              <Button variant="outline" onClick={minifyEvents} disabled={!canEdit || !simValid} title={!canEdit ? 'Keine Berechtigung' : !simValid ? 'Bitte gültiges JSON-Array einfügen' : undefined}>JSON minimieren</Button>
                            </>
                          ) : null}
                        </div>
                        {eventsEditorRef.current && showEditorHints && (
                          <div className="text-[11px] text-muted-foreground mt-1">Tipp: Formatieren mit <kbd className="px-1 py-0.5 border rounded">Cmd/Ctrl</kbd> + <kbd className="px-1 py-0.5 border rounded">Shift</kbd> + <kbd className="px-1 py-0.5 border rounded">F</kbd> • Minimieren mit <kbd className="px-1 py-0.5 border rounded">Cmd/Ctrl</kbd> + <kbd className="px-1 py-0.5 border rounded">M</kbd></div>
                        )}
                        <Button onClick={handleSimulate} disabled={!canEdit || isSimulating || !rulesValid || !rulesSchemaValid || !simValid} title={!canEdit ? 'Keine Berechtigung zum Simulieren' : (!rulesValid ? 'Bitte gültiges JSON für Regeln einfügen' : !rulesSchemaValid ? "Regeln-Objekt muss ein 'rules' Array enthalten" : !simValid ? 'Bitte gültiges JSON-Array für Events einfügen' : undefined)}>
                          {isSimulating ? 'Simuliere...' : 'Simulieren'}
                        </Button>
                        <Button variant="outline" onClick={handleExportSim} disabled={!simResult} title={!simResult ? 'Noch kein Ergebnis vorhanden' : undefined}>
                          Ergebnis exportieren
                        </Button>
                        <Button variant="outline" onClick={handleCopySim} disabled={!simResult} title={!simResult ? 'Noch kein Ergebnis vorhanden' : undefined}>Ergebnis kopieren</Button>
                        {simResult && (
                          <div className="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-2 text-sm">
                            <div className="border rounded p-2"><b>Events</b><div className="text-lg font-semibold">{simResult.total_events}</div></div>
                            <div className="border rounded p-2"><b>Treffer</b><div className="text-lg font-semibold">{simResult.hits}</div></div>
                            <div className="border rounded p-2"><b>Trefferquote</b><div className="text-lg font-semibold">{(simResult.hit_rate*100).toFixed(1)}%</div></div>
                          </div>
                        )}
                        {simResult && (
                          <div className="text-sm mt-2">
                            <div><b>Events:</b> {simResult.total_events}</div>
                            <div><b>Treffer:</b> {simResult.hits} ({(simResult.hit_rate*100).toFixed(1)}%)</div>
                            <div className="mt-2"><b>Nach Regel:</b></div>
                            <ul className="list-disc pl-5">
                              {Object.entries(simResult.by_rule).map(([k,v]) => (<li key={k}>{k}: {v}</li>))}
                            </ul>
                            <div className="mt-2"><b>Nach Severity:</b></div>
                            <ul className="list-disc pl-5">
                              {Object.entries(simResult.by_severity).map(([k,v]) => (<li key={k}>{k}: {v}</li>))}
                            </ul>
                          </div>
                        )}
                      </TabsContent>
                    </Tabs>
                  </CardContent>
                </Card>
              )}

              {!creating && !detail && (
                <div className="text-sm text-muted-foreground">Bitte eine Policy aus der Liste auswählen oder neu anlegen.</div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
      </div>
    </div>
  );
}
