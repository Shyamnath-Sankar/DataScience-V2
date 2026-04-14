import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import TableCard from './TableCard'

interface SQLOutputCardProps {
  data: {
    sql?: string
    columns?: string[]
    rows?: Record<string, any>[]
    total_rows?: number
  }
}

export default function SQLOutputCard({ data }: SQLOutputCardProps) {
  return (
    <div className="flex flex-col gap-3">
      {/* SQL Query */}
      {data.sql && (
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--text-dim)' }}>
            SQL Query
          </p>
          <div className="rounded-lg overflow-hidden border" style={{ borderColor: 'var(--border)' }}>
            <SyntaxHighlighter
              language="sql"
              style={oneDark}
              customStyle={{
                background: 'var(--bg-base)',
                margin: 0,
                padding: '12px 16px',
                fontSize: '12px',
                lineHeight: '1.6',
                fontFamily: 'var(--font-mono)',
              }}
            >
              {data.sql}
            </SyntaxHighlighter>
          </div>
        </div>
      )}

      {/* Result table */}
      {data.rows && (
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--text-dim)' }}>
            Result
          </p>
          <TableCard data={{ columns: data.columns, rows: data.rows, total_rows: data.total_rows }} />
        </div>
      )}
    </div>
  )
}
