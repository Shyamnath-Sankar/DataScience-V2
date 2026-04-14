import { useThemeStore, type Theme } from '@/stores/themeStore'
import { Sun, Moon, Monitor, Palette, Info, Code, Sparkles } from 'lucide-react'

const themes: { id: Theme; label: string; desc: string; icon: React.ReactNode; preview: string }[] = [
  {
    id: 'dark',
    label: 'Dark Mode',
    desc: 'Deep dark with violet accents and glassmorphic panels. Perfect for night-time data crunching.',
    icon: <Moon size={20} />,
    preview: 'bg-gradient-to-br from-[#0a0a0f] to-[#1a1a26]',
  },
  {
    id: 'light',
    label: 'Light Mode',
    desc: 'Excel-inspired clean white with green accents. Familiar spreadsheet feel for daytime work.',
    icon: <Sun size={20} />,
    preview: 'bg-gradient-to-br from-[#f5f5f5] to-[#ffffff]',
  },
]

export default function Settings() {
  const { theme, setTheme } = useThemeStore()

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-2xl mx-auto px-6 py-10">
        {/* Page header */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-[var(--accent-muted)] border border-[var(--accent-border)]">
              <Sparkles size={18} style={{ color: 'var(--accent)' }} />
            </div>
            <h1 className="text-2xl font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>
              Settings
            </h1>
          </div>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
            Customize the look and feel of your DataSci AI workspace.
          </p>
        </div>

        {/* Appearance Section */}
        <section className="mb-10">
          <div className="flex items-center gap-2 mb-5">
            <Palette size={16} style={{ color: 'var(--accent)' }} />
            <h2 className="text-sm font-bold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
              Appearance
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {themes.map((t) => {
              const isActive = theme === t.id
              return (
                <button
                  key={t.id}
                  onClick={() => setTheme(t.id)}
                  className={`group relative flex flex-col rounded-xl border transition-all duration-300 overflow-hidden text-left ${
                    isActive
                      ? 'border-[var(--accent)] ring-2 ring-[var(--accent-border)] shadow-lg'
                      : 'border-[var(--border)] hover:border-[var(--border-hover)] hover:shadow-md'
                  }`}
                  style={{ background: 'var(--bg-card)' }}
                >
                  {/* Preview strip */}
                  <div className={`h-20 w-full ${t.preview} relative`}>
                    {/* Mini mockup */}
                    <div className="absolute inset-3 rounded-lg flex gap-1 overflow-hidden" 
                         style={{ border: `1px solid ${t.id === 'dark' ? 'rgba(255,255,255,0.1)' : '#e5e7eb'}` }}>
                      {/* Sidebar mock */}
                      <div className="w-1/4 h-full" style={{ background: t.id === 'dark' ? '#0f0f17' : '#f0f0f0' }} />
                      {/* Main area mock */}
                      <div className="flex-1 flex flex-col gap-px p-1">
                        {[...Array(4)].map((_, i) => (
                          <div key={i} className="flex-1 rounded-sm" style={{ 
                            background: t.id === 'dark' ? '#1a1a26' : '#ffffff',
                            border: `1px solid ${t.id === 'dark' ? 'rgba(255,255,255,0.05)' : '#e5e7eb'}`,
                          }} />
                        ))}
                      </div>
                      {/* Sidebar 2 mock */}
                      <div className="w-1/4 h-full" style={{ background: t.id === 'dark' ? '#0f0f17' : '#f0f0f0' }} />
                    </div>

                    {/* Active badge */}
                    {isActive && (
                      <div className="absolute top-2 right-2 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider text-white"
                           style={{ background: 'var(--accent)' }}>
                        Active
                      </div>
                    )}
                  </div>

                  {/* Details */}
                  <div className="px-4 py-3.5">
                    <div className="flex items-center gap-2 mb-1">
                      <span style={{ color: isActive ? 'var(--accent)' : 'var(--text-muted)' }}>{t.icon}</span>
                      <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{t.label}</span>
                    </div>
                    <p className="text-xs leading-relaxed" style={{ color: 'var(--text-dim)' }}>{t.desc}</p>
                  </div>
                </button>
              )
            })}
          </div>
        </section>

        {/* About Section */}
        <section className="mb-10">
          <div className="flex items-center gap-2 mb-5">
            <Info size={16} style={{ color: 'var(--accent)' }} />
            <h2 className="text-sm font-bold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
              About
            </h2>
          </div>

          <div className="rounded-xl border p-5 space-y-4"
               style={{ borderColor: 'var(--border)', background: 'var(--bg-card)' }}>
            <div>
              <p className="text-sm font-semibold mb-0.5" style={{ color: 'var(--text-primary)' }}>
                DataSci AI Platform
              </p>
              <p className="text-xs" style={{ color: 'var(--text-dim)' }}>
                Version 1.0.0
              </p>
            </div>

            <div className="space-y-2.5">
              <InfoRow icon={<Code size={13} />} label="Backend" value="FastAPI + LangGraph" />
              <InfoRow icon={<Monitor size={13} />} label="Frontend" value="React + TypeScript + Vite" />
              <InfoRow icon={<Palette size={13} />} label="Styling" value="Tailwind CSS v3" />
            </div>

            <p className="text-xs leading-relaxed pt-2 border-t" 
               style={{ color: 'var(--text-dim)', borderColor: 'var(--border)' }}>
              Two-mode platform: <strong>Sheets Copilot</strong> for smart data editing with revertible operations, 
              and <strong>Agent Chat</strong> for deep data science analysis with multi-agent LangGraph orchestration.
            </p>
          </div>
        </section>

        {/* Keyboard Shortcuts */}
        <section>
          <div className="flex items-center gap-2 mb-5">
            <Code size={16} style={{ color: 'var(--accent)' }} />
            <h2 className="text-sm font-bold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
              Keyboard Shortcuts
            </h2>
          </div>

          <div className="rounded-xl border divide-y"
               style={{ borderColor: 'var(--border)', background: 'var(--bg-card)' }}>
            <ShortcutRow keys={['Enter']} action="Send message" />
            <ShortcutRow keys={['Shift', 'Enter']} action="New line in chat" />
            <ShortcutRow keys={['Ctrl', 'Z']} action="Revert last operation (Sheets)" />
          </div>
        </section>
      </div>
    </div>
  )
}

function InfoRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span style={{ color: 'var(--text-dim)' }}>{icon}</span>
        <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>{label}</span>
      </div>
      <span className="text-xs font-mono" style={{ color: 'var(--text-secondary)' }}>{value}</span>
    </div>
  )
}

function ShortcutRow({ keys, action }: { keys: string[]; action: string }) {
  return (
    <div className="flex items-center justify-between px-4 py-2.5" style={{ borderColor: 'var(--border)' }}>
      <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{action}</span>
      <div className="flex items-center gap-1">
        {keys.map((k, i) => (
          <span key={i}>
            <kbd className="px-2 py-0.5 rounded text-[11px] font-mono font-semibold border"
                 style={{ 
                   background: 'var(--bg-elevated)', 
                   borderColor: 'var(--border)', 
                   color: 'var(--text-secondary)' 
                 }}>
              {k}
            </kbd>
            {i < keys.length - 1 && <span className="text-[10px] mx-0.5" style={{ color: 'var(--text-dim)' }}>+</span>}
          </span>
        ))}
      </div>
    </div>
  )
}
