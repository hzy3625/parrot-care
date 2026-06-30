import { ChangeEvent, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { localRepository } from '../data/localRepository'
import { formatDuration, formatEventTime, severityLabels, statusLabels } from '../domain/catalog'
import type { AnomalyEvent, DashboardSummary, EventStatus } from '../types'
import './homepage.css'

const emptySummary: DashboardSummary = { total: 0, pending: 0, highRisk: 0, today: 0 }

const readAudioDuration = (file: File) =>
  new Promise<number>((resolve) => {
    const url = URL.createObjectURL(file)
    const audio = document.createElement('audio')
    audio.preload = 'metadata'
    audio.onloadedmetadata = () => {
      const duration = Number.isFinite(audio.duration) ? audio.duration : 0
      URL.revokeObjectURL(url)
      resolve(duration)
    }
    audio.onerror = () => {
      URL.revokeObjectURL(url)
      resolve(0)
    }
    audio.src = url
  })

function HomePage() {
  const [events, setEvents] = useState<AnomalyEvent[]>([])
  const [summary, setSummary] = useState<DashboardSummary>(emptySummary)
  const [statusFilter, setStatusFilter] = useState<EventStatus | 'all'>('all')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [importing, setImporting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const loadDashboard = async () => {
    setLoading(true)
    setError('')
    try {
      const [nextEvents, nextSummary] = await Promise.all([
        localRepository.listEvents(),
        localRepository.summary(),
      ])
      setEvents(nextEvents)
      setSummary(nextSummary)
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : '无法读取本地记录')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDashboard()
  }, [])

  const visibleEvents = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    return events.filter((event) => {
      const matchesStatus = statusFilter === 'all' || event.status === statusFilter
      const matchesQuery = !normalizedQuery || event.type.toLowerCase().includes(normalizedQuery)
      return matchesStatus && matchesQuery
    })
  }, [events, query, statusFilter])

  const handleImport = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    if (!file.type.startsWith('audio/')) {
      setError('请选择音频文件')
      return
    }

    setImporting(true)
    setError('')
    try {
      const duration = await readAudioDuration(file)
      await localRepository.createEvent({
        categoryId: 'unclassified',
        duration,
        source: 'import',
        audio: file,
      })
      await loadDashboard()
    } catch (importError) {
      setError(importError instanceof Error ? importError.message : '音频导入失败')
    } finally {
      setImporting(false)
    }
  }

  return (
    <div className="home-page">
      <section className="dashboard-hero">
        <div>
          <p className="page-kicker">Local-first care journal</p>
          <h1 className="page-title">听见它的每一次变化</h1>
          <p className="page-description">
            录音、标注和护理记录保存在当前设备。即使没有网络或后台服务，手机也可以独立完成完整工作流。
          </p>
        </div>
        <div className="hero-actions">
          <Link className="primary-button" to="/record">
            <span aria-hidden="true">●</span> 开始采集
          </Link>
          <button
            className="secondary-button"
            type="button"
            disabled={importing}
            onClick={() => fileInputRef.current?.click()}
          >
            {importing ? '正在导入…' : '导入音频'}
          </button>
          <input
            ref={fileInputRef}
            className="visually-hidden"
            type="file"
            accept="audio/*"
            onChange={handleImport}
          />
        </div>
      </section>

      <section className="summary-grid" aria-label="健康记录摘要">
        <article className="summary-card accent">
          <span>今日记录</span>
          <strong>{summary.today}</strong>
          <small>条本机采集</small>
        </article>
        <article className="summary-card">
          <span>待跟进</span>
          <strong>{summary.pending}</strong>
          <small>需要确认状态</small>
        </article>
        <article className="summary-card">
          <span>高风险</span>
          <strong>{summary.highRisk}</strong>
          <small>建议优先查看</small>
        </article>
        <article className="summary-card">
          <span>全部记录</span>
          <strong>{summary.total}</strong>
          <small>仅存储于本机</small>
        </article>
      </section>

      <section className="events-section panel">
        <div className="events-toolbar">
          <div>
            <p className="section-eyebrow">Timeline</p>
            <h2>声音记录</h2>
          </div>
          <div className="filter-controls">
            <label className="search-field">
              <span className="visually-hidden">搜索记录</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="搜索类型"
              />
            </label>
            <label>
              <span className="visually-hidden">按状态筛选</span>
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as EventStatus | 'all')}>
                <option value="all">全部状态</option>
                <option value="pending">待处理</option>
                <option value="reviewing">观察中</option>
                <option value="resolved">已处理</option>
                <option value="false_positive">已排除</option>
              </select>
            </label>
          </div>
        </div>

        {error && <div className="inline-error" role="alert">{error}</div>}
        {loading ? (
          <div className="loading-state">正在读取本地记录…</div>
        ) : visibleEvents.length === 0 ? (
          <div className="empty-state">
            <strong>没有符合条件的记录</strong>
            <p>调整筛选条件，或采集一段新的声音。</p>
          </div>
        ) : (
          <div className="event-list">
            {visibleEvents.map((event) => (
              <Link className="event-row" to={`/anomaly/${event.id}`} key={event.id}>
                <span className={`severity-marker severity-${event.severity}`} aria-hidden="true" />
                <div className="event-main">
                  <div className="event-title-line">
                    <strong>{event.type}</strong>
                    <span className={`status-tag status-${event.status}`}>{statusLabels[event.status]}</span>
                  </div>
                  <span>{formatEventTime(event.timestamp)} · {formatDuration(event.duration)}</span>
                </div>
                <div className="event-confidence">
                  <small>{event.confidence === null ? '人工标注' : '识别置信度'}</small>
                  <strong>{event.confidence === null ? severityLabels[event.severity] : `${Math.round(event.confidence * 100)}%`}</strong>
                </div>
                <span className="row-arrow" aria-hidden="true">→</span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export default HomePage
