import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface Activity {
  id: string
  name: string
  org: string
  action: string
  timeAgo: string
}

// Simulated activities (in production, fetch from API)
const MOCK_ACTIVITIES: Activity[] = [
  { id: '1', name: 'Sarah J.', org: 'FBI', action: 'started trial', timeAgo: '2 min ago' },
  { id: '2', name: 'Marcus C.', org: 'Binance', action: 'upgraded to Pro', timeAgo: '5 min ago' },
  { id: '3', name: 'Dr. James P.', org: 'HSBC', action: 'started trial', timeAgo: '8 min ago' },
  { id: '4', name: 'Lisa M.', org: 'Interpol', action: 'started trial', timeAgo: '12 min ago' },
  { id: '5', name: 'Ahmed K.', org: 'Coinbase', action: 'upgraded to Plus', timeAgo: '15 min ago' },
]

export function LiveActivityFeed() {
  const [activities, setActivities] = useState<Activity[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    // Show first activity after 5 seconds
    const initialTimer = setTimeout(() => {
      setActivities([MOCK_ACTIVITIES[0]])
      setCurrentIndex(1)
    }, 5000)

    return () => clearTimeout(initialTimer)
  }, [])

  useEffect(() => {
    if (currentIndex === 0 || currentIndex >= MOCK_ACTIVITIES.length) return

    // Show next activity every 8-12 seconds (randomized for realism)
    const delay = 8000 + Math.random() * 4000
    const timer = setTimeout(() => {
      setActivities(prev => {
        const newActivity = MOCK_ACTIVITIES[currentIndex]
        // Keep only last 3 activities
        return [newActivity, ...prev].slice(0, 3)
      })
      setCurrentIndex(prev => (prev + 1) % MOCK_ACTIVITIES.length)
    }, delay)

    return () => clearTimeout(timer)
  }, [currentIndex])

  return (
    <div className="fixed bottom-4 left-4 z-40 max-w-sm pointer-events-none">
      <AnimatePresence mode="sync">
        {activities.map((activity, index) => (
          <motion.div
            key={activity.id}
            initial={{ opacity: 0, x: -100, y: 0 }}
            animate={{ 
              opacity: 1 - (index * 0.3), 
              x: 0, 
              y: index * -60,
              scale: 1 - (index * 0.05)
            }}
            exit={{ opacity: 0, x: -100 }}
            transition={{ 
              type: 'spring', 
              stiffness: 300, 
              damping: 30 
            }}
            className="absolute bottom-0 left-0 w-full"
          >
            <div className="bg-background border border-border rounded-lg shadow-xl p-3 mb-2 flex items-center gap-3 pointer-events-auto">
              {/* Live indicator */}
              <div className="relative">
                <div className="w-2 h-2 bg-green-500 rounded-full" />
                <div className="absolute inset-0 w-2 h-2 bg-green-500 rounded-full animate-ping" />
              </div>

              {/* Content */}
              <div className="flex-1 text-sm">
                <strong>{activity.name}</strong>
                {' '}from {activity.org}
                {' '}{activity.action}
                <div className="text-xs text-muted-foreground">{activity.timeAgo}</div>
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )
}
