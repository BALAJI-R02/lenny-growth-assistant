import { useState } from 'react';
import type { Citation } from '../types';

interface CitationChipProps {
  citation: Citation;
}

export function CitationChip({ citation }: CitationChipProps) {
  const [expanded, setExpanded] = useState(false);

  const label = `EP // ${citation.guest || citation.episode}`;

  return (
    <div className="inline-block">
      <button
        className="evidence-chip"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        aria-label={`Evidence from ${citation.guest || citation.episode}`}
        id={`citation-${citation.ref}`}
      >
        <span className="opacity-60">[{citation.ref}]</span>
        <span>{label.length > 30 ? label.slice(0, 30) + '…' : label}</span>
        <span className="opacity-50">{expanded ? '▲' : '▼'}</span>
      </button>

      {expanded && (
        <div
          className="mt-1 p-3 rounded text-xs font-mono animate-slide-in"
          style={{
            background: 'rgba(0,212,255,0.05)',
            border: '1px solid rgba(0,212,255,0.2)',
            maxWidth: '480px',
          }}
          role="region"
          aria-label={`Evidence detail for citation ${citation.ref}`}
        >
          <div className="flex flex-col gap-1 mb-2">
            <div>
              <span className="text-text-secondary">EPISODE: </span>
              <span className="text-accent-cyan">{citation.episode}</span>
            </div>
            <div>
              <span className="text-text-secondary">GUEST: </span>
              <span className="text-text-primary">{citation.guest || 'Unknown'}</span>
            </div>
            <div>
              <span className="text-text-secondary">SOURCE: </span>
              <span className="text-text-muted text-[10px] break-all">{citation.source_path}</span>
            </div>
          </div>
          <div
            className="p-2 rounded text-text-secondary leading-relaxed"
            style={{ background: 'rgba(0,0,0,0.3)', fontSize: '11px' }}
          >
            "{citation.snippet}"
          </div>
        </div>
      )}
    </div>
  );
}
