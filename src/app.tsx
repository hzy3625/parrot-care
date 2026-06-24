import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import HomePage from './pages/homepage'
import AnomalyDetailPage from './pages/anomalydetailpage'
import RecordPage from './pages/recordpage'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app-container">
        <header className="app-header">
          <h1>鹦鹉护理系统</h1>
          <p className="subtitle">异常事件监测平台</p>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/anomaly/:id" element={<AnomalyDetailPage />} />
            <Route path="/record" element={<RecordPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
