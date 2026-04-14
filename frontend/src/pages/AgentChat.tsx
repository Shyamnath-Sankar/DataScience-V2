import Split from 'react-split'
import SourceSelector from '@/components/agent/SourceSelector'
import AgentModePicker from '@/components/agent/AgentModePicker'
import ChatThread from '@/components/agent/ChatThread'
import Canvas from '@/components/agent/Canvas'

export default function AgentChat() {
  return (
    <div className="relative h-full w-full">
      <Split
        sizes={[40, 60]}
        minSize={[320, 450]}
        gutterSize={4}
        className="flex h-full relative z-10"
        style={{ height: '100%' }}
      >
        {/* Left panel: source + mode + chat */}
        <div className="flex flex-col h-full overflow-hidden border-r"
             style={{ background: 'var(--bg-surface)', borderColor: 'var(--border)' }}>
          <SourceSelector />
          <AgentModePicker />
          <div className="flex-1 overflow-hidden relative">
            <ChatThread />
          </div>
        </div>

        {/* Right panel: canvas */}
        <div style={{ background: 'var(--bg-base)' }}><Canvas /></div>
      </Split>
    </div>
  )
}
