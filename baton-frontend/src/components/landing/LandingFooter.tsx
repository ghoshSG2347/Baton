export function LandingFooter() {
  return (
    <footer className="relative border-t border-baton-border py-12 px-6 lg:px-8">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5">
            <div className="w-1 h-3.5 bg-baton-accent" />
            <div className="w-1 h-3.5 bg-baton-white/40" />
            <div className="w-1 h-3.5 bg-baton-white/20" />
          </div>
          <span className="text-sm font-bold tracking-tight">BATON</span>
        </div>
        <p className="font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase">
          Mission Control for AI-Assisted Development
        </p>
        <div className="flex items-center gap-6 font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase">
          <span>GITHUB</span>
          <span>DOCS</span>
          <span>PRIVACY</span>
        </div>
      </div>
    </footer>
  );
}
