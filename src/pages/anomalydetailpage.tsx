import React, { useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import './AnomalyDetailPage.css'

interface AnomalyDetail {
  id: string
  type: string
  timestamp: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  confidence: number
  status: 'pending' | 'reviewing' | 'resolved' | 'false_positive'
  audioUrl: string
  duration: number
  notes: Note[]
}

interface Note {
  id: string
  content: string
  timestamp: string
  author: string
}

const mockDetail: AnomalyDetail = {
  id: '1',
  type: '异常叫声',
  timestamp: '2026-06-21 14:30:25',
  severity: 'medium',
  confidence: 0.85,
  status: 'pending',
  audioUrl: '/audio/sample.wav',
  duration: 15,
  notes: [
    {
      id: 'n1',
      content: '鹦鹉在下午时段发出异常高频叫声，持续约15秒',
      timestamp: '2026-06-21 14:35:00',
      author: '系统管理员'
    }
  ]
}

const severityLabels = {
  low: '低',
  medium: '中',
  high: '高',
  critical: '严重'
}

const severityColors = {
  low: '#4CAF50',
  medium: '#FF9800',
  high: '#F44336',
  critical: '#9C27B0'
}

const statusOptions = [
  { value: 'pending', label: '待处理', color: '#9E9E9E' },
  { value: 'reviewing', label: '需关注', color: '#2196F3' },
  { value: 'resolved', label: '已处理', color: '#4CAF50' },
  { value: 'false_positive', label: '误报', color: '#FF5722' }
]

function AnomalyDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [detail, setDetail] = useState<AnomalyDetail>(mockDetail)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [newNote, setNewNote] = useState('')
  const audioRef = useRef<HTMLAudioElement>(null)

  // REQ-020: 音频回放功能
  const handlePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause()
      } else {
        audioRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime)
    }
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value)
    setCurrentTime(time)
    if (audioRef.current) {
      audioRef.current.currentTime = time
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // REQ-020: 事件标记功能
  const handleStatusChange = (newStatus: AnomalyDetail['status']) => {
    setDetail(prev => ({ ...prev, status: newStatus }))
    // 实际项目中这里会调用API更新状态
    console.log(`Status updated to: ${newStatus}`)
  }

  // REQ-020: 添加备注功能
  const handleAddNote = () => {
    if (newNote.trim()) {
      const note: Note = {
        id: `n${Date.now()}`,
        content: newNote.trim(),
        timestamp: new Date().toLocaleString('zh-CN'),
        author: '当前用户'
      }
      setDetail(prev => ({
        ...prev,
        notes: [...prev.notes, note]
      }))
      setNewNote('')
    }
  }

  return (
    <div className="detail-page">
      <div className="back-link">
        <Link to="/">← 返回列表</Link>
      </div>

      <div className="detail-container">
        {/* REQ-020: 详情展示 */}
        <section className="detail-header-section">
          <div className="detail-title">
            <h2>{detail.type}</h2>
            <span 
              className="severity-badge large"
              style={{ backgroundColor: severityColors[detail.severity] }}
            >
              {severityLabels[detail.severity]}严重程度
            </span>
          </div>

          <div className="detail-stats">
            <div className="stat-item">
              <span className="stat-label">事件时间</span>
              <span className="stat-value">{detail.timestamp}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">置信度</span>
              <span className="stat-value highlight">
                {(detail.confidence * 100).toFixed(1)}%
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">事件ID</span>
              <span className="stat-value">{detail.id}</span>
            </div>
          </div>
        </section>

        {/* REQ-020: 音频回放功能 */}
        <section className="audio-section">
          <h3>🔊 音频回放</h3>
          <div className="audio-player">
            <audio 
              ref={audioRef}
              src={detail.audioUrl}
              onTimeUpdate={handleTimeUpdate}
              onEnded={() => setIsPlaying(false)}
            />
            
            <button 
              className="play-btn touch-friendly"
              onClick={handlePlayPause}
            >
              {isPlaying ? '⏸️ 暂停' : '▶️ 播放'}
            </button>

            <div className="audio-progress">
              <input
                type="range"
                min="0"
                max={detail.duration}
                value={currentTime}
                onChange={handleSeek}
                className="progress-slider touch-friendly"
              />
              <div className="time-display">
                {formatTime(currentTime)} / {formatTime(detail.duration)}
              </div>
            </div>

            <div className="audio-controls">
              <button className="control-btn touch-friendly">🔊 音量</button>
              <button className="control-btn touch-friendly">⏪ 回退5s</button>
              <button className="control-btn touch-friendly">⏩ 前进5s</button>
            </div>
          </div>
        </section>

        {/* REQ-020: 事件标记功能 */}
        <section className="status-section">
          <h3>📋 事件标记</h3>
          <div className="status-options">
            {statusOptions.map(option => (
              <button
                key={option.value}
                className={`status-btn touch-friendly ${detail.status === option.value ? 'active' : ''}`}
                style={{ 
                  borderColor: option.color,
                  backgroundColor: detail.status === option.value ? option.color : 'transparent',
                  color: detail.status === option.value ? 'white' : option.color
                }}
                onClick={() => handleStatusChange(option.value as AnomalyDetail['status'])}
              >
                {option.label}
              </button>
            ))}
          </div>
          <div className="current-status">
            当前状态: <strong>{statusOptions.find(o => o.value === detail.status)?.label}</strong>
          </div>
        </section>

        {/* REQ-020: 添加备注功能 */}
        <section className="notes-section">
          <h3>📝 备注记录</h3>
          <div className="notes-list">
            {detail.notes.map(note => (
              <div key={note.id} className="note-item">
                <div className="note-header">
                  <span className="note-author">{note.author}</span>
                  <span className="note-time">{note.timestamp}</span>
                </div>
                <div className="note-content">{note.content}</div>
              </div>
            ))}
          </div>
          
          <div className="add-note">
            <textarea
              className="note-input touch-friendly"
              placeholder="添加备注..."
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              rows={3}
            />
            <button 
              className="add-note-btn touch-friendly"
              onClick={handleAddNote}
              disabled={!newNote.trim()}
            >
              添加备注
            </button>
          </div>
        </section>
      </div>
    </div>
  )
}

export default AnomalyDetailPage