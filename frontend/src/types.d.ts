declare module 'react-plotly.js' {
  import { Component } from 'react'
  interface PlotParams {
    data: any[]
    layout?: Record<string, any>
    config?: Record<string, any>
    style?: React.CSSProperties
    useResizeHandler?: boolean
    onInitialized?: (figure: any, graphDiv: any) => void
    onUpdate?: (figure: any, graphDiv: any) => void
    onRelayout?: (event: any) => void
    onHover?: (event: any) => void
  }
  export default class Plot extends Component<PlotParams> {}
}

declare module 'react-split' {
  import { ComponentType, CSSProperties, ReactNode } from 'react'
  interface SplitProps {
    sizes?: number[]
    minSize?: number | number[]
    maxSize?: number | number[]
    gutterSize?: number
    gutterAlign?: string
    snapOffset?: number
    dragInterval?: number
    direction?: 'horizontal' | 'vertical'
    cursor?: string
    className?: string
    style?: CSSProperties
    children?: ReactNode
    onDrag?: (sizes: number[]) => void
    onDragStart?: (sizes: number[]) => void
    onDragEnd?: (sizes: number[]) => void
  }
  const Split: ComponentType<SplitProps>
  export default Split
}
