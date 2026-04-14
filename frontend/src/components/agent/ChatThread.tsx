import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, RotateCcw, Sparkles } from 'lucide-react'
import { useAgentStore, type AgentMessage } from '@/stores/agentStore'
import { createAgentSSE } from '@/lib/api'
import { toast } from 'sonner'
import AgentBadge from '@/components/shared/AgentBadge'

export default function ChatThread() {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  const {
    sessionId, messages, isStreaming, streamingText, currentStatus,
    activeFileId, sourceType, pinnedMode, dbConnected,
    addMessage, appendStreamingToken, finalizeStreaming,
    setStreaming, setStatus, addCanvasOutput, resetSession,
  } = useAgentStore()

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText, currentStatus])

  const canSend = (sourceType === 'file' && activeFileId) || (sourceType === 'database' && dbConnected)

  const handleSend = () => {
    if (!input.trim() || isStreaming || !canSend) return

    const userMsg = input.trim()
    setInput('')
    addMessage({ role: 'user', content: userMsg })
    setStreaming(true)

    abortRef.current = createAgentSSE(
      userMsg,
      sessionId,
      activeFileId,
      sourceType || 'file',
      pinnedMode,
      (event, data) => {
        switch (event) {
          case 'status':
            setStatus(typeof data === 'string' ? data : data?.data || 'Working...')
            break

          case 'token':
            appendStreamingToken(typeof data === 'string' ? data : '')
            break

          case 'text': {
            const textData = typeof data === 'string' ? JSON.parse(data) : data
            addMessage({
              role: 'assistant',
              content: textData.content,
              agentName: textData.agent_name,
            })
            addCanvasOutput({
              type: 'text',
              agentName: textData.agent_name || 'Assistant',
              data: textData,
            })
            break
          }

          case 'chart': {
            const chartData = typeof data === 'string' ? JSON.parse(data) : data
            addCanvasOutput({
              type: 'chart',
              agentName: 'Visualizer Agent',
              data: chartData,
            })
            break
          }

          case 'table': {
            const tableData = typeof data === 'string' ? JSON.parse(data) : data
            addCanvasOutput({
              type: 'table',
              agentName: 'Code Executor',
              data: tableData,
            })
            break
          }

          case 'eda': {
            const edaData = typeof data === 'string' ? JSON.parse(data) : data
            addCanvasOutput({
              type: 'eda',
              agentName: 'EDA Agent',
              data: edaData,
            })
            break
          }

          case 'code_output': {
            const codeData = typeof data === 'string' ? JSON.parse(data) : data
            addCanvasOutput({
              type: 'code_output',
              agentName: 'Code Executor',
              data: codeData,
            })
            break
          }

          case 'sql_output': {
            const sqlData = typeof data === 'string' ? JSON.parse(data) : data
            addCanvasOutput({
              type: 'sql_output',
              agentName: 'SQL Agent',
              data: sqlData,
            })
            break
          }

          case 'error':
            toast.error(typeof data === 'string' ? data : 'Something went wrong.')
            break

          case 'done':
            finalizeStreaming()
            setStatus(null)
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
      <div className="flex items-center justify-between px-4 py-3 border-b"
           style={{ borderColor: 'var(--border)', background: 'var(--bg-surface)' }}>
        <div className="flex items-center gap-2">
          <Sparkles size={16} style={{ color: 'var(--accent)' }} />
          <span className="text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
            Chat
          </span>
        </div>
        <button
          onClick={resetSession}
          className="flex items-center gap-1.5 text-[11px] font-semibold tracking-wide px-3 py-1.5 rounded-lg transition-all duration-300 border"
          style={{ color: 'var(--text-dim)', background: 'var(--bg-elevated)', borderColor: 'var(--border)' }}
        >
          <RotateCcw size={12} />
          New Session
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-4 scroll-smooth">
        {messages.length === 0 && !isStreaming && (
          <div className="flex-1 flex flex-col items-center justify-center text-center py-8">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 border"
                 style={{ background: 'var(--accent-muted)', borderColor: 'var(--accent-border)' }}>
              <Sparkles size={22} style={{ color: 'var(--accent)' }} />
            </div>
            <p className="text-sm font-semibold mb-1.5 tracking-wide" style={{ color: 'var(--text-primary)' }}>
              Agent Chat
            </p>
            <p className="text-xs leading-relaxed max-w-[220px]" style={{ color: 'var(--text-dim)' }}>
              Ask me to analyze your data — EDA, charts, Python code, SQL queries, and more.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[88%] text-sm rounded-xl px-4 py-3 animate-fade-in border ${
                msg.role === 'user' ? 'rounded-tr-sm' : 'rounded-tl-sm border-l-[3px]'
              }`}
              style={{
                background: msg.role === 'user' ? 'var(--accent-muted)' : 'var(--bg-card)',
                borderColor: msg.role === 'user' ? 'var(--accent-border)' : 'var(--border)',
                borderLeftColor: msg.role === 'assistant' ? 'var(--accent)' : undefined,
                color: 'var(--text-primary)',
              }}
            >
              {msg.role === 'assistant' && msg.agentName && (
                <div className="mb-2">
                  <AgentBadge name={msg.agentName} />
                </div>
              )}
              <p className="whitespace-pre-wrap break-words leading-relaxed font-sans">
                {msg.content}
              </p>
            </div>
          </div>
        ))}

        {/* Status line */}
        {isStreaming && currentStatus && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2.5 px-3.5 py-2 animate-fade-in rounded-lg border"
                 style={{ background: 'var(--bg-elevated)', borderColor: 'var(--border)' }}>
              <Loader2 size={14} className="animate-spin" style={{ color: 'var(--accent)' }} />
              <span className="text-xs font-semibold tracking-wide" style={{ color: 'var(--text-muted)' }}>
                {currentStatus}
              </span>
            </div>
          </div>
        )}

        {/* Streaming text */}
        {isStreaming && streamingText && (
          <div className="flex justify-start">
            <div className="max-w-[88%] text-sm rounded-xl px-4 py-3 border border-l-[3px] rounded-tl-sm"
                 style={{ background: 'var(--bg-card)', borderColor: 'var(--border)', borderLeftColor: 'var(--accent)' }}>
              <p className="whitespace-pre-wrap break-words leading-relaxed font-sans" style={{ color: 'var(--text-primary)' }}>
                {streamingText}
                <span className="inline-block w-1.5 h-4 ml-0.5 animate-pulse align-middle" style={{ background: 'var(--accent)' }} />
              </p>
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
            placeholder={canSend ? "Ask about your data..." : "Select a data source first..."}
            disabled={!canSend || isStreaming}
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
            disabled={!input.trim() || isStreaming || !canSend}
            className="shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-300 mb-0.5"
            style={{
              background: input.trim() && canSend ? 'var(--accent)' : 'var(--bg-elevated)',
              color: input.trim() && canSend ? 'white' : 'var(--text-dim)',
            }}
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  )
}
