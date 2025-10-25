/**
 * Demo Mode Banner - Shows remaining time for live demo users
 * Displays at top of dashboard when user is in demo mode
 */

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, AlertTriangle, X, Zap } from 'lucide-react';
import { Button } from './ui/button';
import { useNavigate } from 'react-router-dom';

interface DemoModeBannerProps {
  expiresAt: string; // ISO timestamp
  onClose?: () => void;
}

export const DemoModeBanner: React.FC<DemoModeBannerProps> = ({ expiresAt, onClose }) => {
  const navigate = useNavigate();
  const [timeRemaining, setTimeRemaining] = useState<number>(0);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const calculateTimeRemaining = () => {
      const now = Date.now();
      const expires = new Date(expiresAt).getTime();
      const remaining = Math.max(0, Math.floor((expires - now) / 1000));
      setTimeRemaining(remaining);

      // Auto-hide banner when expired
      if (remaining === 0) {
        setIsVisible(false);
      }
    };

    // Initial calculation
    calculateTimeRemaining();

    // Update every second
    const interval = setInterval(calculateTimeRemaining, 1000);

    return () => clearInterval(interval);
  }, [expiresAt]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getColorClass = () => {
    const minutes = Math.floor(timeRemaining / 60);
    if (minutes <= 5) return 'bg-red-500/90';
    if (minutes <= 10) return 'bg-orange-500/90';
    return 'bg-blue-600/90';
  };

  const getIcon = () => {
    const minutes = Math.floor(timeRemaining / 60);
    if (minutes <= 5) return <AlertTriangle className="h-5 w-5" />;
    return <Clock className="h-5 w-5" />;
  };

  const handleClose = () => {
    setIsVisible(false);
    onClose?.();
  };

  if (!isVisible || timeRemaining === 0) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: -100, opacity: 0 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className={`${getColorClass()} backdrop-blur-md border-b border-white/10 transition-colors duration-500`}
      >
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between gap-4">
            {/* Left: Icon + Message */}
            <div className="flex items-center gap-3 flex-1">
              <motion.div
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
              >
                {getIcon()}
              </motion.div>
              
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-white font-semibold">
                    Demo Mode Active
                  </span>
                  <span className="text-white/70 text-sm">
                    • Time remaining:
                  </span>
                  <motion.span
                    key={timeRemaining}
                    initial={{ scale: 1.2 }}
                    animate={{ scale: 1 }}
                    className="text-white font-mono font-bold text-lg"
                  >
                    {formatTime(timeRemaining)}
                  </motion.span>
                </div>
                <p className="text-white/80 text-sm mt-0.5">
                  Sign up to save your work and continue using all features
                </p>
              </div>
            </div>

            {/* Right: Actions */}
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="secondary"
                onClick={() => navigate('/register')}
                className="bg-white text-blue-600 hover:bg-white/90 font-semibold"
              >
                <Zap className="mr-2 h-4 w-4" />
                Sign Up Free
              </Button>
              
              <button
                onClick={handleClose}
                className="p-1.5 rounded hover:bg-white/10 transition-colors"
                aria-label="Close banner"
              >
                <X className="h-4 w-4 text-white/70 hover:text-white" />
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default DemoModeBanner;
