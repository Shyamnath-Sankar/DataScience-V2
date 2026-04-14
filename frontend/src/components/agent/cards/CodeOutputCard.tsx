import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import TableCard from './TableCard'

interface CodeOutputCardProps {
  data: {
    code?: string
    stdout?: string
    error?: string | null
    result_table?: {
      columns: string[]
      rows: Record<string, any>[]
      total_rows: number
    } | null
  }
}

export default function CodeOutputCard({ data }: CodeOutputCardProps) {
  return (
    <div className="flex flex-col gap-3">
      {/* Code */}
      {data.code && (
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--text-dim)' }}>
            Python Code
          </p>
          <div className="rounded-lg overflow-hidden border" style={{ borderColor: 'var(--border)' }}>
            <SyntaxHighlighter
              language="python"
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
              {data.code}
            </SyntaxHighlighter>
          </div>
        </div>
      )}

      {/* Stdout */}
      {data.stdout && (
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--text-dim)' }}>
            Output
          </p>
          <pre className="text-xs px-3 py-2 rounded-lg overflow-x-auto font-mono"
            style={{ background: 'var(--bg-base)', color: 'var(--text-secondary)', border: '1px solid var(--border)' }}>
            {data.stdout}
          </pre>
        </div>
      )}

      {/* Error */}
      {data.error && (
        <div className="px-3 py-2 rounded-lg text-xs font-mono"
          style={{ background: 'var(--destructive-muted)', color: 'var(--destructive)', border: '1px solid rgba(239,68,68,0.2)' }}>
          {data.error}
        </div>
      )}

      {/* Result table */}
      {data.result_table && (
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider mb-1.5" style={{ color: 'var(--text-dim)' }}>
            Result
          </p>
          <TableCard data={data.result_table} />
        </div>
      )}
    </div>
  )
}
