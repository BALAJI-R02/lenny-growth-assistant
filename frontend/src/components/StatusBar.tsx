import { useChatStore } from '../store/chatStore';

const UPLINK_CONFIG = {
  LOCAL: { label: 'LOCAL', color: '#39ff14', pulse: true },
  CLOUD: { label: 'CLOUD', color: '#00d4ff', pulse: true },
  FALLBACK: { label: 'FALLBACK', color: '#ffb347', pulse: false },
  OFFLINE: { label: 'OFFLINE', color: '#ff4444', pulse: false },
  CHECKING: { label: 'CHECKING', color: '#7a8599', pulse: false },
};

export function StatusBar() {
  const { health, uplinkStatus } = useChatStore();
  const uplink = UPLINK_CONFIG[uplinkStatus];

  const dbStatus = health?.db ?? 'checking';
  const indexStatus = health?.index ?? 'checking';
  const chunkCount = health?.chunk_count ?? 0;
  const model = health ? `${health.provider}/${health.model}` : '—';

  return (
    <div
      className="flex items-center justify-between px-4 py-1.5 border-b text-xs font-mono"
      style={{ borderColor: '#1e2330', background: '#0d0f14' }}
      role="status"
      aria-label="System status"
    >
      {/* Left: indicators */}
      <div className="flex items-center gap-4">
        {/* DB */}
        <div className="flex items-center gap-1.5">
          <span
            className="status-dot"
            style={{
              background: dbStatus === 'ok' ? '#39ff14' : dbStatus === 'down' ? '#ff4444' : '#7a8599',
              boxShadow: dbStatus === 'ok' ? '0 0 6px #39ff14' : undefined,
            }}
          />
          <span className="text-text-secondary uppercase tracking-wider">DB</span>
          <span style={{ color: dbStatus === 'ok' ? '#39ff14' : '#ff4444' }}>
            {dbStatus.toUpperCase()}
          </span>
        </div>

        {/* INDEX */}
        <div className="flex items-center gap-1.5">
          <span
            className="status-dot"
            style={{
              background: indexStatus === 'ok' ? '#39ff14' : indexStatus === 'empty' ? '#ffb347' : '#7a8599',
            }}
          />
          <span className="text-text-secondary uppercase tracking-wider">INDEX</span>
          <span style={{ color: indexStatus === 'ok' ? '#39ff14' : '#ffb347' }}>
            {indexStatus === 'ok' ? `${chunkCount.toLocaleString()} CHUNKS` : indexStatus.toUpperCase()}
          </span>
        </div>

        {/* MODEL */}
        <div className="flex items-center gap-1.5">
          <span className="text-text-secondary uppercase tracking-wider">MODEL</span>
          <span className="text-accent-cyan">{model}</span>
        </div>

        {/* SANDBOX */}
        <div className="flex items-center gap-1.5">
          <span
            className="status-dot"
            style={{ background: '#39ff14', boxShadow: '0 0 6px #39ff14' }}
          />
          <span className="text-text-secondary uppercase tracking-wider">SANDBOX</span>
          <span style={{ color: '#39ff14' }}>ACTIVE</span>
        </div>
      </div>

      {/* Right: UPLINK */}
      <div className="flex items-center gap-2">
        <span className="text-text-secondary uppercase tracking-wider">UPLINK</span>
        <span
          className="font-semibold tracking-widest"
          style={{
            color: uplink.color,
            textShadow: uplink.pulse ? `0 0 8px ${uplink.color}` : undefined,
          }}
        >
          {uplink.label}
        </span>
        {uplinkStatus === 'FALLBACK' && (
          <span className="text-accent-amber">⚠ AUTO-SWITCHED</span>
        )}
      </div>
    </div>
  );
}
