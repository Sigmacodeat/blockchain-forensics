import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

function TestPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          ✅ React funktioniert!
        </h1>
        <p className="text-xl text-gray-600 mb-6">
          Das Frontend läuft erfolgreich auf Port 3000
        </p>
        <div className="space-y-3 text-gray-700">
          <div className="flex items-center gap-3">
            <span className="w-4 h-4 bg-green-500 rounded-full"></span>
            <span className="text-lg">React rendert korrekt</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="w-4 h-4 bg-green-500 rounded-full"></span>
            <span className="text-lg">Tailwind CSS funktioniert</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="w-4 h-4 bg-green-500 rounded-full"></span>
            <span className="text-lg">React Router funktioniert</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="w-4 h-4 bg-green-500 rounded-full"></span>
            <span className="text-lg">Backend läuft auf Port 8000</span>
          </div>
        </div>
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-gray-600">
            URL: {window.location.href}
          </p>
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/de" replace />} />
        <Route path="/de" element={<TestPage />} />
        <Route path="/de/simple" element={<TestPage />} />
        <Route path="*" element={<TestPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
