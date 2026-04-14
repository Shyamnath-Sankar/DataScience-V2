interface EDAReportCardProps {
  data: {
    shape?: { rows: number; cols: number }
    dtypes?: Record<string, string>
    type_summary?: Record<string, string>
    missing?: Record<string, { count: number; percentage: number }>
    statistics?: Record<string, Record<string, number | null>>
    correlations?: { col1: string; col2: string; value: number }[]
    outliers?: Record<string, number>
    summary?: string
  }
}

const TYPE_COLORS: Record<string, string> = {
  number: '#3b82f6',
  text: '#f59e0b',
  date: '#14b8a6',
  boolean: '#a855f7',
}

export default function EDAReportCard({ data }: EDAReportCardProps) {
  return (
    <div className="flex flex-col gap-5">
      {/* Shape */}
      {data.shape && (
        <div>
          <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
            {data.shape.rows.toLocaleString()} rows × {data.shape.cols} columns
          </h3>
        </div>
      )}

      {/* Summary */}
      {data.summary && (
        <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          {data.summary}
        </p>
      )}

      {/* Column Types */}
      {data.type_summary && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-dim)' }}>
            Column Types
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {Object.entries(data.type_summary).map(([col, type]) => (
              <span key={col} className="inline-flex items-center gap-1 px-2 py-1 rounded text-[11px] font-mono"
                style={{
                  background: `${TYPE_COLORS[type] || '#71717a'}15`,
                  color: TYPE_COLORS[type] || '#71717a',
                  border: `1px solid ${TYPE_COLORS[type] || '#71717a'}30`,
                }}>
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: TYPE_COLORS[type] || '#71717a' }} />
                {col}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Missing Values */}
      {data.missing && Object.values(data.missing).some((m) => m.count > 0) && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-dim)' }}>
            Missing Values
          </h4>
          <div className="flex flex-col gap-1">
            {Object.entries(data.missing)
              .filter(([, m]) => m.count > 0)
              .sort(([, a], [, b]) => b.percentage - a.percentage)
              .map(([col, m]) => (
                <div key={col} className="flex items-center gap-2">
                  <span className="text-xs font-mono w-32 truncate" style={{ color: 'var(--text-muted)' }}>{col}</span>
                  <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-elevated)' }}>
                    <div className="h-full rounded-full transition-all"
                      style={{
                        width: `${Math.min(m.percentage, 100)}%`,
                        background: m.percentage > 50 ? 'var(--destructive)' : 'var(--warning)',
                      }} />
                  </div>
                  <span className="text-[11px] font-mono w-16 text-right" style={{ color: 'var(--text-dim)' }}>
                    {m.percentage}%
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Top Correlations */}
      {data.correlations && data.correlations.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-dim)' }}>
            Top Correlations
          </h4>
          <div className="flex flex-col gap-1">
            {data.correlations.slice(0, 5).map((c, i) => (
              <div key={i} className="flex items-center gap-2 px-2.5 py-1.5 rounded-md"
                style={{ background: 'var(--bg-elevated)' }}>
                <span className="text-xs font-mono flex-1" style={{ color: 'var(--text-primary)' }}>
                  {c.col1} ↔ {c.col2}
                </span>
                <span className="text-xs font-semibold font-mono px-1.5 py-0.5 rounded"
                  style={{
                    background: Math.abs(c.value) > 0.7 ? 'var(--success-muted)' : 'var(--bg-card)',
                    color: Math.abs(c.value) > 0.7 ? 'var(--success)' : 'var(--text-muted)',
                  }}>
                  {c.value.toFixed(3)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Outliers */}
      {data.outliers && Object.values(data.outliers).some((v) => v > 0) && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-dim)' }}>
            Outliers (IQR)
          </h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(data.outliers)
              .filter(([, count]) => count > 0)
              .map(([col, count]) => (
                <span key={col} className="text-[11px] font-mono px-2 py-1 rounded-md"
                  style={{
                    background: 'var(--warning-muted)',
                    color: 'var(--warning)',
                    border: '1px solid rgba(245, 158, 11, 0.2)',
                  }}>
                  {col}: {count}
                </span>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
