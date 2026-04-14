import { NavLink } from 'react-router-dom'
import { Grid3X3, MessageSquareMore, Sparkles, Settings, Sun, Moon } from 'lucide-react'
import { useThemeStore } from '@/stores/themeStore'

export default function Navbar() {
  const { theme, toggleTheme } = useThemeStore()

  return (
    <nav className="flex items-center h-14 px-5 border-b shrink-0 relative z-50 transition-colors duration-300"
         style={{ 
           background: 'var(--bg-surface)', 
           borderColor: 'var(--border)',
         }}>
      
      {/* Background Glow — only visible in dark */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[var(--accent-glow)] to-transparent" />

      {/* Logo */}
      <div className="flex items-center gap-3 mr-10 group cursor-default">
        <div className="w-7 h-7 rounded-lg flex items-center justify-center transition-transform group-hover:scale-105"
             style={{ 
               background: `linear-gradient(135deg, var(--accent), var(--accent-hover))`,
               boxShadow: '0 0 10px var(--accent-glow)',
             }}>
          <Sparkles size={14} className="text-white" />
        </div>
        <span className="text-[15px] font-semibold tracking-tight" style={{ color: 'var(--text-primary)' }}>
          DataSci <span style={{ color: 'var(--accent)' }} className="font-bold">AI</span>
        </span>
      </div>

      {/* Nav Links */}
      <div className="flex items-center gap-2">
        <NavLink
          to="/sheets"
          className={({ isActive }) =>
            `flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-[13px] font-medium transition-all duration-300 border ${
              isActive
                ? 'border-[var(--accent-border)] ring-1 ring-[var(--accent-border)]'
                : 'border-transparent hover:border-[var(--border-hover)]'
            }`
          }
          style={({ isActive }) => ({
            background: isActive ? 'var(--accent-muted)' : 'transparent',
            color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
          })}
        >
          <Grid3X3 size={15} className="opacity-80" />
          Sheets Copilot
        </NavLink>

        <NavLink
          to="/agent"
          className={({ isActive }) =>
            `flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-[13px] font-medium transition-all duration-300 border ${
              isActive
                ? 'border-[var(--accent-border)] ring-1 ring-[var(--accent-border)]'
                : 'border-transparent hover:border-[var(--border-hover)]'
            }`
          }
          style={({ isActive }) => ({
            background: isActive ? 'var(--accent-muted)' : 'transparent',
            color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
          })}
        >
          <MessageSquareMore size={15} className="opacity-80" />
          Agent Chat
        </NavLink>
      </div>

      {/* Right side: settings + theme toggle */}
      <div className="flex items-center gap-2 ml-auto">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-300 border"
          style={{
            borderColor: 'var(--border)',
            background: 'var(--bg-elevated)',
            color: 'var(--text-muted)',
          }}
          title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
          {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
        </button>

        {/* Settings link */}
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-300 border ${
              isActive ? 'border-[var(--accent-border)]' : 'border-[var(--border)]'
            }`
          }
          style={({ isActive }) => ({
            background: isActive ? 'var(--accent-muted)' : 'var(--bg-elevated)',
            color: isActive ? 'var(--accent)' : 'var(--text-muted)',
          })}
          title="Settings"
        >
          <Settings size={15} />
        </NavLink>
      </div>
    </nav>
  )
}
