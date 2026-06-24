import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import './HomePage.css'

interface AnomalyEvent {
  id: string
  type: string
  timestamp: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  confidence: number
  status: 'pending' | 'reviewing' | 'resolved' | 'false_positive'
}

const mockEvents: AnomalyEvent[] = [
  {
    id: '1',
    type: '异常叫声',
    timestamp: '2026-06-21 14:30:25',
    severity: 'medium',
    confidence: 0.85,
    status: 'pending'
  },
  {
    id: '2',
    type: '呼吸异常',
    timestamp: '2026-06-21 12:15:10',
    severity: 'high',
    confidence: 0.92,
    status: 'reviewing'
  },
  {
    id: '3',
    type: '环境噪音',
    timestamp: '2026-06-21 09:45:00',
    severity: 'low',
    confidence: 0.65,
    status: 'false_positive'
  }
]

const severityColors = {
  low: '#4CAF50',
  medium: '#FF9800',
  high: '#F44336',
  critical: '#9C27B0'
}

const statusLabels = {
  pending: '待处理',
  reviewing: '审核中',
  resolved: '已处理',
  false_positive: '误报'
}

function HomePage() {
  const [events] = useState<AnomalyEvent[]>(mockEvents)

  return (
    <div className="home-page">
      <div className="page-header">
        <h2>异常事件列表</h2>
        <div className="header-actions">
          <Link to="/record" className="upload-btn touch-friendly">
            🎙️ 录音采集
          </Link>
          <button className="upload-btn touch-friendly">
            📤 上传音频
          </button>
        </div>
      </div>

      <div className="events-grid">
        {events.map(event => (
          <Link 
            to={`/anomaly/${event.id}`} 
            key={event.id}
            className="event-card touch-friendly"
          >
            <div className="event-header">
              <span 
                className="severity-badge"
                style={{ backgroundColor: severityColors[event.severity] }}
              >
                {event.severity.toUpperCase()}
              </span>
              <span className="event-type">{event.type}</span>
            </div>
            <div className="event-details">
              <div className="detail-row">
                <span className="detail-label">时间:</span>
                <span className="detail-value">{event.timestamp}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">置信度:</span>
                <span className="detail-value">{(event.confidence * 100).toFixed(1)}%</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">状态:</span>
                <span className="status-badge">{statusLabels[event.status]}</span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

export default HomePage