import { ChangeEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { localRepository } from '../data/localRepository'
import { categories, formatDuration } from '../domain/catalog'
import './recordpage.css'

const MIN_DURATION = 3
const MAX_DURATION = 60
const visibleCategories = categories.filter((category) => category.id !== 'unclassified')

const getMediaErrorMessage = (error: unknown) => {
  if (!(error instanceof DOMException)) return '无法启动录音，请检查设备后重试。'
  if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
    return '麦克风权限被拒绝。请在浏览器设置中允许访问后重试。'
  }
  if (error.name === 'NotFoundError') return '没有检测到可用的麦克风。'
  if (error.name === 'NotReadableError') return '麦克风正被其他应用占用。'
  return `录音启动失败：${error.message}`
}

function RecordPage() {
  const navigate = useNavigate()
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [audioUrl, setAudioUrl] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('normal_chirp')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [counts, setCounts] = useState<Record<string, number>>({})
  const [source, setSource] = useState<'recording' | 'import'>('recording')

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const startedAtRef = useRef(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const loadCounts = useCallback(async () => {
    try {
      const events = await localRepository.listEvents()
      const nextCounts = events.reduce<Record<string, number>>((result, event) => {
        result[event.categoryId] = (result[event.categoryId] ?? 0) + 1
        return result
      }, {})
      setCounts(nextCounts)
    } catch {
      setCounts({})
    }
  }, [])

  const releasePreview = useCallback(() => {
    setAudioUrl((currentUrl) => {
      if (currentUrl) URL.revokeObjectURL(currentUrl)
      return ''
    })
  }, [])

  const stopRecording = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    const elapsed = Math.min(MAX_DURATION, (Date.now() - startedAtRef.current) / 1000)
    setRecordingTime(elapsed)
    if (mediaRecorderRef.current?.state === 'recording') mediaRecorderRef.current.stop()
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    setIsRecording(false)
  }, [])

  useEffect(() => {
    void loadCounts()
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      streamRef.current?.getTracks().forEach((track) => track.stop())
    }
  }, [loadCounts])

  useEffect(() => () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl)
  }, [audioUrl])

  const clearDraft = () => {
    releasePreview()
    setAudioBlob(null)
    setRecordingTime(0)
    setError('')
  }

  const startRecording = async () => {
    clearDraft()
    chunksRef.current = []
    setSource('recording')

    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setError('当前浏览器不支持录音。你仍可使用“导入音频”完成本地记录。')
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
      })
      streamRef.current = stream
      const preferredTypes = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/webm']
      const mimeType = preferredTypes.find((type) => MediaRecorder.isTypeSupported(type))
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream)
      mediaRecorderRef.current = recorder
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data)
      }
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        setAudioBlob(blob)
        setAudioUrl(URL.createObjectURL(blob))
      }
      recorder.start(500)
      startedAtRef.current = Date.now()
      setRecordingTime(0)
      setIsRecording(true)
      timerRef.current = setInterval(() => {
        const elapsed = (Date.now() - startedAtRef.current) / 1000
        setRecordingTime(Math.min(MAX_DURATION, elapsed))
        if (elapsed >= MAX_DURATION) stopRecording()
      }, 250)
    } catch (mediaError) {
      setError(getMediaErrorMessage(mediaError))
      streamRef.current?.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
  }

  const handleFileImport = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    if (!file.type.startsWith('audio/')) {
      setError('请选择音频文件。')
      return
    }

    clearDraft()
    setSource('import')
    setAudioBlob(file)
    const url = URL.createObjectURL(file)
    setAudioUrl(url)
    const probe = document.createElement('audio')
    probe.preload = 'metadata'
    probe.onloadedmetadata = () => setRecordingTime(Number.isFinite(probe.duration) ? probe.duration : 0)
    probe.onerror = () => setRecordingTime(0)
    probe.src = url
  }

  const saveLocally = async () => {
    if (!audioBlob || saving) return
    if (source === 'recording' && recordingTime < MIN_DURATION) {
      setError(`录音至少需要 ${MIN_DURATION} 秒。`)
      return
    }

    setSaving(true)
    setError('')
    try {
      const event = await localRepository.createEvent({
        categoryId: selectedCategory,
        duration: recordingTime,
        source,
        audio: audioBlob,
      })
      navigate(`/anomaly/${event.id}`, { replace: true })
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : '无法保存到当前设备')
    } finally {
      setSaving(false)
    }
  }

  const totalLocalRecords = useMemo(() => Object.values(counts).reduce((sum, count) => sum + count, 0), [counts])

  return (
    <div className="record-page">
      <div className="record-heading">
        <div>
          <p className="page-kicker">Private audio capture</p>
          <h1 className="page-title">采集一段声音</h1>
          <p className="page-description">音频直接写入当前设备，不经过网络。你可以录音，也可以导入已有文件。</p>
        </div>
        <Link className="text-button" to="/">← 返回总览</Link>
      </div>

      <div className="record-layout">
        <section className="recorder-panel panel">
          <div className={`record-visual ${isRecording ? 'is-recording' : ''}`}>
            <div className="record-rings" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
            <div className="record-time">{formatDuration(recordingTime)}</div>
            <p>{isRecording ? '正在聆听…' : audioBlob ? '录音已就绪' : '准备录音'}</p>
          </div>

          <div className="record-actions">
            {isRecording ? (
              <button className="stop-button" type="button" onClick={stopRecording}>
                <span aria-hidden="true" /> 停止录音
              </button>
            ) : (
              <button className="primary-button" type="button" onClick={() => void startRecording()}>
                <span aria-hidden="true">●</span> {audioBlob ? '重新录音' : '开始录音'}
              </button>
            )}
            {!isRecording && (
              <button className="secondary-button" type="button" onClick={() => fileInputRef.current?.click()}>
                导入音频
              </button>
            )}
            <input
              ref={fileInputRef}
              className="visually-hidden"
              type="file"
              accept="audio/*"
              onChange={handleFileImport}
            />
          </div>

          {audioUrl && !isRecording && (
            <div className="audio-preview">
              <audio controls src={audioUrl}>当前浏览器不支持音频播放。</audio>
              <button className="text-button" type="button" onClick={clearDraft}>移除</button>
            </div>
          )}

          {error && <div className="record-error" role="alert">{error}</div>}

          <div className="privacy-strip">
            <span aria-hidden="true">◆</span>
            <div>
              <strong>默认留在本机</strong>
              <p>关闭网络或后台服务不会影响录音、回放、标注和备注。</p>
            </div>
          </div>
        </section>

        <aside className="label-panel panel">
          <div className="panel-heading">
            <div>
              <span>步骤 2</span>
              <h2>选择声音类型</h2>
            </div>
            <small>{totalLocalRecords} 条本地记录</small>
          </div>

          <div className="category-list">
            {visibleCategories.map((category) => (
              <button
                className={selectedCategory === category.id ? 'selected' : ''}
                type="button"
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
              >
                <span className="category-icon" aria-hidden="true">{category.icon}</span>
                <span className="category-copy">
                  <strong>{category.name}</strong>
                  <small>{category.description}</small>
                </span>
                <span className="category-count">{counts[category.id] ?? 0}</span>
              </button>
            ))}
          </div>

          <button
            className="primary-button save-recording"
            type="button"
            disabled={!audioBlob || saving || (source === 'recording' && recordingTime < MIN_DURATION)}
            onClick={() => void saveLocally()}
          >
            {saving ? '正在保存…' : '保存到本机'}
          </button>
          <p className="save-hint">录音建议 {MIN_DURATION}–{MAX_DURATION} 秒；导入文件不受此限制。</p>
        </aside>
      </div>
    </div>
  )
}

export default RecordPage
