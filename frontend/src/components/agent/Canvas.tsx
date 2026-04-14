import { useAgentStore } from '@/stores/agentStore'
import { Trash2, Layout } from 'lucide-react'
import AgentBadge from '@/components/shared/AgentBadge'
import ChartCard from './cards/ChartCard'
import TableCard from './cards/TableCard'
import EDAReportCard from './cards/EDAReportCard'
import CodeOutputCard from './cards/CodeOutputCard'
import SQLOutputCard from './cards/SQLOutputCard'
import TextCard from './cards/TextCard'

export default function Canvas() {
  const { canvasOutputs, clearCanvas } = useAgentStore()

  const renderCard = (output: any) => {
    switch (output.type) {
      case 'chart': return <ChartCard data={output.data} />
      case 'table': return <TableCard data={output.data} />
      case 'eda': return <EDAReportCard data={output.data} />
      case 'code_output': return <CodeOutputCard data={output.data} />
      case 'sql_output': return <SQLOutputCard data={output.data} />
      case 'text': return <TextCard data={output.data} />
      default: return null
    }
  }

  return (
    <div className="flex flex-col h-full" style={{ background: 'var(--bg-base)' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b shrink-0"
        style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-2">
          <Layout size={14} style={{ color: 'var(--text-muted)' }} />
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
            Canvas
          </span>
          {canvasOutputs.length > 0 && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full font-mono"
              style={{ background: 'var(--bg-card)', color: 'var(--text-dim)' }}>
              {canvasOutputs.length}
            </span>
          )}
        </div>
        {canvasOutputs.length > 0 && (
          <button
            onClick={clearCanvas}
            className="flex items-center gap-1 text-[10px] font-medium px-2 py-1 rounded-md transition-colors"
            style={{ color: 'var(--text-dim)', background: 'var(--bg-card)' }}
          >
            <Trash2 size={10} />
            Clear
          </button>
        )}
      </div>

      {/* Output cards */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
        {canvasOutputs.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 rounded-xl flex items-center justify-center mb-3"
              style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
              <Layout size={28} style={{ color: 'var(--text-dim)' }} />
            </div>
            <p className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
              No outputs yet
            </p>
            <p className="text-xs mt-1.5 max-w-52" style={{ color: 'var(--text-dim)' }}>
              Start a conversation and analysis results will appear here
            </p>
          </div>
        ) : (
          canvasOutputs.map((output) => (
            <div key={output.id} className="animate-slide-up rounded-xl border overflow-hidden"
              style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}>
              {/* Card header */}
              <div className="flex items-center justify-between px-4 py-2.5 border-b"
                style={{ borderColor: 'var(--border)' }}>
                <AgentBadge name={output.agentName} />
                <span className="text-[10px] font-mono" style={{ color: 'var(--text-dim)' }}>
                  {new Date(output.timestamp).toLocaleTimeString()}
                </span>
              </div>
              {/* Card content */}
              <div className="p-4">
                {renderCard(output)}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
