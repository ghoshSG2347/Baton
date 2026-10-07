import { useSyncExternalStore } from 'react';
import { getUsage, subscribeUsage, type Counts } from '@/lib/usage';
const value = (count: number | null | undefined) => count == null ? 'UNKNOWN' : count.toLocaleString();
function AIUsage({ label, counts }: { label: string; counts: Counts }) {
  return <section className="border-t border-baton-border py-6" aria-label={label}>
    <h2 className="text-lg mb-4">{label}</h2>
    <dl className="grid grid-cols-2 gap-3 text-sm">
      {([['AI requests', counts.ai_requests], ['Input tokens', counts.input_tokens], ['Output tokens', counts.output_tokens], ['Total tokens', counts.total_tokens], ['Thinking tokens', counts.thinking_tokens], ['Provider latency (ms)', counts.provider_latency_ms], ['Errors', counts.errors], ['Abandoned operations', counts.abandoned]] as const).map(([name, count]) => <div key={name}><dt className="text-baton-text-tertiary">{name}</dt><dd>{value(count)}</dd></div>)}
    </dl>
  </section>;
}
export function UsageCenter() {
  const { session, conversation, quota, last } = useSyncExternalStore(subscribeUsage, getUsage);
  return <div className="p-6 lg:p-10 max-w-4xl mx-auto">
    <h1 className="text-2xl mb-3">Usage Center</h1>
    <p className="text-sm text-baton-text-tertiary mb-6">This tab's runtime session. Reload clears measurements. New Chat clears the current conversation totals and preserves session totals. UNKNOWN means the provider or backend did not report a measurement.</p>
    <AIUsage label="Current conversation" counts={conversation} />
    <AIUsage label="Current Baton session" counts={session} />
    <section className="border-t border-baton-border py-6"><h2 className="text-lg mb-4">Baton GitHub consumption</h2><dl className="grid grid-cols-2 gap-3 text-sm">
      {([['API requests', session.github_requests], ['Archive downloads', session.github_downloads], ['Cache hits', session.cache_hits], ['Snapshot reads', session.snapshot_hits]] as const).map(([name, count]) => <div key={name}><dt className="text-baton-text-tertiary">{name}</dt><dd>{value(count)}</dd></div>)}
    </dl><p className="text-xs text-baton-text-tertiary mt-4">Downloads are counted separately from GitHub API requests. Reusing evidence does not collect repository files again; authorization can still read HEAD.</p></section>
    <section className="border-t border-baton-border py-6"><h2 className="text-lg mb-4">GitHub provider quota</h2><p className="text-sm">Latest observed account bucket: {value(quota.remaining)} remaining / {value(quota.limit)} limit. Used: {value(quota.used)}.</p><p className="text-xs text-baton-text-tertiary mt-3">Shared account quota is separate from this tab's Baton consumption. Gemini token counts are provider reports, not character estimates, monetary charges or remaining account quota. Deterministic exports make zero AI calls. Abandoning a browser request does not prove remote cancellation.</p></section>
    {last && <section className="border-t border-baton-border py-6" aria-label="Last operation"><h2 className="text-lg mb-3">Last operation</h2><code className="text-xs break-all">{last.operation}</code><p className="text-sm mt-2">Status: {last.abandoned ? 'Abandoned by browser' : last.status || 'Network error'} · {value(last.latency_ms)} ms</p></section>}
  </div>;
}
