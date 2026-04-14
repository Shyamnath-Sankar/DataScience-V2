const BASE_URL = '/api'

export interface FileRecord {
  id: string
  filename: string
  original_name: string
  row_count: number
  col_count: number
  columns: ColumnInfo[]
  uploaded_at: string
  file_size: number
}

export interface ColumnInfo {
  name: string
  dtype: string
  sample_values?: string[]
}

export interface Operation {
  id: string
  file_id: string
  type: string
  description: string
  params: Record<string, any>
  inverse_data: Record<string, any>
  timestamp: string
}

export interface FilePreview {
  file_id: string
  columns: ColumnInfo[]
  rows: Record<string, any>[]
  total_rows: number
  total_cols: number
}

// ── File API ──

export async function uploadFile(file: File): Promise<FileRecord> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${BASE_URL}/files/upload`, { method: 'POST', body: formData })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Upload failed.' }))
    throw new Error(err.detail || err.message || 'Upload failed.')
  }
  return res.json()
}

export async function fetchFiles(): Promise<FileRecord[]> {
  const res = await fetch(`${BASE_URL}/files`)
  if (!res.ok) throw new Error('Failed to load files.')
  return res.json()
}

export async function deleteFile(fileId: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/files/${fileId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to delete file.')
}

export async function fetchPreview(fileId: string): Promise<FilePreview> {
  const res = await fetch(`${BASE_URL}/files/${fileId}/preview`)
  if (!res.ok) throw new Error('Failed to load file preview.')
  return res.json()
}

export async function fetchFullData(fileId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/files/${fileId}/full`)
  if (!res.ok) throw new Error('Failed to load file data.')
  return res.json()
}

// ── Copilot API ──

export async function fetchOperations(sessionId: string): Promise<Operation[]> {
  const res = await fetch(`${BASE_URL}/copilot/${sessionId}/operations`)
  if (!res.ok) return []
  const data = await res.json()
  return data.operations || []
}

export async function revertOperation(sessionId: string, operationId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/copilot/${sessionId}/revert/${operationId}`, { method: 'POST' })
  if (!res.ok) throw new Error('Revert failed.')
  return res.json()
}

export async function revertLast(sessionId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/copilot/${sessionId}/revert-last`, { method: 'POST' })
  if (!res.ok) throw new Error('Revert failed.')
  return res.json()
}

// ── Agent API ──

export async function connectDatabase(sessionId: string, connectionUrl: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/agent/connect-db`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, connection_url: connectionUrl }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Connection failed.' }))
    throw new Error(err.detail || 'Connection failed.')
  }
  return res.json()
}

export async function clearAgentSession(sessionId: string): Promise<void> {
  await fetch(`${BASE_URL}/agent/${sessionId}/clear`, { method: 'POST' })
}

// ── SSE Helpers ──

export function createCopilotSSE(
  message: string,
  sessionId: string,
  fileId: string,
  onEvent: (event: string, data: any) => void,
): AbortController {
  const controller = new AbortController()

  fetch(`${BASE_URL}/copilot/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId, file_id: fileId }),
    signal: controller.signal,
  }).then(async (response) => {
    if (!response.ok || !response.body) {
      onEvent('error', 'Failed to connect to copilot.')
      return
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      let currentEvent = 'message'
      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEvent = line.slice(6).trim()
        } else if (line.startsWith('data:')) {
          const data = line.slice(5).trim()
          try {
            const parsed = JSON.parse(data)
            onEvent(currentEvent, parsed)
          } catch {
            onEvent(currentEvent, data)
          }
        }
      }
    }
  }).catch((e) => {
    if (e.name !== 'AbortError') {
      onEvent('error', 'Connection lost.')
    }
  })

  return controller
}

export function createAgentSSE(
  message: string,
  sessionId: string,
  fileId: string | null,
  sourceType: string,
  pinnedMode: string | null,
  onEvent: (event: string, data: any) => void,
): AbortController {
  const controller = new AbortController()

  fetch(`${BASE_URL}/agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      file_id: fileId,
      source_type: sourceType,
      pinned_mode: pinnedMode,
    }),
    signal: controller.signal,
  }).then(async (response) => {
    if (!response.ok || !response.body) {
      onEvent('error', 'Failed to connect to agent.')
      return
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      let currentEvent = 'message'
      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEvent = line.slice(6).trim()
        } else if (line.startsWith('data:')) {
          const data = line.slice(5).trim()
          try {
            const parsed = JSON.parse(data)
            onEvent(currentEvent, parsed)
          } catch {
            onEvent(currentEvent, data)
          }
        }
      }
    }
  }).catch((e) => {
    if (e.name !== 'AbortError') {
      onEvent('error', 'Connection lost.')
    }
  })

  return controller
}
