import { HashRouter, NavLink, Route, Routes } from 'react-router-dom'
import AnomalyDetailPage from './pages/anomalydetailpage'
import HomePage from './pages/homepage'
import RecordPage from './pages/recordpage'
import './app.css'

const Navigation = () => (
  <nav className="app-navigation" aria-label="主导航">
    <NavLink to="/" end>
      <span aria-hidden="true">⌂</span>
      <span>总览</span>
    </NavLink>
    <NavLink to="/record">
      <span aria-hidden="true">●</span>
      <span>采集</span>
    </NavLink>
  </nav>
)

function App() {
  return (
    <HashRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="app-shell">
        <header className="app-header">
          <NavLink className="brand" to="/" aria-label="返回 ParrotCare 首页">
            <span className="brand-mark" aria-hidden="true">P</span>
            <span>
              <strong>ParrotCare</strong>
              <small>本地健康记录</small>
            </span>
          </NavLink>
          <Navigation />
          <div className="local-mode" title="核心功能不依赖网络或后台服务">
            <span className="status-dot" aria-hidden="true" />
            本机模式
          </div>
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/anomaly/:id" element={<AnomalyDetailPage />} />
            <Route path="/record" element={<RecordPage />} />
          </Routes>
        </main>

        <div className="mobile-navigation">
          <Navigation />
        </div>
      </div>
    </HashRouter>
  )
}

export default App
