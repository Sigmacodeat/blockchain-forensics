import { motion } from 'framer-motion'
import { Trophy, Lock } from 'lucide-react'
import { useAchievements } from '@/hooks/useAchievements'
import { getRarityColor, getRarityBorder, ACHIEVEMENTS } from '@/lib/achievements'

export default function AchievementsPanel() {
  const { progress, getUnlockedAchievements, getLockedAchievements, getProgressForAchievement } = useAchievements()
  
  const unlocked = getUnlockedAchievements()
  const locked = getLockedAchievements().slice(0, 6) // Show only 6 locked

  return (
    <div className="relative overflow-hidden rounded-xl bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 p-6 shadow-lg">
      {/* Gradient Background */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-yellow-500/5 to-orange-500/5 rounded-full blur-3xl -mr-32 -mt-32" />
      
      <div className="relative">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-yellow-500 rounded-lg blur opacity-20 animate-pulse" />
              <div className="relative p-2 bg-gradient-to-br from-yellow-500 to-orange-500 rounded-lg">
                <Trophy className="h-5 w-5 text-white" />
              </div>
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">Achievements</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">{progress.totalPoints} Punkte</p>
            </div>
          </div>
          
          {/* Progress Badge */}
          <div className="px-3 py-1.5 bg-gradient-to-r from-yellow-500 to-orange-500 text-white rounded-full text-sm font-semibold shadow-lg">
            {unlocked.length}/{ACHIEVEMENTS.length}
          </div>
        </div>

        {/* Unlocked Achievements */}
        {unlocked.length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">🏆 Freigeschaltet</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {unlocked.map((achievement, index) => (
                <motion.div
                  key={achievement.id}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.05 }}
                  className={`relative group p-4 rounded-xl border-2 ${getRarityBorder(achievement.rarity)} bg-gradient-to-br ${getRarityColor(achievement.rarity)} bg-opacity-10 hover:shadow-lg transition-all cursor-pointer`}
                >
                  {/* Glow Effect */}
                  <div className={`absolute inset-0 bg-gradient-to-br ${getRarityColor(achievement.rarity)} opacity-0 group-hover:opacity-10 rounded-xl transition-opacity`} />
                  
                  <div className="relative text-center">
                    <div className="text-3xl mb-2">{achievement.icon}</div>
                    <div className="text-xs font-bold text-gray-900 dark:text-white mb-1">{achievement.title}</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">{achievement.description}</div>
                    <div className="mt-2 text-xs font-semibold text-yellow-600 dark:text-yellow-400">+{achievement.points}</div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Locked Achievements */}
        {locked.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">🔒 Gesperrt</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {locked.map((achievement, index) => {
                const progress = getProgressForAchievement(achievement.id)
                const progressPercent = Math.min((progress.current / progress.required) * 100, 100)
                
                return (
                  <motion.div
                    key={achievement.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.05 }}
                    className="relative p-4 rounded-xl border-2 border-gray-200 dark:border-slate-700 bg-gray-50 dark:bg-slate-700/50 hover:bg-gray-100 dark:hover:bg-slate-700 transition-all cursor-pointer"
                  >
                    <div className="relative text-center opacity-60">
                      <div className="relative inline-block">
                        <div className="text-3xl mb-2 filter grayscale">{achievement.icon}</div>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <Lock className="w-4 h-4 text-gray-400" />
                        </div>
                      </div>
                      <div className="text-xs font-bold text-gray-700 dark:text-gray-300 mb-1">{achievement.title}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">{achievement.description}</div>
                      
                      {/* Progress Bar */}
                      {progressPercent > 0 && (
                        <div className="mt-2">
                          <div className="w-full h-1.5 bg-gray-200 dark:bg-slate-600 rounded-full overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              animate={{ width: `${progressPercent}%` }}
                              className="h-full bg-gradient-to-r from-primary-500 to-purple-500"
                            />
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {progress.current}/{progress.required}
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )
              })}
            </div>
          </div>
        )}

        {/* Empty State */}
        {unlocked.length === 0 && (
          <div className="text-center py-8">
            <Trophy className="w-16 h-16 text-gray-300 dark:text-slate-600 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-gray-400 mb-2 font-medium">Noch keine Achievements freigeschaltet</p>
            <p className="text-sm text-gray-400 dark:text-gray-500">Starte deinen ersten Trace, um deine Reise zu beginnen!</p>
          </div>
        )}
      </div>
    </div>
  )
}
