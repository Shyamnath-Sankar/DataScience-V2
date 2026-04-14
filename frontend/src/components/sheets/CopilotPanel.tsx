import { useState, useRef, useEffect } from 'react'
import { Send, Bot, Loader2 } from 'lucide-react'
import { useFileStore } from '@/stores/fileStore'
import { useCopilotStore } from '@/stores/copilotStore'
import { createCopilotSSE, fetchFullData } from '@/lib/api'
import { toast } from 'sonner'
import { useNavigate } from 'react-router-dom'

export default function CopilotPanel() {
  const [input, setInput] = useState('')
  const [statusText, setStatusText] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)
  const navigate = useNavigate()

  const { activeFileId } = useFileStore()
  const {
    sessionId, messages, isStreaming, streamingText,
    addMessage, appendStreamingToken, finalizeStreaming,
    setStreaming, addOperation, setGridData,
  } = useCopilotStore()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText])

  const handleSend = () => {
    if (!input.trim() || isStreaming || !activeFileId) return

    const userMsg = input.trim()
    setInput('')
    addMessage({ role: 'user', content: userMsg })
    setStreaming(true)
    setStatusText(null)

    abortRef.current = createCopilotSSE(
      userMsg,
      sessionId,
      activeFileId,
      (event, data) => {
        switch (event) {
          case 'status':
            setStatusText(typeof data === 'string' ? data : 'Thinking...')
            break

          case 'token':
            setStatusText(null) // Clear status once tokens start arriving
            appendStreamingToken(data)
            break

          case 'operation':
            if (data.operation) {
              addOperation(data.operation)
            }
            if (data.rows) {
              setGridData({
                rows: data.rows,
                columns: data.columns?.map((c: any) => ({
                  field: c.name,
                  headerName: c.name,
                  sortable: true,
                  filter: true,
                  resizable: true,
                  editable: true,
                  minWidth: 100,
                })) || [],
              })
              toast.success(data.operation?.description || 'Edit applied')
            }
            break

          case 'redirect':
            // Will be handled after streaming finalizes
            break

          case 'error':
            toast.error(typeof data === 'string' ? data : 'Something went wrong.')
            setStreaming(false)
            setStatusText(null)
            break

          case 'done':
            finalizeStreaming()
            setStatusText(null)
            break
        }
      },
    )
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full" style={{ background: 'var(--bg-surface)' }}>
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b relative"
           style={{ borderColor: 'var(--border)', background: 'var(--bg-surface)' }}>
        <Bot size={16} style={{ color: 'var(--accent)' }} />
        <h2 className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
          Copilot
        </h2>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-4 scroll-smooth">
        {messages.length === 0 && !isStreaming && (
          <div className="flex-1 flex flex-col items-center justify-center text-center py-8">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 border"
                 style={{ background: 'var(--accent-muted)', borderColor: 'var(--accent-border)' }}>
              <Bot size={22} style={{ color: 'var(--accent)' }} />
            </div>
            <p className="text-sm font-semibold mb-1.5 tracking-wide" style={{ color: 'var(--text-primary)' }}>
              Sheets Copilot
            </p>
            <p className="text-xs leading-relaxed max-w-[200px]" style={{ color: 'var(--text-dim)' }}>
              Ask me to edit your data — add rows, update cells, compute columns, and more.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] text-sm rounded-xl px-4 py-2.5 animate-fade-in border ${
                msg.role === 'user' ? 'rounded-tr-sm' : 'rounded-tl-sm border-l-[3px]'
              }`}
              style={{
                background: msg.role === 'user' ? 'var(--accent-muted)' : 'var(--bg-card)',
                borderColor: msg.role === 'user' ? 'var(--accent-border)' : 'var(--border)',
                borderLeftColor: msg.role === 'assistant' ? 'var(--accent)' : undefined,
                color: 'var(--text-primary)',
              }}
            >
              <p className="whitespace-pre-wrap break-words leading-relaxed font-sans">{msg.content}</p>
              {msg.redirect && activeFileId && (
                <button
                  onClick={() => navigate(`/agent?file_id=${activeFileId}`)}
                  className="mt-3 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-300 text-white"
                  style={{ background: 'var(--accent)' }}
                >
                  Open in Agent Chat →
                </button>
              )}
            </div>
          </div>
        ))}

        {/* Streaming / status indicator */}
        {isStreaming && (
          <div className="flex justify-start">
            <div className="max-w-[85%] text-sm rounded-xl px-4 py-2.5 border border-l-[3px] rounded-tl-sm"
                 style={{ background: 'var(--bg-card)', borderColor: 'var(--border)', borderLeftColor: 'var(--accent)' }}>
              {streamingText ? (
                <p className="whitespace-pre-wrap break-words leading-relaxed font-sans" style={{ color: 'var(--text-primary)' }}>
                  {streamingText}
                  <span className="inline-block w-1.5 h-4 ml-0.5 animate-pulse align-middle" style={{ background: 'var(--accent)' }} />
                </p>
              ) : (
                <div className="flex items-center gap-2 py-0.5">
                  <Loader2 size={14} className="animate-spin" style={{ color: 'var(--accent)' }} />
                  <span className="text-xs font-medium tracking-wide" style={{ color: 'var(--text-muted)' }}>
                    {statusText || 'Copilot is thinking...'}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4" style={{ background: 'var(--bg-surface)' }}>
        <div className="flex items-end gap-2 rounded-xl border px-3 py-2 transition-all duration-300"
             style={{
               background: 'var(--bg-card)',
               borderColor: input ? 'var(--accent-border)' : 'var(--border)',
             }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={activeFileId ? "Ask to edit your data..." : "Select a file first..."}
            disabled={!activeFileId || isStreaming}
            rows={1}
            className="flex-1 bg-transparent text-[13px] resize-none outline-none py-1"
            style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', minHeight: '26px', maxHeight: '100px' }}
            onInput={(e: any) => {
              e.target.style.height = '26px'
              e.target.style.height = Math.min(e.target.scrollHeight, 100) + 'px'
            }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming || !activeFileId}
            className="shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-300 mb-0.5"
            style={{
              background: input.trim() && activeFileId ? 'var(--accent)' : 'var(--bg-elevated)',
              color: input.trim() && activeFileId ? 'white' : 'var(--text-dim)',
            }}
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}
