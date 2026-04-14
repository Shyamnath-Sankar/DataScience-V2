import { useAgentStore } from '@/stores/agentStore'

const MODES = [
  { id: null, label: 'Auto' },
  { id: 'eda', label: 'EDA' },
  { id: 'visualization', label: 'Visualizer' },
  { id: 'code', label: 'Code' },
  { id: 'sql', label: 'SQL' },
]

export default function AgentModePicker() {
  const { pinnedMode, setPinnedMode } = useAgentStore()

  return (
    <div className="flex items-center gap-1 px-3 py-2 border-b" style={{ borderColor: 'var(--border)' }}>
      <span className="text-[10px] font-semibold uppercase tracking-wider mr-1.5" style={{ color: 'var(--text-dim)' }}>
        Mode
      </span>
      {MODES.map((mode) => (
        <button
          key={mode.label}
          onClick={() => setPinnedMode(mode.id)}
          className="px-2 py-1 rounded-md text-[11px] font-medium transition-all duration-150"
          style={{
            background: pinnedMode === mode.id ? 'var(--accent)' : 'var(--bg-card)',
            color: pinnedMode === mode.id ? 'white' : 'var(--text-muted)',
            border: `1px solid ${pinnedMode === mode.id ? 'var(--accent)' : 'var(--border)'}`,
          }}
        >
          {mode.label}
        </button>
      ))}
    </div>
  )
}
