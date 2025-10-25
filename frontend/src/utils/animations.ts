/**
 * Reusable animation utilities for consistent scroll animations across all pages
 * State-of-the-art, elegant, professional animations
 */

import { Variants } from 'framer-motion'

// Elegant fade + slide up animation
export const fadeUp: Variants = {
  initial: { opacity: 0, y: 40 },
  whileInView: { 
    opacity: 1, 
    y: 0,
    transition: { 
      duration: 0.6, 
      ease: [0.25, 0.1, 0.25, 1] // easeOutQuart
    }
  }
}

// Subtle fade in
export const fadeIn: Variants = {
  initial: { opacity: 0 },
  whileInView: { 
    opacity: 1,
    transition: { 
      duration: 0.6,
      ease: 'easeOut'
    }
  }
}

// Slide from left
export const slideInLeft: Variants = {
  initial: { opacity: 0, x: -40 },
  whileInView: { 
    opacity: 1, 
    x: 0,
    transition: { 
      duration: 0.6,
      type: 'spring',
      stiffness: 80
    }
  }
}

// Slide from right
export const slideInRight: Variants = {
  initial: { opacity: 0, x: 40 },
  whileInView: { 
    opacity: 1, 
    x: 0,
    transition: { 
      duration: 0.6,
      type: 'spring',
      stiffness: 80
    }
  }
}

// Scale up with fade
export const scaleUp: Variants = {
  initial: { opacity: 0, scale: 0.8 },
  whileInView: { 
    opacity: 1, 
    scale: 1,
    transition: { 
      duration: 0.5,
      type: 'spring',
      stiffness: 100
    }
  }
}

// Icon bounce animation
export const iconBounce: Variants = {
  initial: { scale: 0, rotate: -10 },
  whileInView: { 
    scale: 1, 
    rotate: 0,
    transition: { 
      duration: 0.4,
      type: 'spring',
      stiffness: 200
    }
  }
}

// Stagger container for child elements
export const staggerContainer: Variants = {
  initial: {},
  whileInView: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2
    }
  }
}

// Stagger item (use with staggerContainer)
export const staggerItem: Variants = {
  initial: { opacity: 0, y: 30 },
  whileInView: { 
    opacity: 1, 
    y: 0,
    transition: { 
      duration: 0.5,
      ease: 'easeOut'
    }
  }
}

// Default viewport settings for all animations
export const defaultViewport = {
  once: true,
  margin: '-100px',
  amount: 0.2 as const
}

// Viewport for cards/items that should animate earlier
export const earlyViewport = {
  once: true,
  margin: '-50px',
  amount: 0.1 as const
}

// Hover effects for cards
export const cardHoverEffect = {
  y: -6,
  transition: { duration: 0.2, ease: 'easeOut' }
}

export const cardScaleHover = {
  scale: 1.03,
  y: -6,
  transition: { duration: 0.2, ease: 'easeOut' }
}

// Button hover effects
export const buttonHoverEffect = {
  scale: 1.05,
  transition: { duration: 0.2, type: 'spring', stiffness: 300 }
}
