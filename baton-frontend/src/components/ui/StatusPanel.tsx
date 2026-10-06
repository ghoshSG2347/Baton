import type { ReactNode } from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle } from 'lucide-react';
import { BatonApiError } from '@/lib/api/batonApi';
import { requestFailure, type Severity } from '@/lib/workspaceStatus';
import { redactUserText } from '@/lib/utils/redaction';
import './StatusPanel.css';
import { useRetryBackoff } from '@/hooks/useRetryBackoff';

export function StatusPanel({ severity = 'info', title, explanation, technicalDetails, primaryAction, secondaryAction, children, className = '' }: {
  severity?: Severity; title: string; explanation: string; technicalDetails?: string;
  primaryAction?: ReactNode; secondaryAction?: ReactNode; children?: ReactNode; className?: string;
}) {
  const Icon = { info: Info, warning: AlertTriangle, error: AlertCircle, success: CheckCircle2 }[severity];
  return <div className={`baton-status baton-status-${severity} ${className}`} role={severity === 'error' ? 'alert' : 'status'}>
    <Icon size={16} aria-hidden="true" /><div className="baton-status-content"><h3>{title}</h3><p>{explanation}</p>{children}
      {(primaryAction || secondaryAction) && <div className="baton-status-actions">{primaryAction}{secondaryAction}</div>}
      {technicalDetails && <details><summary>Technical details</summary><pre>{redactUserText(technicalDetails)}</pre></details>}
    </div>
  </div>;
}

export function ErrorStatus({ error, operation, primaryAction, secondaryAction }: { error: unknown; operation?: string; primaryAction?: ReactNode; secondaryAction?: ReactNode }) {
  const blocked = useRetryBackoff(error);
  const message = requestFailure(error, operation);
  const details = error instanceof BatonApiError ? `HTTP ${error.status || 'unavailable'} · ${error.code}\n${error.message}` : undefined;
  return <StatusPanel {...message} technicalDetails={details} primaryAction={primaryAction && <fieldset disabled={blocked}>{primaryAction}</fieldset>} secondaryAction={secondaryAction} />;
}
