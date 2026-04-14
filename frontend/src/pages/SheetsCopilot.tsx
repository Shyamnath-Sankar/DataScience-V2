import Split from 'react-split'
import FileLibrary from '@/components/sheets/FileLibrary'
import SpreadsheetGrid from '@/components/sheets/SpreadsheetGrid'
import CopilotPanel from '@/components/sheets/CopilotPanel'
import OperationLog from '@/components/sheets/OperationLog'

export default function SheetsCopilot() {
  return (
    <div className="flex flex-col h-full relative">
      <div className="flex-1 overflow-hidden">
        <Split
          sizes={[15, 60, 25]}
          minSize={[200, 400, 300]}
          gutterSize={4}
          className="flex h-full"
          style={{ height: '100%' }}
        >
          <div className="h-full border-r" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border)' }}>
            <FileLibrary />
          </div>
          <div className="h-full relative z-10" style={{ background: 'var(--bg-surface)' }}>
            <SpreadsheetGrid />
          </div>
          <div className="h-full border-l" style={{ background: 'var(--bg-surface)', borderColor: 'var(--border)' }}>
            <CopilotPanel />
          </div>
        </Split>
      </div>
      <div className="border-t z-20" style={{ borderColor: 'var(--border)', background: 'var(--bg-surface)' }}>
        <OperationLog />
      </div>
    </div>
  )
}
