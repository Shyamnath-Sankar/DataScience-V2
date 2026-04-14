import { useCallback, useRef, useState } from 'react'
import { Upload, FileSpreadsheet, X } from 'lucide-react'
import { uploadFile } from '@/lib/api'
import { useFileStore } from '@/stores/fileStore'
import { toast } from 'sonner'

export default function FileUploader() {
  const [isDragging, setIsDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const { addFile, setUploading, isUploading } = useFileStore()

  const handleFiles = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return
    const file = files[0]
    const ext = file.name.split('.').pop()?.toLowerCase()

    if (ext !== 'csv' && ext !== 'xlsx') {
      toast.error('Only .csv and .xlsx files are supported.')
      return
    }

    setUploading(true)
    try {
      const record = await uploadFile(file)
      addFile(record)
      toast.success(`Uploaded ${record.original_name} · ${record.row_count} rows`)
    } catch (e: any) {
      toast.error(e.message || 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }, [addFile, setUploading])

  return (
    <div
      className={`relative border border-dashed rounded-lg p-3 text-center cursor-pointer transition-all duration-200 ${
        isDragging ? 'border-[var(--accent)]' : 'border-[var(--border-hover)]'
      }`}
      style={{
        background: isDragging ? 'var(--accent-glow)' : 'transparent',
      }}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setIsDragging(false)
        handleFiles(e.dataTransfer.files)
      }}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xlsx"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      {isUploading ? (
        <div className="flex flex-col items-center gap-1.5 py-1">
          <div className="w-5 h-5 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Uploading...</span>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-1.5 py-1">
          <Upload size={16} style={{ color: 'var(--text-muted)' }} />
          <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
            Drop CSV or XLSX
          </span>
        </div>
      )}
    </div>
  )
}
