import { motion, useScroll, useTransform } from 'framer-motion';
import { useEffect, useState } from 'react';
import { SignalField } from '@/components/ui/SignalField';
import { useSmoothScroll } from '@/hooks/useSmoothScroll';
import { LandingHeader } from '@/components/landing/LandingHeader';
import { HeroSection } from '@/components/landing/HeroSection';
import { ProblemSection } from '@/components/landing/ProblemSection';
import { BatonLoopSection } from '@/components/landing/BatonLoopSection';
import { ContextSection } from '@/components/landing/ContextSection';
import { OwnershipSection } from '@/components/landing/OwnershipSection';
import { HandoffSection } from '@/components/landing/HandoffSection';
import { ConflictRadarSection } from '@/components/landing/ConflictRadarSection';
import { IntegrationSection } from '@/components/landing/IntegrationSection';
import { PhilosophySection } from '@/components/landing/PhilosophySection';
import { FinalCTASection } from '@/components/landing/FinalCTASection';
import { LandingFooter } from '@/components/landing/LandingFooter';

interface LandingPageProps {
  onEnterWorkspace: () => void;
}

export function LandingPage({ onEnterWorkspace }: LandingPageProps) {
  useSmoothScroll();
  const { scrollYProgress } = useScroll();
  const heroOpacity = useTransform(scrollYProgress, [0, 0.05], [1, 0]);
  const [showTransition, setShowTransition] = useState(false);

  const handleEnterWorkspace = () => {
    setShowTransition(true);
    setTimeout(() => {
      onEnterWorkspace();
    }, 400);
  };

  useEffect(() => {
    if (showTransition) {
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [showTransition]);

  return (
    <div className="relative min-h-screen bg-baton-black text-baton-white overflow-x-hidden">
      {/* Background signal field - fixed for entire page */}
      <div className="fixed inset-0 z-0 opacity-40">
        <SignalField density={50} interactive={true} />
      </div>

      {/* Scanline */}
      <div className="scanline-overlay" />

      {/* Grid overlay */}
      <div className="fixed inset-0 z-0 opacity-20 grid-bg pointer-events-none" />

      {/* Content */}
      <div className="relative z-10">
        <LandingHeader onEnterWorkspace={handleEnterWorkspace} />

        <motion.div style={{ opacity: heroOpacity }}>
          <HeroSection onEnterWorkspace={handleEnterWorkspace} />
        </motion.div>

        <ProblemSection />
        <BatonLoopSection />
        <ContextSection />
        <OwnershipSection />
        <HandoffSection />
        <ConflictRadarSection />
        <IntegrationSection />
        <PhilosophySection />
        <FinalCTASection onEnterWorkspace={handleEnterWorkspace} />
        <LandingFooter />
      </div>

      {/* Page transition overlay */}
      {showTransition && (
        <motion.div
          className="fixed inset-0 z-[10001] bg-baton-black pointer-events-none"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.15 }}
        >
          <motion.div
            className="absolute top-0 left-0 right-0 h-1 bg-baton-accent"
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            style={{ transformOrigin: 'left' }}
          />
        </motion.div>
      )}
    </div>
  );
}
