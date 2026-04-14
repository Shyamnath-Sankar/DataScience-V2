import { create } from 'zustand'
import type { FileRecord } from '@/lib/api'

interface FileStore {
  files: FileRecord[]
  activeFileId: string | null
  isUploading: boolean
  setFiles: (files: FileRecord[]) => void
  setActiveFile: (id: string | null) => void
  addFile: (file: FileRecord) => void
  removeFile: (id: string) => void
  setUploading: (v: boolean) => void
  getActiveFile: () => FileRecord | undefined
}

export const useFileStore = create<FileStore>((set, get) => ({
  files: [],
  activeFileId: null,
  isUploading: false,
  setFiles: (files) => set({ files }),
  setActiveFile: (id) => set({ activeFileId: id }),
  addFile: (file) => set((s) => ({ files: [...s.files, file] })),
  removeFile: (id) =>
    set((s) => ({
      files: s.files.filter((f) => f.id !== id),
      activeFileId: s.activeFileId === id ? null : s.activeFileId,
    })),
  setUploading: (v) => set({ isUploading: v }),
  getActiveFile: () => {
    const s = get()
    return s.files.find((f) => f.id === s.activeFileId)
  },
}))
