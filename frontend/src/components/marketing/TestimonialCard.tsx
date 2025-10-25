import { motion } from 'framer-motion'
import { Star } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

interface TestimonialCardProps {
  quote: string
  author: string
  role: string
  organization: string
  avatar: string
  badge: string
  stats?: Record<string, string>
  rating?: number
}

export function TestimonialCard({
  quote,
  author,
  role,
  organization,
  avatar,
  badge,
  stats,
  rating = 5
}: TestimonialCardProps) {
  return (
    <motion.div
      className="bg-card border border-border rounded-xl p-6 hover:shadow-xl transition-all h-full flex flex-col"
      whileHover={{ y: -4 }}
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
    >
      {/* Rating */}
      <div className="flex items-center gap-1 mb-4">
        {[...Array(rating)].map((_, i) => (
          <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
        ))}
      </div>

      {/* Quote */}
      <blockquote className="text-foreground mb-6 italic flex-1">
        "{quote}"
      </blockquote>

      {/* Stats (if provided) */}
      {stats && (
        <div className="flex gap-4 mb-4 pb-4 border-b">
          {Object.entries(stats).map(([key, value]) => (
            <div key={key} className="text-center">
              <div className="text-2xl font-bold text-primary">{value}</div>
              <div className="text-xs text-muted-foreground capitalize">{key}</div>
            </div>
          ))}
        </div>
      )}

      {/* Author */}
      <div className="flex items-center gap-3">
        <img 
          src={avatar} 
          alt={author}
          className="w-12 h-12 rounded-full border-2 border-primary object-cover"
          onError={(e) => {
            // Fallback to placeholder if image fails
            e.currentTarget.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(author)}&background=6366f1&color=fff`
          }}
        />
        <div className="flex-1">
          <div className="font-semibold">{author}</div>
          <div className="text-sm text-muted-foreground">{role}</div>
          <div className="text-sm text-muted-foreground">{organization}</div>
        </div>
      </div>

      {/* Verification Badge */}
      <Badge className="mt-4 w-full justify-center" variant="secondary">
        {badge}
      </Badge>
    </motion.div>
  )
}
