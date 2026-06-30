export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical'

export type EventStatus = 'pending' | 'reviewing' | 'resolved' | 'false_positive'

export type EventSource = 'sample' | 'recording' | 'import'

export interface Note {
  id: string
  content: string
  timestamp: string
  author: string
}

export interface AnomalyEvent {
  id: string
  categoryId: string
  type: string
  timestamp: string
  severity: SeverityLevel
  confidence: number | null
  status: EventStatus
  duration: number
  source: EventSource
  audioId?: string
  notes: Note[]
}

export interface AudioAsset {
  id: string
  blob: Blob
  mimeType: string
  createdAt: string
}

export interface Category {
  id: string
  name: string
  description: string
  icon: string
  severity: SeverityLevel
}

export interface NewLocalEvent {
  categoryId: string
  duration: number
  source: Exclude<EventSource, 'sample'>
  audio: Blob
}

export interface DashboardSummary {
  total: number
  pending: number
  highRisk: number
  today: number
}
