import type { Category, EventStatus, SeverityLevel } from '../types'

export const categories: Category[] = [
  {
    id: 'normal_chirp',
    name: '正常鸣叫',
    description: '日常交流、轻声鸣叫',
    icon: '♪',
    severity: 'low',
  },
  {
    id: 'scream',
    name: '持续尖叫',
    description: '高音量或反复尖叫',
    icon: '!',
    severity: 'medium',
  },
  {
    id: 'night_fright',
    name: '夜间惊飞',
    description: '夜间突然扑翅或撞笼',
    icon: '☾',
    severity: 'high',
  },
  {
    id: 'plucking',
    name: '啄羽行为',
    description: '疑似过度理羽或啄羽',
    icon: '⌁',
    severity: 'high',
  },
  {
    id: 'silence',
    name: '异常安静',
    description: '活动期长时间无鸣叫',
    icon: '—',
    severity: 'medium',
  },
  {
    id: 'unclassified',
    name: '待确认录音',
    description: '导入后等待人工标注',
    icon: '?',
    severity: 'medium',
  },
]

export const categoryById = (id: string) =>
  categories.find((category) => category.id === id) ?? categories[categories.length - 1]

export const severityLabels: Record<SeverityLevel, string> = {
  low: '平稳',
  medium: '留意',
  high: '高风险',
  critical: '紧急',
}

export const statusLabels: Record<EventStatus, string> = {
  pending: '待处理',
  reviewing: '观察中',
  resolved: '已处理',
  false_positive: '已排除',
}

export const formatEventTime = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

export const formatDuration = (seconds: number) => {
  const safeSeconds = Math.max(0, Math.round(seconds))
  return `${Math.floor(safeSeconds / 60)}:${String(safeSeconds % 60).padStart(2, '0')}`
}
