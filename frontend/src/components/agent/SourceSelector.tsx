import { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useFileStore } from '@/stores/fileStore'
import { useAgentStore } from '@/stores/agentStore'
import { fetchFiles } from '@/lib/api'
import { FileSpreadsheet, Database, Check } from 'lucide-react'

export default function SourceSelector() {
  const [searchParams] = useSearchParams()
  const { files, setFiles } = useFileStore()
  const { sourceType, activeFileId, dbConnected, dbTables, setSource, setDbConnected } = useAgentStore()

  useEffect(() => {
    fetchFiles().then(setFiles).catch(() => {})
  }, [setFiles])

  // Auto-select file from URL param
  useEffect(() => {
    const fileId = searchParams.get('file_id')
    if (fileId && files.find((f) => f.id === fileId)) {
      setSource('file', fileId)
    }
  }, [searchParams, files, setSource])

  const activeFileName = files.find((f) => f.id === activeFileId)?.original_name

  return (
    <div className="border-b px-4 py-3" style={{ borderColor: 'var(--border)', background: 'var(--bg-surface)' }}>
      <p className="text-[10px] font-bold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
        Data Source
      </p>

      {/* Tabs */}
      <div className="flex gap-2 mb-3">
        <button
          onClick={() => setSource('file')}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all duration-300 border"
          style={{
            background: sourceType === 'file' ? 'var(--accent-muted)' : 'var(--bg-card)',
            color: sourceType === 'file' ? 'var(--text-primary)' : 'var(--text-muted)',
            borderColor: sourceType === 'file' ? 'var(--accent-border)' : 'var(--border)',
          }}
        >
          <FileSpreadsheet size={13} style={{ color: sourceType === 'file' ? 'var(--accent)' : 'var(--text-dim)' }} />
          File
        </button>
        <button
          onClick={() => setSource('database')}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all duration-300 border"
          style={{
            background: sourceType === 'database' ? 'var(--accent-muted)' : 'var(--bg-card)',
            color: sourceType === 'database' ? 'var(--text-primary)' : 'var(--text-muted)',
            borderColor: sourceType === 'database' ? 'var(--accent-border)' : 'var(--border)',
          }}
        >
          <Database size={13} style={{ color: sourceType === 'database' ? 'var(--accent)' : 'var(--text-dim)' }} />
          Database
        </button>
      </div>

      {/* File selector */}
      {sourceType === 'file' && (
        <select
          value={activeFileId || ''}
          onChange={(e) => setSource('file', e.target.value || null)}
          className="w-full text-[13px] rounded-lg px-3 py-2 outline-none border transition-all font-sans cursor-pointer"
          style={{
            backgroundColor: 'var(--select-bg)',
            color: 'var(--select-text)',
            borderColor: 'var(--border)',
          }}
        >
          <option value="">Select a file...</option>
          {files.map((f) => (
            <option key={f.id} value={f.id}>
              {f.original_name} ({f.row_count} rows)
            </option>
          ))}
        </select>
      )}

      {/* DB connection status */}
      {sourceType === 'database' && dbConnected && (
        <div className="flex items-center gap-2 text-xs font-semibold px-3 py-2 rounded-lg"
             style={{ background: 'var(--success-muted)', color: 'var(--success)' }}>
          <Check size={14} />
          Connected · {dbTables.length} tables
        </div>
      )}

      {/* Active indicator */}
      {activeFileName && sourceType === 'file' && (
        <div className="flex items-center gap-2 mt-3 text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
          <FileSpreadsheet size={13} style={{ color: 'var(--accent)' }} />
          {activeFileName}
        </div>
      )}
    </div>
  )
}
