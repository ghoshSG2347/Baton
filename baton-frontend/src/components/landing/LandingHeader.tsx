import { motion, useScroll, useMotionValueEvent } from 'framer-motion';
import { useState } from 'react';
import { Button } from '@/components/ui/primitives';

interface LandingHeaderProps {
  onEnterWorkspace: () => void;
}

export function LandingHeader({ onEnterWorkspace }: LandingHeaderProps) {
  const { scrollY } = useScroll();
  const [scrolled, setScrolled] = useState(false);

  useMotionValueEvent(scrollY, 'change', (val) => {
    setScrolled(val > 80);
  });

  const navLinks = [
    { label: 'Product', href: '#problem' },
    { label: 'Workflow', href: '#workflow' },
    { label: 'Why Baton', href: '#philosophy' },
  ];

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-baton-black/80 backdrop-blur-md border-b border-baton-border/50'
          : 'bg-transparent border-b border-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 lg:px-8 flex items-center justify-between h-16">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5">
            <div className="w-1 h-4 bg-baton-accent" />
            <div className="w-1 h-4 bg-baton-white/40" />
            <div className="w-1 h-4 bg-baton-white/20" />
          </div>
          <span className="text-base font-bold tracking-tight">BATON</span>
        </div>

        {/* Nav links */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-sm text-baton-text-secondary hover:text-baton-white transition-colors duration-150"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Right side */}
        <div className="flex items-center gap-4">
          <a
            href="#workflow"
            className="hidden sm:inline text-sm text-baton-text-secondary hover:text-baton-white transition-colors duration-150"
          >
            Docs
          </a>
          <Button variant="primary" onClick={onEnterWorkspace} className="text-xs px-4 py-1.5">
            Enter Mission Control
          </Button>
        </div>
      </div>
    </motion.header>
  );
}
