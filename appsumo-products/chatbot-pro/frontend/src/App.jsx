import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import DashboardPage from './pages/Dashboard'
import ActivationPage from './pages/Activation'
import ChatWidget from './components/ChatWidget'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/activate" element={<ActivationPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Routes>
      <ChatWidget />
    </Router>
  )
}

export default App
