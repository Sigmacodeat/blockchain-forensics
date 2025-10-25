import { motion, AnimatePresence } from 'framer-motion'
import { X, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { track } from '@/lib/analytics'

interface ExitIntentPopupProps {
  isOpen: boolean
  onClose: () => void
  onAccept: () => void
}

export function ExitIntentPopup({ isOpen, onClose, onAccept }: ExitIntentPopupProps) {
  const handleAccept = () => {
    track('exit_intent_accepted')
    onAccept()
  }

  const handleClose = () => {
    track('exit_intent_declined')
    onClose()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
          />

          {/* Modal */}
          <motion.div
            className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[90vw] max-w-md z-[101]"
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          >
            <div className="bg-background border border-border rounded-xl shadow-2xl overflow-hidden">
              {/* Header */}
              <div className="bg-gradient-to-r from-primary to-blue-600 p-6 text-white relative">
                <button
                  onClick={handleClose}
                  className="absolute top-4 right-4 text-white/80 hover:text-white transition"
                  aria-label="Close"
                >
                  <X className="h-5 w-5" />
                </button>

                <div className="flex items-center gap-2 mb-2">
                  <Zap className="h-6 w-6" />
                  <Badge variant="secondary" className="bg-white/20 text-white border-white/30">
                    Limited Time Offer
                  </Badge>
                </div>

                <h2 className="text-2xl font-bold mb-2">
                  Wait! Before You Go...
                </h2>
                <p className="text-white/90">
                  Start your trial today and get <strong>20% off</strong> your first month
                </p>
              </div>

              {/* Body */}
              <div className="p-6">
                <div className="space-y-4 mb-6">
                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-green-600 dark:text-green-400 text-sm">✓</span>
                    </div>
                    <div>
                      <div className="font-medium">No credit card required</div>
                      <div className="text-sm text-muted-foreground">Start your 14-day free trial instantly</div>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-green-600 dark:text-green-400 text-sm">✓</span>
                    </div>
                    <div>
                      <div className="font-medium">Cancel anytime</div>
                      <div className="text-sm text-muted-foreground">No long-term commitment required</div>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-green-600 dark:text-green-400 text-sm">✓</span>
                    </div>
                    <div>
                      <div className="font-medium">Setup in 60 seconds</div>
                      <div className="text-sm text-muted-foreground">Start tracing immediately</div>
                    </div>
                  </div>
                </div>

                {/* CTA */}
                <div className="space-y-3">
                  <Button 
                    size="lg" 
                    className="w-full text-lg" 
                    onClick={handleAccept}
                  >
                    🚀 Claim 20% Discount
                  </Button>
                  <button
                    onClick={handleClose}
                    className="w-full text-sm text-muted-foreground hover:text-foreground transition"
                  >
                    No thanks, I'll pay full price
                  </button>
                </div>

                {/* Social Proof */}
                <div className="mt-6 pt-6 border-t text-center">
                  <p className="text-sm text-muted-foreground mb-2">
                    Join 1,247 investigators who already use SIGMACODE
                  </p>
                  <div className="flex items-center justify-center gap-1">
                    {[1,2,3,4,5].map(i => (
                      <span key={i} className="text-yellow-400">★</span>
                    ))}
                    <span className="ml-2 text-sm font-medium">4.9/5 from 342 reviews</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
