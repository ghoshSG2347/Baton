import { motion, useScroll, useTransform } from 'framer-motion';
import { useRef } from 'react';
import { Button } from '@/components/ui/primitives';
import { SignalField } from '@/components/ui/SignalField';
import { ArrowRight, ChevronDown } from 'lucide-react';

interface HeroSectionProps {
  onEnterWorkspace: () => void;
}

export function HeroSection({ onEnterWorkspace }: HeroSectionProps) {
  const ref = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start start', 'end start'],
  });

  const y = useTransform(scrollYProgress, [0, 1], [0, -100]);
  const opacity = useTransform(scrollYProgress, [0, 0.7], [1, 0]);
  const scale = useTransform(scrollYProgress, [0, 1], [1, 0.95]);

  return (
    <section ref={ref} className="relative min-h-screen flex items-center justify-center pt-16">
      {/* Hero-specific signal field */}
      <div className="absolute inset-0 z-0">
        <SignalField density={80} interactive={true} />
      </div>

      {/* Vignette */}
      <div
        className="absolute inset-0 z-0"
        style={{
          background: 'radial-gradient(ellipse at center, transparent 0%, rgba(0,0,0,0.7) 70%, #000 100%)',
        }}
      />

      <motion.div
        style={{ y, opacity, scale }}
        className="relative z-10 max-w-5xl mx-auto px-6 text-center"
      >
        {/* System label */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="flex items-center justify-center gap-3 mb-8"
        >
          <div className="w-2 h-2 rounded-full bg-baton-accent animate-signal-pulse" />
          <span className="font-mono text-[10px] tracking-[0.3em] text-baton-text-tertiary uppercase">
            BATON — MISSION CONTROL
          </span>
        </motion.div>

        {/* Hero headline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="text-5xl sm:text-6xl lg:text-7xl xl:text-8xl font-bold tracking-tight leading-[0.95] text-balance"
        >
          MISSION CONTROL
          <br />
          <span className="text-baton-text-secondary">FOR AI-ASSISTED</span>
          <br />
          DEVELOPMENT TEAMS
        </motion.h1>

        {/* Supporting copy */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="mt-8 text-lg text-baton-text-tertiary max-w-2xl mx-auto leading-relaxed text-balance"
        >
          Give every teammate and their AI exactly the project context they need —
          <span className="text-baton-text-highlight"> not the entire repository.</span>
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.7 }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <Button variant="primary" onClick={onEnterWorkspace} className="px-8 py-3 text-base">
            ENTER MISSION CONTROL
            <ArrowRight size={16} />
          </Button>
          <a
            href="#workflow"
            className="inline-flex items-center gap-2 text-sm text-baton-text-secondary hover:text-baton-white transition-colors duration-150 px-6 py-3"
          >
            SEE HOW BATON WORKS
            <ChevronDown size={14} />
          </a>
        </motion.div>

        {/* Telemetry strip */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1 }}
          className="mt-16 flex items-center justify-center gap-6 font-mono text-[10px] tracking-wider text-baton-text-tertiary uppercase"
        >
          <span className="flex items-center gap-1.5">
            <span className="w-1 h-1 rounded-full bg-baton-accent" />
            GITHUB CONNECTED
          </span>
          <span className="text-baton-border">|</span>
          <span>BRANCH main</span>
          <span className="text-baton-border">|</span>
          <span>84 FILES</span>
          <span className="text-baton-border">|</span>
          <span>3.2K TOKENS</span>
        </motion.div>
      </motion.div>
    </section>
  );
}
