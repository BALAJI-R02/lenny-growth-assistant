import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import type { Message } from '../types';
import { CitationChip } from './CitationChip';
import { RetrievalTrace } from './RetrievalTrace';

interface MessageBubbleProps {
  message: Message;
  isSending?: boolean;
}

function RouteTag({ route }: { route?: string }) {
  if (!route) return null;
  return (
    <span className={`route-tag ${route}`} aria-label={`Route: ${route}`}>
      {route}
    </span>
  );
}

function LatencyBadge({ ms }: { ms?: number }) {
  if (!ms) return null;
  return (
    <span className="text-[10px] font-mono text-text-muted">
      {ms}ms
    </span>
  );
}

export function MessageBubble({ message, isSending }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isNoIntel = message.content.includes('NO INTEL FOUND');
  const isError = message.content.includes('UPLINK FAILURE') || message.content.startsWith('⚠');

  return (
    <div
      className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} gap-1 animate-slide-in`}
    >
      {/* Role label */}
      <div className={`flex items-center gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
        <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider">
          {isUser ? 'OPERATOR' : 'ASSISTANT'}
        </span>
        {!isUser && <RouteTag route={message.route} />}
        {!isUser && <LatencyBadge ms={message.latency_ms} />}
      </div>

      {/* Message bubble */}
      <div
        className={`${isUser ? 'msg-user' : 'msg-assistant'} ${isNoIntel ? 'msg-no-intel' : ''} ${isError ? 'msg-error' : ''}`}
        aria-live={!isUser ? 'polite' : undefined}
        role={!isUser ? 'log' : undefined}
      >
        {isUser ? (
          <p className="text-sm" style={{ color: '#e2e8f0' }}>{message.content}</p>
        ) : (
          <div className="prose-soc">
            {isSending ? (
              <div className="cursor-blink text-sm">Processing</div>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeSanitize]}
                components={{
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: '#00d4ff' }}
                    >
                      {children}
                    </a>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            )}
          </div>
        )}
      </div>

      {/* EVIDENCE chips */}
      {!isUser && message.citations && message.citations.length > 0 && (
        <div
          className="flex flex-wrap gap-1.5 mt-1"
          role="region"
          aria-label="Evidence sources"
        >
          <span className="text-[10px] font-mono text-text-muted uppercase tracking-wider self-center">
            EVIDENCE:
          </span>
          {message.citations.map((citation) => (
            <CitationChip key={citation.ref} citation={citation} />
          ))}
        </div>
      )}

      {/* Retrieval trace */}
      {!isUser && message.retrieval_chunks && message.retrieval_chunks.length > 0 && (
        <RetrievalTrace chunks={message.retrieval_chunks} />
      )}

      {/* Timestamp */}
      <span className="text-[10px] font-mono text-text-muted opacity-50">
        {new Date(message.created_at).toLocaleTimeString()}
      </span>
    </div>
  );
}
