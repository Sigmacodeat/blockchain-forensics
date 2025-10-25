/**
 * Demo Expiration Modal - Shows when demo expires
 * Encourages user to sign up to save their work
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Clock, Sparkles, CheckCircle, ArrowRight } from 'lucide-react';
import { Button } from './ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { useNavigate } from 'react-router-dom';
import { track } from '@/lib/analytics';

interface DemoExpirationModalProps {
  open: boolean;
  onClose: () => void;
}

export const DemoExpirationModal: React.FC<DemoExpirationModalProps> = ({ open, onClose }) => {
  const navigate = useNavigate();

  const handleSignup = () => {
    track('demo_expired_signup_clicked', {
      source: 'expiration_modal'
    });
    navigate('/register');
    onClose();
  };

  const handleStayDemo = () => {
    track('demo_expired_dismissed', {
      action: 'stay_demo'
    });
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleStayDemo}>
      <DialogContent className="sm:max-w-[500px] p-0 overflow-hidden border-primary/20">
        {/* Gradient Header */}
        <div className="bg-gradient-to-r from-primary to-purple-600 p-6 text-white">
          <DialogHeader>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200 }}
              className="flex items-center justify-center mb-4"
            >
              <div className="relative">
                <Clock className="h-16 w-16" />
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="absolute -top-2 -right-2"
                >
                  <Sparkles className="h-6 w-6 text-yellow-300" />
                </motion.div>
              </div>
            </motion.div>
            <DialogTitle className="text-center text-2xl">
              Your Demo Session Ended
            </DialogTitle>
            <p className="text-center text-white/90 mt-2">
              Thanks for trying our platform! Ready to unlock full access?
            </p>
          </DialogHeader>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Benefits */}
          <div className="space-y-3">
            <h3 className="font-semibold text-lg">Sign up to get:</h3>
            <div className="space-y-2">
              {[
                'Save your cases and investigations',
                'Unlimited transaction tracing',
                'Advanced analytics & reports',
                'Real-time alerts & monitoring',
                'API access & integrations'
              ].map((benefit, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="flex items-center gap-2 text-sm"
                >
                  <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
                  <span>{benefit}</span>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Pricing */}
          <div className="bg-gradient-to-r from-primary/10 to-purple-500/10 border border-primary/20 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold">Start Free Forever</p>
                <p className="text-sm text-muted-foreground">No credit card required</p>
              </div>
              <div className="text-right">
                <p className="text-3xl font-bold text-primary">$0</p>
                <p className="text-xs text-muted-foreground">/month</p>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-2">
            <Button
              onClick={handleSignup}
              className="w-full bg-gradient-to-r from-primary to-purple-600 hover:opacity-90 text-white text-lg py-6"
              size="lg"
            >
              <Sparkles className="mr-2 h-5 w-5" />
              Create Free Account
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            
            <Button
              onClick={handleStayDemo}
              variant="ghost"
              className="w-full"
            >
              Continue Browsing
            </Button>
          </div>

          {/* Fine Print */}
          <p className="text-center text-xs text-muted-foreground">
            Already have an account?{' '}
            <button
              onClick={() => {
                navigate('/login');
                onClose();
              }}
              className="text-primary hover:underline"
            >
              Sign in
            </button>
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default DemoExpirationModal;
