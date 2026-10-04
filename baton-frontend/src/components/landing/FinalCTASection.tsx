import { motion } from 'framer-motion';
import { Button } from '@/components/ui/primitives';
import { ArrowRight } from 'lucide-react';

interface FinalCTASectionProps {
  onEnterWorkspace: () => void;
}

export function FinalCTASection({ onEnterWorkspace }: FinalCTASectionProps) {
  return (
    <section className="relative py-40 px-6 lg:px-8 max-w-4xl mx-auto text-center">
      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="flex items-center justify-center gap-3 mb-10"
      >
        <div className="w-2 h-2 rounded-full bg-baton-accent animate-signal-pulse" />
        <span className="font-mono text-[10px] tracking-[0.3em] text-baton-text-tertiary uppercase">
          YOUR TEAM IS ALREADY BUILDING
        </span>
      </motion.div>

      <motion.h2
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8, delay: 0.1 }}
        className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.05] text-balance"
      >
        MAKE SURE
        <br />
        YOUR AIS ARE BUILDING
        <br />
        <span className="text-baton-accent">FROM THE SAME UNDERSTANDING.</span>
      </motion.h2>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8, delay: 0.3 }}
        className="mt-12"
      >
        <Button variant="primary" onClick={onEnterWorkspace} className="px-8 py-3 text-base">
          ENTER MISSION CONTROL
          <ArrowRight size={16} />
        </Button>
      </motion.div>
    </section>
  );
}
