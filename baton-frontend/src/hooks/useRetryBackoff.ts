import { useEffect, useState } from 'react';
import { BatonApiError } from '@/lib/api/batonApi';

export function useRetryBackoff(error: unknown) {
  const deadline = error instanceof BatonApiError ? error.retryAt || 0 : 0;
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    setNow(Date.now());
    if (!deadline) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [deadline]);
  return deadline > now;
}
