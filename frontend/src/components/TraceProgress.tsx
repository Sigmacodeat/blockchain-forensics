import { Loader2, CheckCircle } from 'lucide-react'
import { motion } from 'framer-motion'

interface TraceProgressProps {
  progress: {
    status: string
    progress_percentage: number
    nodes_discovered: number
    edges_discovered: number
    current_hop: number
    message?: string
  }
  isCompleted: boolean
}

export default function TraceProgress({ progress, isCompleted }: TraceProgressProps) {
  if (isCompleted) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="card p-6 bg-card border border-border"
      >
        <div className="flex items-center gap-3">
          <CheckCircle className="w-6 h-6 text-success-600" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-success-700 dark:text-success-400">
              Trace Completed!
            </h3>
            <p className="text-sm text-muted-foreground">
              Gefunden: {progress.nodes_discovered} Nodes, {progress.edges_discovered} Edges
            </p>
          </div>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card p-6 bg-card border border-border"
    >
      <div className="flex items-center gap-3 mb-4">
        <Loader2 className="w-6 h-6 text-primary-600 animate-spin" />
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-foreground">
            Tracing in Progress...
          </h3>
          <p className="text-sm text-muted-foreground">
            {progress.message || `Hop ${progress.current_hop} wird analysiert`}
          </p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-foreground">
            {progress.progress_percentage}%
          </p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="relative w-full h-2 bg-muted rounded-full overflow-hidden mb-4">
        <motion.div
          className="absolute left-0 top-0 h-full bg-primary-600"
          initial={{ width: 0 }}
          animate={{ width: `${progress.progress_percentage}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-sm text-muted-foreground">Nodes</p>
          <p className="text-lg font-semibold text-foreground">
            {progress.nodes_discovered}
          </p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Edges</p>
          <p className="text-lg font-semibold text-foreground">
            {progress.edges_discovered}
          </p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Current Hop</p>
          <p className="text-lg font-semibold text-foreground">
            {progress.current_hop}
          </p>
        </div>
      </div>
    </motion.div>
  )
}
