import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'

interface AnimatedRobotIconProps {
  size?: number
  isOpen?: boolean
  isTyping?: boolean
  className?: string
  useGradient?: boolean
  gradientFrom?: string
  gradientTo?: string
}

export default function AnimatedRobotIcon({ size = 32, isOpen = false, isTyping = false, className = '', useGradient = false, gradientFrom = '#60a5fa', gradientTo = '#6366f1' }: AnimatedRobotIconProps) {
  const [isBlinking, setIsBlinking] = useState(false)
  const [moodState, setMoodState] = useState<'happy' | 'excited' | 'thinking'>('happy')

  // Zwinkern-Loop: Alle 3-5 Sekunden
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      setIsBlinking(true)
      setTimeout(() => setIsBlinking(false), 200) // 200ms Blink-Dauer
    }, 3000 + Math.random() * 2000) // 3-5 Sekunden

    return () => clearInterval(blinkInterval)
  }, [])

  // Mood wechselt basierend auf isTyping
  useEffect(() => {
    if (isTyping) {
      setMoodState('thinking')
    } else {
      setMoodState('happy')
    }
  }, [isTyping])

  return (
    <motion.svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      initial={{ rotate: 0 }}
      animate={{ 
        rotate: isOpen ? 0 : (isTyping ? [0, -3, 3, 0] : [0, -5, 5, -5, 5, 0]),
        scale: isOpen ? 1 : [1, 1.05, 1]
      }}
      transition={{ 
        rotate: { duration: isTyping ? 1 : 2, repeat: Infinity, repeatDelay: isTyping ? 0 : 3 },
        scale: { duration: 2, repeat: Infinity }
      }}
      whileHover={{ 
        scale: 1.15,
        rotate: [0, -10, 10, -10, 10, 0],
        transition: { duration: 0.5 }
      }}
    >
      {useGradient && (
        <defs>
          <linearGradient id="robotGradient" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor={gradientFrom} />
            <stop offset="100%" stopColor={gradientTo} />
          </linearGradient>
        </defs>
      )}
      {/* 3D-Shadow-Layer (Depth-Effekt) */}
      <motion.rect
        x="14"
        y="18"
        width="40"
        height="36"
        rx="8"
        fill={useGradient ? 'url(#robotGradient)' : 'currentColor'}
        opacity="0.2"
        animate={{ opacity: [0.2, 0.3, 0.2] }}
        transition={{ duration: 3, repeat: Infinity }}
      />

      {/* Roboter Kopf - Moderner 3D-Look */}
      <motion.rect
        x="12"
        y="16"
        width="40"
        height="36"
        rx="10"
        fill={useGradient ? 'url(#robotGradient)' : 'currentColor'}
        initial={{ opacity: 0.95 }}
        animate={{ opacity: isTyping ? [0.95, 1, 0.95] : [0.95, 1, 0.95] }}
        transition={{ duration: isTyping ? 0.8 : 3, repeat: Infinity }}
      />
      
      {/* Glanz-Effekt (3D Highlight) */}
      <motion.ellipse
        cx="28"
        cy="22"
        rx="8"
        ry="4"
        fill="white"
        opacity="0.2"
        animate={{ opacity: [0.2, 0.4, 0.2] }}
        transition={{ duration: 2, repeat: Infinity }}
      />
      
      {/* Antenne */}
      <motion.line
        x1="32"
        y1="16"
        x2="32"
        y2="8"
        stroke={useGradient ? 'url(#robotGradient)' : 'currentColor'}
        strokeWidth="2"
        strokeLinecap="round"
        animate={{ 
          y1: [16, 14, 16],
          y2: [8, 6, 8]
        }}
        transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.circle
        cx="32"
        cy="8"
        r="3"
        fill={useGradient ? 'url(#robotGradient)' : 'currentColor'}
        animate={{ 
          scale: [1, 1.3, 1],
          opacity: [1, 0.7, 1]
        }}
        transition={{ duration: 1.5, repeat: Infinity }}
      />

      {/* Linkes Auge */}
      <motion.g>
        <circle cx="22" cy="28" r="5" fill="white" />
        <motion.circle
          cx="22"
          cy="28"
          r="3"
          fill="#1e293b"
          animate={isBlinking ? { scaleY: 0.1 } : { scaleY: 1 }}
          transition={{ duration: 0.1 }}
        />
        {/* Pupille - folgt Mauszeiger-Effekt */}
        <motion.circle
          cx="22"
          cy="28"
          r="2"
          fill="#0f172a"
          animate={{ 
            x: [0, 1, -1, 0],
            y: [0, 1, -1, 0]
          }}
          transition={{ duration: 4, repeat: Infinity }}
        />
      </motion.g>

      {/* Rechtes Auge */}
      <motion.g>
        <circle cx="42" cy="28" r="5" fill="white" />
        <motion.circle
          cx="42"
          cy="28"
          r="3"
          fill="#1e293b"
          animate={isBlinking ? { scaleY: 0.1 } : { scaleY: 1 }}
          transition={{ duration: 0.1 }}
        />
        <motion.circle
          cx="42"
          cy="28"
          r="2"
          fill="#0f172a"
          animate={{ 
            x: [0, 1, -1, 0],
            y: [0, 1, -1, 0]
          }}
          transition={{ duration: 4, repeat: Infinity }}
        />
      </motion.g>

      {/* Mund - Dynamisch basierend auf Mood */}
      <motion.path
        d={moodState === 'thinking' ? "M 24 42 L 40 42" : "M 24 40 Q 32 46 40 40"}
        stroke="white"
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
        animate={moodState === 'thinking' ? 
          { d: ["M 24 42 L 40 42", "M 26 42 L 38 42", "M 24 42 L 40 42"] } :
          { d: ["M 24 40 Q 32 46 40 40", "M 24 40 Q 32 48 40 40", "M 24 40 Q 32 46 40 40"] }
        }
        transition={{ duration: moodState === 'thinking' ? 0.8 : 2, repeat: Infinity }}
      />

      {/* Details - Moderne Ohren mit Glow */}
      <motion.circle
        cx="10"
        cy="32"
        r="4"
        fill={useGradient ? 'url(#robotGradient)' : 'currentColor'}
        opacity="0.9"
        animate={{ scale: [1, 1.1, 1] }}
        transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
      />
      <circle cx="10" cy="32" r="2" fill="white" opacity="0.3" />
      
      <motion.circle
        cx="54"
        cy="32"
        r="4"
        fill={useGradient ? 'url(#robotGradient)' : 'currentColor'}
        opacity="0.9"
        animate={{ scale: [1, 1.1, 1] }}
        transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
      />
      <circle cx="54" cy="32" r="2" fill="white" opacity="0.3" />

      {/* LED-Indicator (wenn Typing) */}
      {isTyping && (
        <motion.g>
          <motion.circle
            cx="32"
            cy="48"
            r="2"
            fill="#22c55e"
            initial={{ opacity: 0 }}
            animate={{ opacity: [0, 1, 0] }}
            transition={{ duration: 1, repeat: Infinity }}
          />
          <motion.circle
            cx="28"
            cy="48"
            r="2"
            fill="#22c55e"
            initial={{ opacity: 0 }}
            animate={{ opacity: [0, 1, 0] }}
            transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
          />
          <motion.circle
            cx="36"
            cy="48"
            r="2"
            fill="#22c55e"
            initial={{ opacity: 0 }}
            animate={{ opacity: [0, 1, 0] }}
            transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
          />
        </motion.g>
      )}
    </motion.svg>
  )
}
