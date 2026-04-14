import { useEffect } from 'react'
import { useFileStore } from '@/stores/fileStore'
import { fetchFiles } from '@/lib/api'
import FileUploader from '@/components/shared/FileUploader'
import { FileSpreadsheet, Trash2 } from 'lucide-react'
import { deleteFile as apiDeleteFile } from '@/lib/api'
import { toast } from 'sonner'

export default function FileLibrary() {
  const { files, activeFileId, setFiles, setActiveFile, removeFile } = useFileStore()

  useEffect(() => {
    fetchFiles().then(setFiles).catch(() => {})
  }, [setFiles])

  const handleDelete = async (e: React.MouseEvent, fileId: string) => {
    e.stopPropagation()
    try {
      await apiDeleteFile(fileId)
      removeFile(fileId)
      toast.success('File deleted.')
    } catch {
      toast.error('Failed to delete file.')
    }
  }

  return (
    <div className="flex flex-col h-full" style={{ background: 'var(--bg-surface)' }}>
      {/* Header */}
      <div className="px-3 py-2.5 border-b" style={{ borderColor: 'var(--border)' }}>
        <h2 className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
          Files
        </h2>
      </div>

      {/* Upload */}
      <div className="px-3 py-2">
        <FileUploader />
      </div>

      {/* File List */}
      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {files.length === 0 ? (
          <p className="text-xs text-center py-6" style={{ color: 'var(--text-dim)' }}>
            No files uploaded yet
          </p>
        ) : (
          <div className="flex flex-col gap-0.5">
            {files.map((file) => (
              <button
                key={file.id}
                onClick={() => setActiveFile(file.id)}
                className="group flex items-start gap-2 w-full text-left px-2.5 py-2 rounded-md transition-all duration-150"
                style={{
                  background: activeFileId === file.id ? 'var(--accent-muted)' : 'transparent',
                  border: `1px solid ${activeFileId === file.id ? 'var(--accent-border)' : 'transparent'}`,
                }}
              >
                <FileSpreadsheet
                  size={14}
                  className="mt-0.5 shrink-0"
                  style={{ color: activeFileId === file.id ? 'var(--accent)' : 'var(--text-dim)' }}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate font-medium" style={{ color: 'var(--text-primary)' }}>
                    {file.original_name}
                  </p>
                  <p className="text-[11px]" style={{ color: 'var(--text-dim)' }}>
                    {file.row_count.toLocaleString()} rows · {file.col_count} cols
                  </p>
                </div>
                <button
                  onClick={(e) => handleDelete(e, file.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded transition-opacity"
                  style={{ color: 'var(--text-dim)' }}
                >
                  <Trash2 size={12} />
                </button>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
