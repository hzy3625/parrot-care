// 异常事件类型定义 - REQ-020

export interface AnomalyEvent {
  id: string
  type: string
  timestamp: string
  severity: SeverityLevel
  confidence: number // 0-1 之间的置信度
  status: EventStatus
}

export interface AnomalyDetail extends AnomalyEvent {
  audioUrl: string
  duration: number // 音频时长（秒）
  notes: Note[]
}

export type SeverityLevel = 'low' | 'medium' | 'high' | 'critical'

export type EventStatus = 'pending' | 'reviewing' | 'resolved' | 'false_positive'

export interface Note {
  id: string
  content: string
  timestamp: string
  author: string
}

// REQ-022: 响应式断点类型
export interface ResponsiveConfig {
  mobile: number // 768px
  tablet: number // 1024px
  desktop: number // 1200px
}