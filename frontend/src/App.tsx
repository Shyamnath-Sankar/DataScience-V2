import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import Navbar from './components/layout/Navbar'
import SheetsCopilot from './pages/SheetsCopilot'
import AgentChat from './pages/AgentChat'
import Settings from './pages/Settings'
import { useThemeStore } from './stores/themeStore'

export default function App() {
  const { theme } = useThemeStore()

  // Sync theme on initial mount
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-mesh animate-mesh-pan"
         style={{ background: 'var(--bg-base)' }}>
      <Navbar />
      <main className="flex-1 overflow-hidden relative z-10">
        <Routes>
          <Route path="/" element={<Navigate to="/sheets" replace />} />
          <Route path="/sheets" element={<SheetsCopilot />} />
          <Route path="/agent" element={<AgentChat />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}
