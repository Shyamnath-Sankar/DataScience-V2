import Plot from 'react-plotly.js'

interface ChartCardProps {
  data: {
    chart_type?: string
    title?: string
    subtitle?: string
    plotly_data?: any[]
    plotly_layout?: Record<string, any>
  }
}

export default function ChartCard({ data }: ChartCardProps) {
  const layout = {
    template: 'plotly_dark',
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(17,17,19,1)',
    font: { family: 'DM Sans, sans-serif', color: '#fafafa', size: 12 },
    margin: { l: 50, r: 20, t: 40, b: 40 },
    xaxis: { gridcolor: '#222225', zerolinecolor: '#333338' },
    yaxis: { gridcolor: '#222225', zerolinecolor: '#333338' },
    title: { text: data.title || '', font: { size: 14 } },
    ...data.plotly_layout,
  }

  return (
    <div>
      {data.subtitle && (
        <p className="text-xs mb-3" style={{ color: 'var(--text-muted)' }}>
          {data.subtitle}
        </p>
      )}
      <Plot
        data={data.plotly_data || []}
        layout={layout}
        config={{
          displayModeBar: true,
          modeBarButtonsToRemove: ['lasso2d', 'select2d'],
          displaylogo: false,
          responsive: true,
        }}
        useResizeHandler={true}
        style={{ width: '100%', height: '380px' }}
      />
    </div>
  )
}
