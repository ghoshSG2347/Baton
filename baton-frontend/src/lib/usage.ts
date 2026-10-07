// One bounded, memory-only tab session. Contains measurements, never request bodies/headers.
export type Counts = {
  operations: number; errors: number; abandoned: number; latency_ms: number;
  github_requests: number | null; github_downloads: number | null; cache_hits: number | null; snapshot_hits: number | null;
  ai_requests: number | null; input_tokens: number | null; output_tokens: number | null;
  total_tokens: number | null; thinking_tokens: number | null; provider_latency_ms: number | null;
};
type Record = Counts & { operation: string; status: number };
const measured = ['github_requests', 'github_downloads', 'cache_hits', 'snapshot_hits', 'ai_requests', 'input_tokens', 'output_tokens', 'total_tokens', 'thinking_tokens', 'provider_latency_ms'] as const;
const zero = (): Counts => ({ operations: 0, errors: 0, abandoned: 0, latency_ms: 0, github_requests: 0, github_downloads: 0, cache_hits: 0, snapshot_hits: 0, ai_requests: 0, input_tokens: 0, output_tokens: 0, total_tokens: 0, thinking_tokens: 0, provider_latency_ms: 0 });
let state = { session: zero(), conversation: zero(), quota: {} as Partial<{ limit: number; remaining: number; used: number; reset_at: number }>, last: null as Record | null };
let conversationKey = 0;
const listeners = new Set<() => void>();
const emit = () => listeners.forEach(listener => listener());
export const subscribeUsage = (listener: () => void) => { listeners.add(listener); return () => { listeners.delete(listener); }; };
export const getUsage = () => state;
export const currentConversationKey = () => conversationKey;
export function beginConversation() { conversationKey++; state = { ...state, conversation: zero() }; emit(); }
export function clearProviderQuota() { state = { ...state, quota: {} }; beginConversation(); }
const number = (value: unknown): number | null => typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 ? value : null;
function add(left: Counts, right: Counts): Counts {
  const result = { ...left, operations: left.operations + right.operations, errors: left.errors + right.errors, abandoned: left.abandoned + right.abandoned, latency_ms: left.latency_ms + right.latency_ms };
  for (const key of measured) result[key] = left[key] === null || right[key] === null ? null : left[key]! + right[key]!;
  return result;
}
export function recordUsage(operation: string, status: number, header: string | null, duration: number, key: number, abandoned = false) {
  let data: { [key: string]: unknown } = {};
  try { const parsed = header && header.length < 3000 ? JSON.parse(header) : null; if (parsed && typeof parsed === 'object') data = parsed; } catch { /* Older backend or missing measurements means UNKNOWN. */ }
  const record: Record = { ...zero(), operation: operation.split('?')[0], status, operations: 1, errors: status >= 400 || (!status && !abandoned) ? 1 : 0, abandoned: abandoned ? 1 : 0, latency_ms: number(data.latency_ms) ?? Math.round(duration) };
  for (const field of measured) record[field] = number(data[field]);
  const quota = { ...state.quota };
  if (key === conversationKey && data.quota && typeof data.quota === 'object') for (const field of ['limit', 'remaining', 'used', 'reset_at'] as const) {
    const value = number((data.quota as { [key: string]: unknown })[field]); if (value !== null) quota[field] = value;
  }
  state = { session: add(state.session, record), conversation: operation === '/api/v1/workspace/chat' && key === conversationKey ? add(state.conversation, record) : state.conversation, quota, last: record };
  emit();
}
