import { useEffect, useState } from 'react';
import { useChatStore } from '../store/chatStore';

const BOOT_LINES = [
  { text: 'INITIALIZING LENNY GROWTH ASSISTANT v1.0', delay: 0 },
  { text: 'ESTABLISHING DATABASE CONNECTION...', delay: 200 },
  { text: 'OK — SESSIONS TABLE READY', delay: 400 },
  { text: 'LOADING TRANSCRIPT INDEX...', delay: 600 },
  { text: 'OK — FULL-TEXT SEARCH ARMED', delay: 800 },
  { text: 'ESTABLISHING UPLINK...', delay: 1000 },
  { text: 'OK — LLM PROVIDER ONLINE', delay: 1200 },
  { text: 'SANDBOXING ARTIFACT RENDERER...', delay: 1400 },
  { text: 'CONTAINMENT ACTIVE', delay: 1600 },
  { text: 'ALL SYSTEMS NOMINAL', delay: 1800 },
  { text: '> READY_', delay: 2000 },
];

interface BootSequenceProps {
  onComplete: () => void;
}

export function BootSequence({ onComplete }: BootSequenceProps) {
  const [visibleLines, setVisibleLines] = useState(0);
  const [skipped, setSkipped] = useState(false);
  const { isBooted } = useChatStore();

  useEffect(() => {
    // Check if already booted this session
    const booted = sessionStorage.getItem('soc_booted');
    if (booted || isBooted) {
      onComplete();
      return;
    }

    // Show lines with delay
    const timers = BOOT_LINES.map((line, i) =>
      setTimeout(() => {
        setVisibleLines(i + 1);
        if (i === BOOT_LINES.length - 1) {
          setTimeout(() => {
            sessionStorage.setItem('soc_booted', '1');
            onComplete();
          }, 600);
        }
      }, line.delay)
    );

    return () => timers.forEach(clearTimeout);
  }, [onComplete, isBooted]);

  const handleSkip = () => {
    sessionStorage.setItem('soc_booted', '1');
    setSkipped(true);
    onComplete();
  };

  if (skipped) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: '#0a0c0f' }}
      role="status"
      aria-label="System initializing"
    >
      <div className="w-full max-w-2xl px-8">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="text-accent-green font-mono text-xs tracking-[0.3em] uppercase mb-2 opacity-60">
            SOC CONSOLE // CLASSIFIED
          </div>
          <div
            className="w-20 h-px mx-auto mb-2"
            style={{ background: 'linear-gradient(90deg, transparent, #39ff14, transparent)' }}
          />
        </div>

        {/* Boot lines */}
        <div className="font-mono text-sm space-y-1">
          {BOOT_LINES.slice(0, visibleLines).map((line, i) => (
            <div
              key={i}
              className="flex gap-3 animate-slide-in"
              style={{ color: line.text.startsWith('OK') || line.text.startsWith('>') ? '#39ff14' : '#7a8599' }}
            >
              <span className="opacity-40 select-none">{String(i).padStart(2, '0')}</span>
              <span>{line.text}</span>
            </div>
          ))}
          {visibleLines > 0 && visibleLines < BOOT_LINES.length && (
            <div className="flex gap-3">
              <span className="opacity-40 font-mono">▌</span>
              <span className="animate-blink" style={{ color: '#39ff14' }}>█</span>
            </div>
          )}
        </div>

        {/* Skip button (appears after 500ms) */}
        {visibleLines >= 2 && (
          <button
            onClick={handleSkip}
            className="mt-8 text-xs font-mono text-text-muted hover:text-text-secondary transition-colors"
            aria-label="Skip boot sequence"
          >
            [SKIP]
          </button>
        )}
      </div>
    </div>
  );
}
