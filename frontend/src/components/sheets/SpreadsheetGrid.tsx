import { useEffect, useRef, useMemo } from 'react'
import { AgGridReact } from 'ag-grid-react'
import {
  AllCommunityModule,
  ModuleRegistry,
  themeQuartz,
  colorSchemeDark,
  colorSchemeLight,
} from 'ag-grid-community'
import { useFileStore } from '@/stores/fileStore'
import { useCopilotStore } from '@/stores/copilotStore'
import { useThemeStore } from '@/stores/themeStore'
import { fetchFullData } from '@/lib/api'
import { FileSpreadsheet } from 'lucide-react'

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule])

const darkGridTheme = themeQuartz.withPart(colorSchemeDark).withParams({
  backgroundColor: '#111113',
  foregroundColor: '#fafafa',
  headerBackgroundColor: '#09090b',
  accentColor: '#7c3aed',
  borderColor: '#222225',
  rowHoverColor: '#1e1e22',
  fontFamily: "'JetBrains Mono', monospace",
  fontSize: 13,
  headerFontSize: 11,
  rowHeight: 34,
  headerHeight: 38,
})

const lightGridTheme = themeQuartz.withPart(colorSchemeLight).withParams({
  backgroundColor: '#ffffff',
  foregroundColor: '#1a1a1a',
  headerBackgroundColor: '#f5f5f5',
  accentColor: '#217346',
  borderColor: '#e5e7eb',
  rowHoverColor: '#f0fdf4',
  fontFamily: "'JetBrains Mono', monospace",
  fontSize: 13,
  headerFontSize: 11,
  rowHeight: 34,
  headerHeight: 38,
})

export default function SpreadsheetGrid() {
  const gridRef = useRef<AgGridReact>(null)
  const { activeFileId } = useFileStore()
  const activeFile = useFileStore((s) => s.files.find((f) => f.id === s.activeFileId))
  const { gridData, setGridData } = useCopilotStore()
  const { theme } = useThemeStore()

  const gridTheme = theme === 'dark' ? darkGridTheme : lightGridTheme

  // Load data when active file changes
  useEffect(() => {
    if (!activeFileId) {
      setGridData(null)
      return
    }
    fetchFullData(activeFileId)
      .then((data) => {
        setGridData({
          rows: data.rows,
          columns: data.columns.map((c: any) => ({
            field: c.name,
            headerName: c.name,
            sortable: true,
            filter: true,
            resizable: true,
            editable: true,
            minWidth: 100,
          })),
        })
      })
      .catch(() => setGridData(null))
  }, [activeFileId, setGridData])

  if (!activeFileId || !gridData) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4"
           style={{ background: 'var(--bg-surface)' }}>
        <div className="w-16 h-16 rounded-2xl flex items-center justify-center border"
             style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}>
          <FileSpreadsheet size={28} style={{ color: 'var(--text-dim)' }} />
        </div>
        <div className="text-center">
          <p className="text-[15px] font-semibold tracking-wide" style={{ color: 'var(--text-primary)' }}>
            No file selected
          </p>
          <p className="text-[13px] mt-1.5" style={{ color: 'var(--text-dim)' }}>
            Choose a file from the library to view it here
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full relative" style={{ background: 'var(--bg-surface)' }}>
      {/* Header bar */}
      <div className="flex items-center justify-between px-5 h-12 shrink-0 border-b relative z-10 w-full"
           style={{ borderColor: 'var(--border)', background: 'var(--bg-surface)' }}>
        <div className="flex items-center gap-2.5">
          <FileSpreadsheet size={16} style={{ color: 'var(--accent)' }} />
          <span className="text-[14px] font-semibold tracking-wide" style={{ color: 'var(--text-primary)' }}>
            {activeFile?.original_name}
          </span>
        </div>
        <span className="text-[11px] font-mono font-medium tracking-widest uppercase" style={{ color: 'var(--text-muted)' }}>
          {gridData.rows.length.toLocaleString()} rows × {gridData.columns.length} cols
        </span>
      </div>

      {/* Grid */}
      <div className="flex-1 w-full">
        <AgGridReact
          ref={gridRef}
          theme={gridTheme}
          rowData={gridData.rows}
          columnDefs={gridData.columns}
          defaultColDef={{
            sortable: true,
            filter: true,
            resizable: true,
            minWidth: 80,
          }}
          animateRows={true}
          enableCellTextSelection={true}
          suppressMovableColumns={false}
          rowSelection="multiple"
        />
      </div>
    </div>
  )
}
