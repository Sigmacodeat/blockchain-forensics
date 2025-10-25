import React from 'react'

export default function SimpleLandingPage() {
  return (
    <div className="min-h-screen bg-blue-500 flex items-center justify-center">
      <div className="bg-white p-12 rounded-xl shadow-2xl max-w-2xl">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          🎉 React funktioniert!
        </h1>
        <p className="text-xl text-gray-600 mb-6">
          Wenn du das siehst, läuft das Frontend korrekt.
        </p>
        <div className="space-y-2 text-gray-700">
          <p>✅ Vite läuft auf Port 3000</p>
          <p>✅ React rendert korrekt</p>
          <p>✅ Tailwind CSS funktioniert</p>
          <p>✅ Routing ist aktiv</p>
        </div>
      </div>
    </div>
  )
}
