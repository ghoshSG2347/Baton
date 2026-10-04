import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

export function formatTimestamp(iso: string): string {
  if (!iso) return 'NOT AVAILABLE';
  try {
    const d = new Date(iso);
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  } catch {
    return iso;
  }
}

export function formatTime(iso: string): string {
  if (!iso) return '--:--';
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  } catch {
    return '--:--';
  }
}

export function shortSha(sha: string): string {
  if (!sha) return 'NOT AVAILABLE';
  return sha.substring(0, 7);
}

export function formatNumber(n: number): string {
  return n.toLocaleString('en-US');
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}
