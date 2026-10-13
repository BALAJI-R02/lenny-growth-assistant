import { useState } from 'react';
import type { ChunkResult } from '../types';

interface RetrievalTraceProps {
  chunks: ChunkResult[];
}

export function RetrievalTrace({ chunks }: RetrievalTraceProps) {
  const [open, setOpen] = useState(false);

  if (!chunks || chunks.length === 0) return null;

  return (
    <div className="mt-2">
      <button
        className="flex items-center gap-1.5 text-xs font-mono text-text-muted hover:text-text-secondary transition-colors"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-label="Toggle retrieval trace"
      >
        <span style={{ color: '#39ff14', opacity: 0.7 }}>⬡</span>
        <span>RETRIEVAL TRACE</span>
        <span className="text-text-muted">({chunks.length} chunks)</span>
        <span>{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div
          className="mt-1 rounded overflow-hidden animate-slide-in"
          style={{ border: '1px solid #1e2330' }}
        >
          <div
            className="px-3 py-1.5 text-[10px] font-mono uppercase tracking-wider text-text-secondary flex gap-4"
            style={{ background: '#0d0f14', borderBottom: '1px solid #1e2330' }}
          >
            <span className="w-10">SCORE</span>
            <span className="w-32">EPISODE</span>
            <span className="flex-1">EXCERPT</span>
          </div>
          {chunks.map((chunk, i) => (
            <div
              key={chunk.id || i}
              className="px-3 py-2 text-xs font-mono flex gap-4 items-start hover:bg-soc-hover transition-colors"
              style={{ borderBottom: i < chunks.length - 1 ? '1px solid #1e2330' : undefined }}
            >
              <span
                className="w-10 shrink-0 font-semibold"
                style={{ color: chunk.score > 0.3 ? '#39ff14' : chunk.score > 0.1 ? '#ffb347' : '#7a8599' }}
              >
                {chunk.score.toFixed(3)}
              </span>
              <span className="w-32 shrink-0 text-accent-cyan truncate" title={chunk.episode}>
                {chunk.episode?.slice(0, 18)}
              </span>
              <span className="flex-1 text-text-secondary leading-relaxed line-clamp-2">
                {chunk.text?.slice(0, 150)}…
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
