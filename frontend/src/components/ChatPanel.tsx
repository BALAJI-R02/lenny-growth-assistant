import { useEffect, useRef, useState } from 'react';
import { useChat } from '../hooks/useChat';
import { useSession } from '../hooks/useSession';
import { useChatStore } from '../store/chatStore';
import { MessageBubble } from './MessageBubble';

const ROUTE_HINTS = [
  { trigger: 'write a ship 30', hint: '→ ESSAY ROUTE', color: '#00d4ff' },
  { trigger: 'write an essay', hint: '→ ESSAY ROUTE', color: '#00d4ff' },
  { trigger: 'create html', hint: '→ ARTIFACT ROUTE', color: '#ffb347' },
  { trigger: 'generate', hint: '→ ARTIFACT ROUTE', color: '#ffb347' },
  { trigger: 'create markdown', hint: '→ ARTIFACT ROUTE', color: '#ffb347' },
];

function detectRouteHint(input: string) {
  const lower = input.toLowerCase();
  for (const { trigger, hint, color } of ROUTE_HINTS) {
    if (lower.includes(trigger)) return { hint, color };
  }
  return null;
}

export function ChatPanel() {
  const { currentSessionId, messages, isSending } = useChatStore();
  const { startNewSession } = useSession();
  const { send } = useChat();

  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const sessionMessages = currentSessionId ? (messages[currentSessionId] || []) : [];
  const routeHint = detectRouteHint(input);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [sessionMessages.length, isSending]);

  // Auto-init session on mount
  useEffect(() => {
    if (!currentSessionId) {
      startNewSession();
    }
  }, [currentSessionId, startNewSession]);

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isSending) return;
    setInput('');
    await send(trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full soc-panel" style={{ borderRight: '1px solid #1e2330' }}>
      {/* Panel header */}
      <div
        className="flex items-center justify-between px-4 py-2.5 border-b"
        style={{ borderColor: '#1e2330', background: '#0d0f14' }}
      >
        <div className="flex items-center gap-2">
          <span style={{ color: '#39ff14', fontSize: '10px' }}>◈</span>
          <span className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-text-secondary">
            OPERATIONS
          </span>
          {currentSessionId && (
            <span className="text-[10px] font-mono text-text-muted">
              [{currentSessionId.slice(0, 8)}…]
            </span>
          )}
        </div>
        <button
          onClick={() => startNewSession()}
          className="text-[10px] font-mono text-text-muted hover:text-accent-green transition-colors"
          aria-label="Start new operation"
          id="new-session-btn"
        >
          [+ NEW OP]
        </button>
      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto px-4 py-4 space-y-4"
        role="log"
        aria-label="Conversation"
        aria-live="polite"
      >
        {sessionMessages.length === 0 && !isSending && (
          <div className="flex flex-col items-center justify-center h-full text-center opacity-40">
            <div className="font-mono text-accent-green text-2xl mb-3">◈</div>
            <p className="font-mono text-xs text-text-secondary uppercase tracking-wider mb-2">
              AWAITING QUERY
            </p>
            <p className="text-sm text-text-muted max-w-xs">
              Ask a product/growth question, request a Ship30 essay, or generate an artifact.
            </p>
          </div>
        )}

        {sessionMessages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            isSending={false}
          />
        ))}

        {isSending && (
          <div className="flex items-start gap-2">
            <div
              className="msg-assistant"
              style={{ minWidth: '80px' }}
              aria-live="polite"
              aria-label="Processing response"
            >
              <div className="cursor-blink text-sm font-mono text-accent-green">
                PROCESSING
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div
        className="border-t px-4 py-3"
        style={{ borderColor: '#1e2330', background: '#0d0f14' }}
      >
        {/* Route hint */}
        {routeHint && (
          <div className="mb-1.5 text-[11px] font-mono" style={{ color: routeHint.color }}>
            {routeHint.hint}
          </div>
        )}

        <div className="flex gap-2">
          <textarea
            ref={textareaRef}
            className="soc-input flex-1 rounded px-3 py-2 resize-none text-sm"
            rows={2}
            placeholder="Query the transcripts... (Shift+Enter for newline)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSending || !currentSessionId}
            aria-label="Chat input"
            id="chat-input"
            style={{ minHeight: '60px', maxHeight: '120px' }}
          />
          <button
            className="soc-btn self-end px-4 py-2 flex items-center gap-1.5"
            onClick={handleSend}
            disabled={isSending || !input.trim() || !currentSessionId}
            aria-label="Send message"
            id="send-btn"
          >
            {isSending ? (
              <span className="animate-pulse font-mono text-xs">WAIT</span>
            ) : (
              <>
                <span className="font-mono text-xs">SEND</span>
                <span>↵</span>
              </>
            )}
          </button>
        </div>

        {/* Footer info */}
        <div className="mt-1.5 flex items-center gap-3 text-[10px] font-mono text-text-muted">
          <span>QA · ESSAY · ARTIFACT auto-detected</span>
          {isSending && (
            <span className="text-accent-amber animate-pulse">⟳ UPLINK ACTIVE</span>
          )}
        </div>
      </div>
    </div>
  );
}
