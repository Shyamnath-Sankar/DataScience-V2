import { useCopilotStore } from '@/stores/copilotStore'
import { useFileStore } from '@/stores/fileStore'
import { revertOperation, revertLast, fetchFullData } from '@/lib/api'
import { Undo2, RotateCcw } from 'lucide-react'
import { toast } from 'sonner'

export default function OperationLog() {
  const { operations, sessionId, setOperations, setGridData } = useCopilotStore()
  const { activeFileId } = useFileStore()

  const handleRevert = async (operationId: string) => {
    if (!activeFileId) return
    try {
      const result = await revertOperation(sessionId, operationId)
      // Update grid
      setGridData({
        rows: result.rows,
        columns: result.columns.map((c: any) => ({
          field: c.name,
          headerName: c.name,
          sortable: true,
          filter: true,
          resizable: true,
          editable: true,
          minWidth: 100,
        })),
      })
      // Remove reverted operations
      const idx = operations.findIndex((o) => o.id === operationId)
      if (idx !== -1) {
        setOperations(operations.slice(0, idx))
      }
      toast.success(`Reverted ${result.reverted_count} operation(s)`)
    } catch {
      toast.error('Revert failed.')
    }
  }

  const handleRevertLast = async () => {
    if (!activeFileId || operations.length === 0) return
    try {
      const result = await revertLast(sessionId)
      setGridData({
        rows: result.rows,
        columns: result.columns.map((c: any) => ({
          field: c.name,
          headerName: c.name,
          sortable: true,
          filter: true,
          resizable: true,
          editable: true,
          minWidth: 100,
        })),
      })
      setOperations(operations.slice(0, -1))
      toast.success('Reverted last operation')
    } catch {
      toast.error('Revert failed.')
    }
  }

  return (
    <div
      className="flex items-center h-14 px-3 border-t shrink-0 gap-2"
      style={{ background: 'var(--bg-surface)', borderColor: 'var(--border)' }}
    >
      <span className="text-[10px] font-semibold uppercase tracking-wider shrink-0 mr-1"
        style={{ color: 'var(--text-dim)' }}>
        Log
      </span>

      {/* Scrollable operation pills */}
      <div className="flex-1 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
        {operations.length === 0 ? (
          <span className="text-xs" style={{ color: 'var(--text-dim)' }}>
            No operations yet
          </span>
        ) : (
          operations.map((op, i) => (
            <button
              key={op.id}
              className="group flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-medium whitespace-nowrap shrink-0 transition-all duration-150 hover:border-[var(--accent-border)]"
              style={{
                background: 'var(--bg-card)',
                borderColor: 'var(--border)',
                color: 'var(--text-secondary)',
              }}
              onClick={() => handleRevert(op.id)}
              title={`Revert: ${op.description}`}
            >
              <span className="text-[10px] font-mono" style={{ color: 'var(--text-dim)' }}>
                {i + 1}
              </span>
              <span className="max-w-40 truncate">{op.description}</span>
              <Undo2 size={10} className="opacity-0 group-hover:opacity-100 transition-opacity"
                style={{ color: 'var(--accent)' }} />
            </button>
          ))
        )}
      </div>

      {/* Revert Last button */}
      {operations.length > 0 && (
        <button
          onClick={handleRevertLast}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium shrink-0 transition-all duration-150"
          style={{
            background: 'var(--destructive-muted)',
            color: 'var(--destructive)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
          }}
        >
          <RotateCcw size={11} />
          Undo
        </button>
      )}
    </div>
  )
}
