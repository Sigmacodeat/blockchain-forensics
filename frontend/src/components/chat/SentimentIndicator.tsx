import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Smile, Meh, Frown } from 'lucide-react'

interface SentimentIndicatorProps {
  message: string
}

export default function SentimentIndicator({ message }: SentimentIndicatorProps) {
  const [sentiment, setSentiment] = useState<'positive' | 'neutral' | 'negative'>('neutral')

  useEffect(() => {
    // Simple sentiment analysis (in production: use ML API)
    const lowerMessage = message.toLowerCase()
    
    const positiveWords = ['danke', 'toll', 'super', 'perfekt', 'gut', 'klasse', 'genial', 'hilft', 'funktioniert']
    const negativeWords = ['problem', 'fehler', 'nicht', 'schlecht', 'bug', 'kaputt', 'funktioniert nicht']

    const positiveCount = positiveWords.filter(word => lowerMessage.includes(word)).length
    const negativeCount = negativeWords.filter(word => lowerMessage.includes(word)).length

    if (positiveCount > negativeCount && positiveCount > 0) {
      setSentiment('positive')
    } else if (negativeCount > positiveCount && negativeCount > 0) {
      setSentiment('negative')
    } else {
      setSentiment('neutral')
    }
  }, [message])

  const config = {
    positive: {
      icon: Smile,
      color: 'text-green-500',
      bg: 'bg-green-100 dark:bg-green-900/20',
      message: 'Freut mich! 😊'
    },
    neutral: {
      icon: Meh,
      color: 'text-gray-500',
      bg: 'bg-gray-100 dark:bg-gray-900/20',
      message: ''
    },
    negative: {
      icon: Frown,
      color: 'text-red-500',
      bg: 'bg-red-100 dark:bg-red-900/20',
      message: 'Lass mich helfen! 🤝'
    }
  }

  const current = config[sentiment]
  const Icon = current.icon

  if (sentiment === 'neutral' || !current.message) return null

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`flex items-center gap-2 text-xs ${current.bg} ${current.color} px-2 py-1 rounded-lg mt-1`}
    >
      <Icon className="w-3 h-3" />
      <span>{current.message}</span>
    </motion.div>
  )
}
