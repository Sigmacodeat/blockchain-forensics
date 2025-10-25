import { motion } from 'framer-motion'
import { Zap, Search, Shield, Sparkles } from 'lucide-react'

interface QuickReplyButtonsProps {
  onSelect: (query: string) => void
}

const QUICK_REPLIES = [
  {
    icon: Search,
    text: "Wie tracke ich eine Bitcoin-Transaktion?",
    emoji: "🔍",
    gradient: "from-blue-500 to-cyan-500"
  },
  {
    icon: Shield,
    text: "Was ist Tornado Cash?",
    emoji: "🌪️",
    gradient: "from-purple-500 to-pink-500"
  },
  {
    icon: Zap,
    text: "Welche Blockchains unterstützt ihr?",
    emoji: "⛓️",
    gradient: "from-orange-500 to-red-500"
  },
  {
    icon: Sparkles,
    text: "Wie funktioniert AI-Agent?",
    emoji: "🤖",
    gradient: "from-green-500 to-emerald-500"
  }
]

export default function QuickReplyButtons({ onSelect }: QuickReplyButtonsProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ staggerChildren: 0.1 }}
      className="space-y-2"
    >
      <p className="text-xs text-muted-foreground mb-3 flex items-center gap-2">
        <Sparkles className="w-3 h-3" />
        Probier diese Fragen:
      </p>
      <div className="grid grid-cols-1 gap-2">
        {QUICK_REPLIES.map((reply, index) => {
          const Icon = reply.icon
          return (
            <motion.button
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.02, x: 5 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onSelect(reply.text)}
              className="group relative w-full text-left p-3 rounded-xl bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-800 dark:to-slate-900 hover:shadow-lg transition-all border border-slate-200 dark:border-slate-700 overflow-hidden"
            >
              {/* Gradient-Overlay on Hover */}
              <motion.div
                className={`absolute inset-0 bg-gradient-to-r ${reply.gradient} opacity-0 group-hover:opacity-10 transition-opacity`}
                initial={{ opacity: 0 }}
                whileHover={{ opacity: 0.1 }}
              />

              <div className="relative flex items-start gap-3">
                {/* Icon mit Gradient-Background */}
                <div className={`flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br ${reply.gradient} flex items-center justify-center text-white shadow-md`}>
                  <span className="text-base">{reply.emoji}</span>
                </div>

                {/* Text */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-200 group-hover:text-slate-900 dark:group-hover:text-white transition-colors line-clamp-2">
                    {reply.text}
                  </p>
                </div>

                {/* Arrow-Indicator */}
                <motion.div
                  initial={{ x: -5, opacity: 0 }}
                  whileHover={{ x: 0, opacity: 1 }}
                  className="flex-shrink-0 text-slate-400 dark:text-slate-500"
                >
                  →
                </motion.div>
              </div>
            </motion.button>
          )
        })}
      </div>

      {/* Hint Text */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="text-xs text-center text-muted-foreground mt-3 italic"
      >
        💡 Oder stelle deine eigene Frage unten!
      </motion.p>
    </motion.div>
  )
}
