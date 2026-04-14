interface TextCardProps {
  data: {
    content?: string
    agent_name?: string
  }
}

export default function TextCard({ data }: TextCardProps) {
  return (
    <p className="text-sm leading-relaxed whitespace-pre-wrap" style={{ color: 'var(--text-primary)' }}>
      {data.content || ''}
    </p>
  )
}
