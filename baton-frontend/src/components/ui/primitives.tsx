import { motion } from 'framer-motion';
import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface StatusIndicatorProps {
  status: 'connected' | 'fresh' | 'stale' | 'analyzing' | 'attention' | 'idle' | 'matched' | 'unmatched';
  label?: string;
  className?: string;
  pulse?: boolean;
}

const statusConfig = {
  connected: { color: '#34d59a', label: 'CONNECTED' },
  fresh: { color: '#34d59a', label: 'FRESH' },
  stale: { color: '#94979e', label: 'STALE' },
  analyzing: { color: '#34d59a', label: 'ANALYZING' },
  attention: { color: '#ff3621', label: 'ATTENTION' },
  idle: { color: '#797d86', label: 'IDLE' },
  matched: { color: '#34d59a', label: 'MATCH' },
  unmatched: { color: '#ff3621', label: 'UNMATCHED' },
};

export function StatusIndicator({ status, label, className, pulse = true }: StatusIndicatorProps) {
  const config = statusConfig[status];
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <motion.div
        className="w-1.5 h-1.5 rounded-full"
        style={{ backgroundColor: config.color }}
        animate={pulse ? { opacity: [1, 0.4, 1] } : {}}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
      />
      <span className="font-mono text-[10px] tracking-wider text-baton-text-highlight uppercase">
        {label || config.label}
      </span>
    </div>
  );
}

interface MonoLabelProps {
  children: ReactNode;
  className?: string;
  variant?: 'default' | 'accent' | 'warning' | 'dim';
}

export function MonoLabel({ children, className, variant = 'default' }: MonoLabelProps) {
  const colors = {
    default: 'text-baton-text-secondary',
    accent: 'text-baton-accent',
    warning: 'text-baton-warning',
    dim: 'text-baton-text-tertiary',
  };
  return (
    <span className={cn('font-mono text-[10px] tracking-[0.15em] uppercase', colors[variant], className)}>
      {children}
    </span>
  );
}

interface PanelProps {
  children: ReactNode;
  className?: string;
  label?: string;
}

export function Panel({ children, className, label }: PanelProps) {
  return (
    <div className={cn('border border-baton-border bg-baton-near-black rounded-baton', className)}>
      {label && (
        <div className="border-b border-baton-border px-4 py-2">
          <MonoLabel>{label}</MonoLabel>
        </div>
      )}
      {children}
    </div>
  );
}

interface ButtonProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  className?: string;
  type?: 'button' | 'submit';
  disabled?: boolean;
}

export function Button({ children, onClick, variant = 'secondary', className, type = 'button', disabled }: ButtonProps) {
  const variants = {
    primary: 'bg-baton-accent text-baton-black hover:brightness-110',
    secondary: 'border border-baton-border text-baton-white hover:border-baton-text-tertiary bg-baton-near-black',
    ghost: 'text-baton-text-secondary hover:text-baton-white',
  };
  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      whileTap={{ scale: 0.97 }}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-full px-5 py-2 text-sm font-medium transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed',
        variants[variant],
        className
      )}
    >
      {children}
    </motion.button>
  );
}

interface SectionLabelProps {
  children: ReactNode;
  className?: string;
}

export function SectionLabel({ children, className }: SectionLabelProps) {
  return (
    <div className={cn('flex items-center gap-3', className)}>
      <div className="w-8 h-px bg-baton-accent" />
      <MonoLabel variant="accent">{children}</MonoLabel>
    </div>
  );
}

interface CopyButtonProps {
  text: string;
  label?: string;
}

import { useState } from 'react';
import { Check, Copy } from 'lucide-react';

export function CopyButton({ text, label = 'COPY' }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // fallback
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-1.5 font-mono text-[10px] tracking-wider text-baton-text-secondary hover:text-baton-accent transition-colors uppercase"
    >
      {copied ? <Check size={12} className="text-baton-accent" /> : <Copy size={12} />}
      {copied ? 'COPIED' : label}
    </button>
  );
}

interface TelemetryLineProps {
  className?: string;
  active?: boolean;
}

export function TelemetryLine({ className, active = true }: TelemetryLineProps) {
  return (
    <div className={cn('relative h-px overflow-hidden bg-baton-border', className)}>
      {active && (
        <motion.div
          className="absolute h-full bg-baton-accent"
          style={{ width: '40%' }}
          animate={{ x: ['-100%', '250%'] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
        />
      )}
    </div>
  );
}
