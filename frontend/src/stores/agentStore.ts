import { create } from 'zustand'
import { generateId } from '@/lib/utils'

export interface AgentMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  agentName?: string
  timestamp: number
}

export interface CanvasOutput {
  id: string
  type: 'chart' | 'table' | 'eda' | 'code_output' | 'sql_output' | 'text'
  agentName: string
  data: any
  timestamp: number
}

interface AgentStore {
  sessionId: string
  messages: AgentMessage[]
  canvasOutputs: CanvasOutput[]
  pinnedMode: string | null
  currentStatus: string | null
  isStreaming: boolean
  streamingText: string

  sourceType: 'file' | 'database' | null
  activeFileId: string | null
  dbConnected: boolean
  dbTables: string[]

  addMessage: (msg: Omit<AgentMessage, 'id' | 'timestamp'>) => void
  appendStreamingToken: (token: string) => void
  finalizeStreaming: (agentName?: string) => void
  addCanvasOutput: (output: Omit<CanvasOutput, 'id' | 'timestamp'>) => void
  setPinnedMode: (mode: string | null) => void
  setStatus: (status: string | null) => void
  setStreaming: (v: boolean) => void
  clearCanvas: () => void
  resetSession: () => void
  setSource: (type: 'file' | 'database', fileId?: string | null) => void
  setDbConnected: (connected: boolean, tables?: string[]) => void
}

export const useAgentStore = create<AgentStore>((set, get) => ({
  sessionId: generateId(),
  messages: [],
  canvasOutputs: [],
  pinnedMode: null,
  currentStatus: null,
  isStreaming: false,
  streamingText: '',
  sourceType: null,
  activeFileId: null,
  dbConnected: false,
  dbTables: [],

  addMessage: (msg) =>
    set((s) => ({
      messages: [...s.messages, { ...msg, id: generateId(), timestamp: Date.now() }],
    })),

  appendStreamingToken: (token) => set((s) => ({ streamingText: s.streamingText + token })),

  finalizeStreaming: (agentName) => {
    const s = get()
    if (s.streamingText) {
      set((state) => ({
        messages: [
          ...state.messages,
          {
            id: generateId(),
            role: 'assistant' as const,
            content: state.streamingText,
            agentName,
            timestamp: Date.now(),
          },
        ],
        streamingText: '',
        isStreaming: false,
        currentStatus: null,
      }))
    } else {
      set({ isStreaming: false, currentStatus: null })
    }
  },

  addCanvasOutput: (output) =>
    set((s) => ({
      canvasOutputs: [
        { ...output, id: generateId(), timestamp: Date.now() },
        ...s.canvasOutputs,
      ],
    })),

  setPinnedMode: (mode) => set({ pinnedMode: mode }),
  setStatus: (status) => set({ currentStatus: status }),
  setStreaming: (v) => set({ isStreaming: v, streamingText: '' }),
  clearCanvas: () => set({ canvasOutputs: [] }),

  resetSession: () =>
    set({
      sessionId: generateId(),
      messages: [],
      canvasOutputs: [],
      currentStatus: null,
      isStreaming: false,
      streamingText: '',
    }),

  setSource: (type, fileId = null) =>
    set({
      sourceType: type,
      activeFileId: fileId,
      dbConnected: false,
      dbTables: [],
    }),

  setDbConnected: (connected, tables = []) =>
    set({ dbConnected: connected, dbTables: tables }),
}))
