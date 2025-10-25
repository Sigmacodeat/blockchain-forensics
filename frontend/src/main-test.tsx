import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'

function App() {
  return (
    <div className="min-h-screen bg-blue-500 flex items-center justify-center">
      <div className="bg-white p-12 rounded-xl shadow-2xl">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          🎉 React funktioniert!
        </h1>
        <p className="text-xl text-gray-600">
          Das Frontend rendert korrekt.
        </p>
      </div>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
