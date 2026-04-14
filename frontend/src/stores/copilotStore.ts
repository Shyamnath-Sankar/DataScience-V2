import { create } from 'zustand'
import type { Operation } from '@/lib/api'
import { generateId } from '@/lib/utils'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  operation?: Operation
  redirect?: boolean
  timestamp: number
}

interface CopilotStore {
  sessionId: string
  messages: ChatMessage[]
  operations: Operation[]
  isStreaming: boolean
  streamingText: string
  gridData: { rows: any[]; columns: any[] } | null

  addMessage: (msg: Omit<ChatMessage, 'id' | 'timestamp'>) => void
  updateStreamingText: (text: string) => void
  appendStreamingToken: (token: string) => void
  finalizeStreaming: () => void
  addOperation: (op: Operation) => void
  setOperations: (ops: Operation[]) => void
  removeOperationsFrom: (opId: string) => void
  setGridData: (data: any) => void
  setStreaming: (v: boolean) => void
  clearMessages: () => void
}

export const useCopilotStore = create<CopilotStore>((set, get) => ({
  sessionId: generateId(),
  messages: [],
  operations: [],
  isStreaming: false,
  streamingText: '',
  gridData: null,

  addMessage: (msg) =>
    set((s) => ({
      messages: [...s.messages, { ...msg, id: generateId(), timestamp: Date.now() }],
    })),

  updateStreamingText: (text) => set({ streamingText: text }),
  appendStreamingToken: (token) => set((s) => ({ streamingText: s.streamingText + token })),

  finalizeStreaming: () => {
    const s = get()
    if (s.streamingText) {
      set((state) => ({
        messages: [
          ...state.messages,
          {
            id: generateId(),
            role: 'assistant' as const,
            content: state.streamingText,
            timestamp: Date.now(),
          },
        ],
        streamingText: '',
        isStreaming: false,
      }))
    } else {
      set({ isStreaming: false })
    }
  },

  addOperation: (op) => set((s) => ({ operations: [...s.operations, op] })),

  setOperations: (ops) => set({ operations: ops }),

  removeOperationsFrom: (opId) =>
    set((s) => {
      const idx = s.operations.findIndex((o) => o.id === opId)
      if (idx === -1) return s
      return { operations: s.operations.slice(0, idx) }
    }),

  setGridData: (data) => set({ gridData: data }),
  setStreaming: (v) => set({ isStreaming: v }),
  clearMessages: () => set({ messages: [], streamingText: '' }),
}))
