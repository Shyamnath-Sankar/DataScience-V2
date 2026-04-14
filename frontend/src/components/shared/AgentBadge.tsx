const AGENT_COLORS: Record<string, string> = {
  'EDA Agent': '#14b8a6',
  'Visualizer Agent': '#7c3aed',
  'Code Executor': '#f59e0b',
  'SQL Agent': '#3b82f6',
  'Assistant': '#71717a',
}

export default function AgentBadge({ name }: { name: string }) {
  const color = AGENT_COLORS[name] || 'var(--text-muted)'
  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider"
      style={{
        background: `${color}18`,
        color,
        border: `1px solid ${color}30`,
      }}
    >
      {name}
    </span>
  )
}
