import { useEffect, useRef } from 'react';
import { useReducedMotion } from 'framer-motion';

interface SignalFieldProps {
  density?: number;
  className?: string;
  interactive?: boolean;
}

interface Bar {
  x: number;
  width: number;
  height: number;
  baseOpacity: number;
  speed: number;
  phase: number;
  isAccent: boolean;
}

export function SignalField({ density = 60, className = '', interactive = true }: SignalFieldProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: -1000, y: -1000 });
  const rafRef = useRef(0);
  const reducedMotion = useReducedMotion();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let bars: Bar[] = [];
    let time = 0;

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);

      const count = Math.floor((rect.width / 1920) * density);
      bars = Array.from({ length: Math.max(count, 20) }, () => ({
        x: Math.random() * rect.width,
        width: 1 + Math.random() * 1.5,
        height: 20 + Math.random() * rect.height * 0.5,
        baseOpacity: 0.03 + Math.random() * 0.08,
        speed: 0.3 + Math.random() * 0.8,
        phase: Math.random() * Math.PI * 2,
        isAccent: Math.random() < 0.08,
      }));
    };

    const draw = () => {
      const rect = canvas.getBoundingClientRect();
      ctx.clearRect(0, 0, rect.width, rect.height);

      bars.forEach((bar) => {
        const wave = Math.sin(time * bar.speed * 0.01 + bar.phase);
        const opacity = bar.baseOpacity + wave * 0.04;
        const heightMod = 1 + wave * 0.15;

        const mouseX = mouseRef.current.x;
        const mouseY = mouseRef.current.y;
        const dx = bar.x - mouseX;
        const dy = rect.height / 2 - mouseY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const influence = interactive ? Math.max(0, 1 - dist / 250) : 0;

        const finalOpacity = Math.min(0.6, opacity + influence * 0.15);
        const finalHeight = bar.height * heightMod * (1 + influence * 0.3);

        if (bar.isAccent) {
          ctx.fillStyle = `rgba(52, 213, 154, ${finalOpacity * 1.5})`;
        } else {
          ctx.fillStyle = `rgba(255, 255, 255, ${finalOpacity})`;
        }

        const startY = (rect.height - finalHeight) / 2;
        ctx.fillRect(bar.x, startY, bar.width, finalHeight);

        if (bar.isAccent && (wave > 0.5 || influence > 0.3)) {
          ctx.fillStyle = `rgba(52, 213, 154, ${finalOpacity * 0.5})`;
          ctx.fillRect(bar.x, startY - 2, bar.width, finalHeight + 4);
        }
      });

      // Tiny data points near cursor
      if (interactive && mouseRef.current.x > 0) {
        for (let i = 0; i < 5; i++) {
          const angle = time * 0.02 + i * 1.2;
          const r = 40 + Math.sin(time * 0.01 + i) * 20;
          const px = mouseRef.current.x + Math.cos(angle) * r;
          const py = mouseRef.current.y + Math.sin(angle) * r;
          ctx.fillStyle = `rgba(52, 213, 154, ${0.3 + Math.sin(time * 0.03 + i) * 0.2})`;
          ctx.fillRect(px, py, 1.5, 1.5);
        }
      }

      time++;
      if (!reducedMotion) rafRef.current = requestAnimationFrame(draw);
    };

    const onMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseRef.current = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    };

    const onMouseLeave = () => {
      mouseRef.current = { x: -1000, y: -1000 };
    };

    resize();
    draw();
    const onResize = () => { resize(); if (reducedMotion) draw(); };
    window.addEventListener('resize', onResize);
    if (interactive && !reducedMotion && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
      window.addEventListener('mousemove', onMouseMove, { passive: true });
      document.addEventListener('mouseleave', onMouseLeave);
    }

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('resize', onResize);
      window.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseleave', onMouseLeave);
    };
  }, [density, interactive, reducedMotion]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={`absolute inset-0 w-full h-full ${className}`}
      style={{ pointerEvents: 'none' }}
    />
  );
}
