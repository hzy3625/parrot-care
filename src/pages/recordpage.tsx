import { useState, useRef, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import './RecordPage.css'

// 5 类别定义（与模型对齐）
const CATEGORIES = [
  { id: 'normal_chirp', nameCn: '正常鸣叫', nameEn: 'normal_chirp', icon: '🎵' },
  { id: 'scream', nameCn: '尖叫', nameEn: 'scream', icon: '📢' },
  { id: 'night_fright', nameCn: '夜间惊飞', nameEn: 'night_fright', icon: '🌙' },
  { id: 'plucking', nameCn: '啄羽', nameEn: 'plucking', icon: '🪶' },
  { id: 'silence', nameCn: '安静', nameEn: 'silence', icon: '🤫' },
]

const MIN_DURATION = 3
const MAX_DURATION = 15
const API_BASE = 'http://localhost:8000'

interface ProgressItem {
  event_type: string
  label_cn: string
  label_en: string
  count: number
  target: number
}

function RecordPage() {
  // 录音状态
  const [isRecording, setIsRecording] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [micError, setMicError] = useState<string | null>(null)

  // 表单状态
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [privacyAgreed, setPrivacyAgreed] = useState(false)
  const [parrotId] = useState('demo-parrot-001')

  // 上传状态
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<{ success: boolean; message: string } | null>(null)

  // 采集进度
  const [progress, setProgress] = useState<ProgressItem[]>([])
  const [loadingProgress, setLoadingProgress] = useState(false)

  // refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // 拉取采集进度
  const fetchProgress = useCallback(async () => {
    setLoadingProgress(true)
    try {
      const token = localStorage.getItem('token') || ''
      const resp = await fetch(`${API_BASE}/api/audio/collection-progress`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (resp.ok) {
        const data = await resp.json()
        setProgress(data.categories || [])
      }
    } catch (err) {
      // 静默失败，不打断用户
      console.error('获取采集进度失败', err)
    } finally {
      setLoadingProgress(false)
    }
  }, [])

  useEffect(() => {
    fetchProgress()
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop())
      }
    }
  }, [fetchProgress])

  // 开始录音
  const startRecording = async () => {
    setMicError(null)
    setAudioBlob(null)
    setAudioUrl(null)
    setUploadResult(null)
    chunksRef.current = []

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      })
      streamRef.current = stream

      // 选择支持的 mime type
      let mimeType = 'audio/webm'
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/wav'
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = '' // 使用默认
        }
      }

      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream)

      mediaRecorderRef.current = recorder

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || 'audio/webm',
        })
        setAudioBlob(blob)
        setAudioUrl(URL.createObjectURL(blob))
      }

      recorder.start()
      setIsRecording(true)
      setRecordingTime(0)

      // 计时器
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          const next = prev + 1
          if (next >= MAX_DURATION) {
            stopRecording()
          }
          return next
        })
      }, 1000)
    } catch (err: any) {
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setMicError('麦克风权限被拒绝。请在浏览器设置中允许麦克风访问后重试。')
      } else if (err.name === 'NotFoundError') {
        setMicError('未检测到麦克风设备。请确认麦克风已连接。')
      } else {
        setMicError(`录音启动失败: ${err.message || '未知错误'}`)
      }
    }
  }

  // 停止录音
  const stopRecording = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
    setIsRecording(false)
  }

  // 重录
  const reRecord = () => {
    setAudioBlob(null)
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl)
      setAudioUrl(null)
    }
    setUploadResult(null)
    startRecording()
  }

  // 删除录音
  const deleteRecording = () => {
    setAudioBlob(null)
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl)
      setAudioUrl(null)
    }
    setRecordingTime(0)
    setUploadResult(null)
  }

  // 上传
  const handleUpload = async () => {
    if (!audioBlob) return
    if (!selectedCategory) {
      setUploadResult({ success: false, message: '请选择一个类别标签' })
      return
    }
    if (!privacyAgreed) {
      setUploadResult({ success: false, message: '请勾选隐私授权' })
      return
    }
    if (recordingTime < MIN_DURATION) {
      setUploadResult({ success: false, message: `录音时长不足 ${MIN_DURATION} 秒` })
      return
    }

    setUploading(true)
    setUploadResult(null)

    try {
      const formData = new FormData()
      formData.append('parrot_id', parrotId)
      formData.append('event_type', selectedCategory)
      const fileExt = audioBlob.type.includes('webm') ? '.webm' : '.wav'
      formData.append('audio_file', audioBlob, `recording${fileExt}`)

      const token = localStorage.getItem('token') || ''
      const resp = await fetch(`${API_BASE}/api/audio/record-upload`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      })

      if (resp.ok) {
        const data = await resp.json()
        setUploadResult({
          success: true,
          message: `上传成功！类别: ${data.event_type}，已保存。`,
        })
        // 刷新进度
        fetchProgress()
        // 清除录音
        deleteRecording()
      } else {
        const errData = await resp.json().catch(() => ({}))
        setUploadResult({
          success: false,
          message: `上传失败: ${errData.detail || resp.statusText}`,
        })
      }
    } catch (err: any) {
      setUploadResult({
        success: false,
        message: `网络错误: ${err.message || '无法连接服务器'}`,
      })
    } finally {
      setUploading(false)
    }
  }

  const formatTime = (s: number) => `${s}s`

  const canUpload = audioBlob && selectedCategory && privacyAgreed && recordingTime >= MIN_DURATION && !uploading
  const durationWarning = recordingTime > MAX_DURATION
  const durationTooShort = recordingTime < MIN_DURATION && audioBlob

  return (
    <div className="record-page">
      <div className="page-header">
        <h2>🎙️ 录音采集</h2>
        <Link to="/" className="nav-link">← 返回首页</Link>
      </div>

      {/* 隐私提示 */}
      <div className="privacy-notice">
        <h3>📋 隐私说明</h3>
        <p>本录音仅用于训练鹦鹉行为分类 AI 模型，数据存储在本机本地服务器，不会上传至任何外部服务器或第三方平台。</p>
        <p>录音将按标注类别保存，用于提升模型识别准确率。</p>
      </div>

      {/* 录音区域 */}
      <div className="record-section">
        <h3>音频录制</h3>

        {/* 录音时长指示 */}
        <div className="recording-status">
          <div className={`timer ${isRecording ? 'recording' : ''} ${durationWarning ? 'warning' : ''} ${durationTooShort ? 'too-short' : ''}`}>
            <span className="timer-icon">{isRecording ? '🔴' : '⏺️'}</span>
            <span className="timer-text">{formatTime(recordingTime)}</span>
            {!isRecording && audioBlob && (
              <span className="timer-hint">/ {MIN_DURATION}-{MAX_DURATION}s</span>
            )}
          </div>
          {durationWarning && <p className="warning-text">⚠️ 录音超过 {MAX_DURATION} 秒，已自动停止</p>}
          {durationTooShort && <p className="warning-text">⚠️ 录音时长不足 {MIN_DURATION} 秒，请重录</p>}
        </div>

        {/* 录音控制按钮 */}
        <div className="record-controls">
          {!isRecording && !audioBlob && (
            <button className="btn btn-primary touch-friendly" onClick={startRecording}>
              🎙️ 开始录音
            </button>
          )}
          {isRecording && (
            <button className="btn btn-stop touch-friendly" onClick={stopRecording}>
              ⏹️ 停止录音
            </button>
          )}
          {audioBlob && !isRecording && (
            <>
              <button className="btn btn-primary touch-friendly" onClick={reRecord}>
                🔄 重新录音
              </button>
              <button className="btn btn-secondary touch-friendly" onClick={deleteRecording}>
                🗑️ 删除
              </button>
            </>
          )}
        </div>

        {/* 麦克风错误提示 */}
        {micError && (
          <div className="error-banner">
            <p>❌ {micError}</p>
          </div>
        )}

        {/* 试听 */}
        {audioUrl && (
          <div className="playback-section">
            <h4>▶️ 试听录音</h4>
            <audio ref={audioRef} src={audioUrl} controls />
          </div>
        )}
      </div>

      {/* 类别选择 */}
      {audioBlob && (
        <div className="category-section">
          <h3>选择类别标签 <span className="required">*</span></h3>
          <div className="category-grid">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                className={`category-card ${selectedCategory === cat.id ? 'selected' : ''}`}
                onClick={() => setSelectedCategory(cat.id)}
              >
                <span className="category-icon">{cat.icon}</span>
                <span className="category-name">{cat.nameCn}</span>
                <span className="category-en">{cat.nameEn}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 隐私授权 */}
      {audioBlob && (
        <div className="privacy-consent">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={privacyAgreed}
              onChange={(e) => setPrivacyAgreed(e.target.checked)}
            />
            <span>
              我已知晓录音数据仅用于本地 AI 模型训练，不会上传至外部服务器。
            </span>
          </label>
        </div>
      )}

      {/* 上传按钮 */}
      {audioBlob && (
        <div className="upload-section">
          <button
            className="btn btn-upload touch-friendly"
            disabled={!canUpload}
            onClick={handleUpload}
          >
            {uploading ? '⏳ 上传中...' : '📤 提交录音'}
          </button>
          {!selectedCategory && <p className="hint-text">请先选择类别标签</p>}
          {!privacyAgreed && <p className="hint-text">请勾选隐私授权</p>}
        </div>
      )}

      {/* 上传结果反馈 */}
      {uploadResult && (
        <div className={`upload-result ${uploadResult.success ? 'success' : 'error'}`}>
          <p>{uploadResult.success ? '✅' : '❌'} {uploadResult.message}</p>
          {!uploadResult.success && (
            <button className="btn btn-retry touch-friendly" onClick={handleUpload}>
              🔄 重试
            </button>
          )}
        </div>
      )}

      {/* 采集进度 */}
      <div className="progress-section">
        <h3>📊 采集进度</h3>
        {loadingProgress ? (
          <p className="hint-text">加载中...</p>
        ) : progress.length > 0 ? (
          <div className="progress-list">
            {progress.map((item) => {
              const pct = Math.min(100, (item.count / item.target) * 100)
              const cat = CATEGORIES.find(c => c.id === item.event_type)
              return (
                <div key={item.event_type} className="progress-item">
                  <div className="progress-header">
                    <span className="progress-label">
                      {cat?.icon || '📁'} {item.label_cn} ({item.label_en})
                    </span>
                    <span className={`progress-count ${item.count >= item.target ? 'done' : ''}`}>
                      {item.count} / {item.target}
                    </span>
                  </div>
                  <div className="progress-bar-container">
                    <div
                      className={`progress-bar ${pct >= 100 ? 'complete' : ''}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  {item.count >= item.target && (
                    <span className="progress-done-tag">✅ 已达标</span>
                  )}
                </div>
              )
            })}
          </div>
        ) : (
          <p className="hint-text">暂无进度数据</p>
        )}
        <button className="btn btn-secondary touch-friendly" onClick={fetchProgress} disabled={loadingProgress}>
          🔄 刷新进度
        </button>
      </div>
    </div>
  )
}

export default RecordPage
