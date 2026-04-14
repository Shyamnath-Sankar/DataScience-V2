import { useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface TableCardProps {
  data: {
    columns?: string[]
    rows?: Record<string, any>[]
    total_rows?: number
  }
}

const PAGE_SIZE = 50

export default function TableCard({ data }: TableCardProps) {
  const [page, setPage] = useState(0)
  const rows = data.rows || []
  const columns = data.columns || (rows.length > 0 ? Object.keys(rows[0]) : [])
  const totalPages = Math.ceil(rows.length / PAGE_SIZE)
  const pageRows = rows.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <div>
      <div className="overflow-x-auto rounded-lg border" style={{ borderColor: 'var(--border)' }}>
        <table className="w-full text-xs">
          <thead>
            <tr style={{ background: 'var(--bg-base)' }}>
              {columns.map((col) => (
                <th key={col} className="px-3 py-2 text-left font-semibold whitespace-nowrap"
                  style={{ color: 'var(--text-muted)', borderBottom: '1px solid var(--border)' }}>
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr key={i} className="transition-colors" style={{ borderBottom: '1px solid var(--border)' }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-elevated)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}>
                {columns.map((col) => (
                  <td key={col} className="px-3 py-1.5 font-mono whitespace-nowrap"
                    style={{ color: 'var(--text-primary)' }}>
                    {row[col] != null ? String(row[col]) : '—'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between mt-2.5">
        <span className="text-[11px]" style={{ color: 'var(--text-dim)' }}>
          {data.total_rows?.toLocaleString() || rows.length} rows
        </span>
        {totalPages > 1 && (
          <div className="flex items-center gap-1.5">
            <button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0}
              className="p-1 rounded" style={{ color: page === 0 ? 'var(--text-dim)' : 'var(--text-muted)' }}>
              <ChevronLeft size={14} />
            </button>
            <span className="text-[11px] font-mono" style={{ color: 'var(--text-muted)' }}>
              {page + 1}/{totalPages}
            </span>
            <button onClick={() => setPage(Math.min(totalPages - 1, page + 1))} disabled={page >= totalPages - 1}
              className="p-1 rounded" style={{ color: page >= totalPages - 1 ? 'var(--text-dim)' : 'var(--text-muted)' }}>
              <ChevronRight size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
