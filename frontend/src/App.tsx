import { useCallback, useState } from 'react';
import { BootSequence } from './components/BootSequence';
import { StatusBar } from './components/StatusBar';
import { ChatPanel } from './components/ChatPanel';
import { ArtifactViewer } from './components/ArtifactViewer';
import { useChatStore } from './store/chatStore';

type ActiveTab = 'operations' | 'payload';

export default function App() {
  const [booted, setBooted] = useState(false);
  const [activeTab, setActiveTab] = useState<ActiveTab>('operations');
  const { setIsBooted } = useChatStore();

  const handleBootComplete = useCallback(() => {
    setBooted(true);
    setIsBooted(true);
  }, [setIsBooted]);

  return (
    <>
      {!booted && <BootSequence onComplete={handleBootComplete} />}

      {booted && (
        <div className="flex flex-col h-screen" style={{ background: '#0a0c0f' }}>
          {/* Status bar */}
          <StatusBar />

          {/* Mobile tab bar */}
          <div
            className="flex md:hidden border-b"
            style={{ borderColor: '#1e2330', background: '#0d0f14' }}
            role="tablist"
            aria-label="Panel navigation"
          >
            <button
              className={`flex-1 py-2.5 text-xs font-mono uppercase tracking-wider transition-colors ${activeTab === 'operations' ? 'text-accent-green border-b-2' : 'text-text-muted'}`}
              style={activeTab === 'operations' ? { borderColor: '#39ff14' } : {}}
              onClick={() => setActiveTab('operations')}
              role="tab"
              aria-selected={activeTab === 'operations'}
              aria-controls="panel-operations"
              id="tab-operations"
            >
              ◈ OPERATIONS
            </button>
            <button
              className={`flex-1 py-2.5 text-xs font-mono uppercase tracking-wider transition-colors ${activeTab === 'payload' ? 'text-accent-amber border-b-2' : 'text-text-muted'}`}
              style={activeTab === 'payload' ? { borderColor: '#ffb347' } : {}}
              onClick={() => setActiveTab('payload')}
              role="tab"
              aria-selected={activeTab === 'payload'}
              aria-controls="panel-payload"
              id="tab-payload"
            >
              ◫ PAYLOAD
            </button>
          </div>

          {/* Main layout */}
          <div className="flex flex-1 overflow-hidden">
            {/* Desktop: split pane | Mobile: tab-controlled */}
            <div
              id="panel-operations"
              role="tabpanel"
              aria-labelledby="tab-operations"
              className={`
                md:flex md:flex-col md:w-[45%]
                ${activeTab === 'operations' ? 'flex flex-col w-full' : 'hidden'}
              `}
              style={{ minWidth: 0 }}
            >
              <ChatPanel />
            </div>

            {/* Divider (desktop only) */}
            <div
              className="hidden md:block w-px flex-shrink-0"
              style={{ background: '#1e2330' }}
            />

            {/* Artifact viewer */}
            <div
              id="panel-payload"
              role="tabpanel"
              aria-labelledby="tab-payload"
              className={`
                md:flex md:flex-col md:flex-1
                ${activeTab === 'payload' ? 'flex flex-col w-full' : 'hidden'}
              `}
              style={{ minWidth: 0 }}
            >
              <ArtifactViewer />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
