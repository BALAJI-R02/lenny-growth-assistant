import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import { useChatStore } from '../store/chatStore';
import { buildSandboxedSrcdoc } from '../utils/sanitize';

const CONTAINMENT_ALLOWED = [
  'Inline CSS styles',
  'data: URI images',
  'Text content',
  'Basic HTML structure',
];

const CONTAINMENT_BLOCKED = [
  '<script> tags',
  'Event handlers (onerror, onclick…)',
  'javascript: URLs',
  'External resources (http/https)',
  'Forms and inputs',
  'iframes (except sandboxed viewer)',
  'Objects and embeds',
];

function ContainmentBadge() {
  const [showPopover, setShowPopover] = useState(false);

  return (
    <div className="relative">
      <button
        className="containment-badge cursor-pointer"
        onClick={() => setShowPopover((v) => !v)}
        aria-expanded={showPopover}
        aria-label="View containment details"
        id="containment-badge"
      >
        <span>⬡</span>
        <span>CONTAINMENT: ACTIVE</span>
      </button>

      {showPopover && (
        <div
          className="absolute right-0 top-8 z-50 rounded p-3 text-xs font-mono w-72 animate-slide-in"
          style={{
            background: '#1a1d24',
            border: '1px solid rgba(57,255,20,0.2)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
          }}
          role="dialog"
          aria-label="Containment details"
        >
          <div className="mb-2 text-accent-green font-semibold uppercase tracking-wider text-[10px]">
            SANDBOX: allow-same-origin (no-scripts)
          </div>
          <div className="mb-1 text-[10px] text-text-secondary uppercase tracking-wider">
            ✓ ALLOWED
          </div>
          {CONTAINMENT_ALLOWED.map((item) => (
            <div key={item} className="text-accent-green text-[11px] py-0.5">
              + {item}
            </div>
          ))}
          <div className="mt-2 mb-1 text-[10px] text-text-secondary uppercase tracking-wider">
            ✗ BLOCKED
          </div>
          {CONTAINMENT_BLOCKED.map((item) => (
            <div key={item} className="text-error-red text-[11px] py-0.5">
              − {item}
            </div>
          ))}
          <div className="mt-2 text-[10px] text-text-muted border-t pt-2" style={{ borderColor: '#1e2330' }}>
            CSP: default-src 'none'; style-src 'unsafe-inline'; img-src data:
          </div>
          <button
            onClick={() => setShowPopover(false)}
            className="mt-1 text-text-muted hover:text-text-secondary"
            aria-label="Close popover"
          >
            [CLOSE]
          </button>
        </div>
      )}
    </div>
  );
}

export function ArtifactViewer() {
  const { activeArtifact, isLoadingArtifact } = useChatStore();
  const [activeTab, setActiveTab] = useState<'preview' | 'source'>('preview');
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!activeArtifact) return;
    await navigator.clipboard.writeText(activeArtifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!activeArtifact) return;
    const ext = activeArtifact.type === 'html' ? 'html' : 'md';
    const blob = new Blob([activeArtifact.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `artifact-${activeArtifact.id.slice(0, 8)}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full soc-panel">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-2.5 border-b"
        style={{ borderColor: '#1e2330', background: '#0d0f14' }}
      >
        <div className="flex items-center gap-2">
          <span style={{ color: '#ffb347', fontSize: '10px' }}>◈</span>
          <span className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-text-secondary">
            PAYLOAD VIEWER
          </span>
          {activeArtifact && (
            <span
              className="text-[10px] font-mono px-1.5 py-0.5 rounded uppercase tracking-wider"
              style={{
                background: activeArtifact.type === 'html' ? 'rgba(255,179,71,0.1)' : 'rgba(0,212,255,0.1)',
                color: activeArtifact.type === 'html' ? '#ffb347' : '#00d4ff',
              }}
            >
              {activeArtifact.type}
            </span>
          )}
        </div>
        <ContainmentBadge />
      </div>

      {/* Toolbar */}
      {activeArtifact && (
        <div
          className="flex items-center justify-between px-4 py-2 border-b"
          style={{ borderColor: '#1e2330', background: '#111318' }}
        >
          {/* Title */}
          <span className="text-xs text-text-secondary truncate max-w-[200px]" title={activeArtifact.title}>
            {activeArtifact.title}
          </span>

          <div className="flex items-center gap-2">
            {/* Preview / Source tabs */}
            <div className="flex rounded overflow-hidden" style={{ border: '1px solid #1e2330' }}>
              <button
                className={`px-3 py-1 text-xs font-mono transition-colors ${activeTab === 'preview' ? 'bg-soc-elevated text-accent-green' : 'text-text-muted hover:text-text-secondary'}`}
                onClick={() => setActiveTab('preview')}
                aria-selected={activeTab === 'preview'}
                id="tab-preview"
              >
                PREVIEW
              </button>
              <button
                className={`px-3 py-1 text-xs font-mono transition-colors ${activeTab === 'source' ? 'bg-soc-elevated text-accent-green' : 'text-text-muted hover:text-text-secondary'}`}
                onClick={() => setActiveTab('source')}
                aria-selected={activeTab === 'source'}
                id="tab-source"
              >
                SOURCE
              </button>
            </div>

            {/* Copy */}
            <button
              className="soc-btn text-xs px-2 py-1"
              onClick={handleCopy}
              aria-label="Copy artifact content"
              id="copy-artifact-btn"
            >
              {copied ? '✓ COPIED' : 'COPY'}
            </button>

            {/* Download */}
            <button
              className="soc-btn text-xs px-2 py-1"
              onClick={handleDownload}
              aria-label="Download artifact"
              id="download-artifact-btn"
            >
              ↓ DL
            </button>
          </div>
        </div>
      )}

      {/* Content area */}
      <div className="flex-1 overflow-hidden">
        {isLoadingArtifact && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="cursor-blink font-mono text-accent-green mb-2">LOADING PAYLOAD</div>
              <div className="text-xs font-mono text-text-muted">Applying containment protocols…</div>
            </div>
          </div>
        )}

        {!isLoadingArtifact && !activeArtifact && (
          <div className="flex flex-col items-center justify-center h-full opacity-30">
            <div className="font-mono text-accent-amber text-3xl mb-3">◫</div>
            <p className="font-mono text-xs text-text-secondary uppercase tracking-wider mb-2">
              NO PAYLOAD LOADED
            </p>
            <p className="text-sm text-text-muted text-center max-w-xs">
              Generate an essay or artifact in chat — it will appear here with full containment.
            </p>
          </div>
        )}

        {!isLoadingArtifact && activeArtifact && (
          <>
            {activeTab === 'preview' && (
              <div className="h-full overflow-auto">
                {activeArtifact.type === 'html' ? (
                  <iframe
                    sandbox="allow-same-origin"
                    srcDoc={buildSandboxedSrcdoc(activeArtifact.content)}
                    title={activeArtifact.title}
                    className="w-full h-full border-none"
                    style={{ background: '#fff', minHeight: '400px' }}
                    aria-label="Sandboxed HTML artifact preview"
                  />
                ) : (
                  <div className="prose-soc p-6 overflow-auto h-full">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeSanitize]}
                      components={{
                        a: ({ href, children }) => (
                          <a
                            href={href}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {children}
                          </a>
                        ),
                      }}
                    >
                      {activeArtifact.content}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'source' && (
              <div className="h-full overflow-auto p-4">
                <pre
                  className="text-xs font-mono text-text-secondary leading-relaxed whitespace-pre-wrap break-words"
                  aria-label="Artifact source code"
                >
                  {activeArtifact.content}
                </pre>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
