import { FormEvent, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { localRepository } from '../data/localRepository'
import { categories, formatDuration, formatEventTime, severityLabels, statusLabels } from '../domain/catalog'
import type { AnomalyEvent, EventStatus } from '../types'
import './anomalydetailpage.css'

const statusOptions: EventStatus[] = ['pending', 'reviewing', 'resolved', 'false_positive']
const editableCategories = categories.filter((category) => category.id !== 'unclassified')

const guidanceBySeverity = {
  low: '当前记录风险较低，可继续观察日常饮食、活动与鸣叫节律。',
  medium: '建议记录出现前后的环境变化，并在相似时段继续观察。',
  high: '建议优先检查环境安全、呼吸状态和活动表现；如反复出现，请联系专业兽医。',
  critical: '请立即检查鹦鹉状态，并尽快联系具备鸟类诊疗经验的专业兽医。',
}

function AnomalyDetailPage() {
  const { id = '' } = useParams<{ id: string }>()
  const [detail, setDetail] = useState<AnomalyEvent | null>(null)
  const [audioUrl, setAudioUrl] = useState('')
  const [newNote, setNewNote] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    let currentAudioUrl = ''

    const load = async () => {
      setLoading(true)
      try {
        const event = await localRepository.getEvent(id)
        if (!active) return
        if (!event) {
          setError('这条本地记录不存在或已被移除。')
          return
        }
        setDetail(event)
        if (event.audioId) {
          const audio = await localRepository.getAudio(event.audioId)
          if (active && audio) {
            currentAudioUrl = URL.createObjectURL(audio)
            setAudioUrl(currentAudioUrl)
          }
        }
      } catch (loadError) {
        if (active) setError(loadError instanceof Error ? loadError.message : '无法读取本地记录')
      } finally {
        if (active) setLoading(false)
      }
    }

    void load()
    return () => {
      active = false
      if (currentAudioUrl) URL.revokeObjectURL(currentAudioUrl)
    }
  }, [id])

  const updateStatus = async (status: EventStatus) => {
    if (!detail || saving) return
    setSaving(true)
    setError('')
    try {
      setDetail(await localRepository.updateStatus(detail.id, status))
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : '状态保存失败')
    } finally {
      setSaving(false)
    }
  }

  const updateCategory = async (categoryId: string) => {
    if (!detail || saving) return
    setSaving(true)
    setError('')
    try {
      setDetail(await localRepository.updateCategory(detail.id, categoryId))
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : '类型保存失败')
    } finally {
      setSaving(false)
    }
  }

  const addNote = async (event: FormEvent) => {
    event.preventDefault()
    if (!detail || !newNote.trim() || saving) return
    setSaving(true)
    setError('')
    try {
      setDetail(await localRepository.addNote(detail.id, newNote))
      setNewNote('')
    } catch (noteError) {
      setError(noteError instanceof Error ? noteError.message : '备注保存失败')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="panel loading-state">正在读取本地记录…</div>

  if (!detail) {
    return (
      <div className="panel error-state">
        <h1>找不到记录</h1>
        <p>{error}</p>
        <Link className="primary-button" to="/">返回总览</Link>
      </div>
    )
  }

  return (
    <div className="detail-page">
      <div className="detail-breadcrumb">
        <Link to="/">← 声音记录</Link>
        <span>/</span>
        <span>{detail.type}</span>
      </div>

      <section className="detail-summary panel">
        <div className="detail-summary-main">
          <div className={`detail-severity severity-bg-${detail.severity}`}>
            <span>{severityLabels[detail.severity]}</span>
            <small>风险等级</small>
          </div>
          <div>
            <p className="page-kicker">{detail.source === 'sample' ? '示例记录' : '本地记录'}</p>
            <h1>{detail.type}</h1>
            <p>{formatEventTime(detail.timestamp)} · {formatDuration(detail.duration)}</p>
          </div>
        </div>
        <div className="detail-metrics">
          <div>
            <span>识别方式</span>
            <strong>{detail.confidence === null ? '人工标注' : `${Math.round(detail.confidence * 100)}%`}</strong>
          </div>
          <div>
            <span>当前状态</span>
            <strong>{statusLabels[detail.status]}</strong>
          </div>
          <div>
            <span>数据位置</span>
            <strong>当前设备</strong>
          </div>
        </div>
      </section>

      {error && <div className="detail-error" role="alert">{error}</div>}

      <div className="detail-grid">
        <div className="detail-primary-column">
          <section className="detail-card panel">
            <div className="card-heading">
              <div>
                <span>Audio</span>
                <h2>声音回放</h2>
              </div>
              <small>{formatDuration(detail.duration)}</small>
            </div>
            {audioUrl ? (
              <audio className="detail-audio" controls src={audioUrl}>当前浏览器不支持音频播放。</audio>
            ) : (
              <div className="audio-placeholder">示例记录不包含真实音频。新录制或导入的音频可在这里离线回放。</div>
            )}
          </section>

          <section className="detail-card panel">
            <div className="card-heading">
              <div>
                <span>Notes</span>
                <h2>观察备注</h2>
              </div>
              <small>{detail.notes.length} 条</small>
            </div>

            <div className="note-list">
              {detail.notes.length === 0 && <p className="no-notes">还没有备注。记录当时的环境和行为，有助于后续判断。</p>}
              {detail.notes.map((note) => (
                <article className="note" key={note.id}>
                  <div>
                    <strong>{note.author}</strong>
                    <time>{formatEventTime(note.timestamp)}</time>
                  </div>
                  <p>{note.content}</p>
                </article>
              ))}
            </div>

            <form className="note-form" onSubmit={(event) => void addNote(event)}>
              <label htmlFor="new-note">新增备注</label>
              <textarea
                id="new-note"
                rows={3}
                value={newNote}
                onChange={(event) => setNewNote(event.target.value)}
                placeholder="例如：当时刚更换了笼位，室内有陌生声音…"
              />
              <button className="primary-button" type="submit" disabled={!newNote.trim() || saving}>
                保存备注
              </button>
            </form>
          </section>
        </div>

        <aside className="detail-side-column">
          <section className="detail-card panel">
            <div className="card-heading compact">
              <div>
                <span>Review</span>
                <h2>处理状态</h2>
              </div>
            </div>
            <div className="status-list">
              {statusOptions.map((status) => (
                <button
                  type="button"
                  className={detail.status === status ? 'selected' : ''}
                  disabled={saving}
                  key={status}
                  onClick={() => void updateStatus(status)}
                >
                  <span aria-hidden="true" />
                  {statusLabels[status]}
                </button>
              ))}
            </div>
          </section>

          <section className="detail-card panel">
            <div className="card-heading compact">
              <div>
                <span>Label</span>
                <h2>声音类型</h2>
              </div>
            </div>
            <label className="category-select">
              <span>人工修正标签</span>
              <select
                value={detail.categoryId === 'unclassified' ? '' : detail.categoryId}
                disabled={saving}
                onChange={(event) => void updateCategory(event.target.value)}
              >
                <option value="" disabled>请选择类型</option>
                {editableCategories.map((category) => (
                  <option value={category.id} key={category.id}>{category.name}</option>
                ))}
              </select>
            </label>
          </section>

          <section className={`guidance-card guidance-${detail.severity}`}>
            <span>护理提示</span>
            <p>{guidanceBySeverity[detail.severity]}</p>
            <small>本提示不构成医疗诊断。</small>
          </section>
        </aside>
      </div>
    </div>
  )
}

export default AnomalyDetailPage
