import React from 'react';
import { motion } from 'framer-motion';

/**
 * Skeleton Screen Component
 * Premium loading states for better UX
 */

interface SkeletonProps {
  variant?: 'text' | 'circular' | 'rectangular' | 'card' | 'table';
  width?: string | number;
  height?: string | number;
  count?: number;
  className?: string;
  animate?: boolean;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'text',
  width = '100%',
  height,
  count = 1,
  className = '',
  animate = true,
}) => {
  const getVariantClasses = () => {
    switch (variant) {
      case 'text':
        return 'h-4 rounded';
      case 'circular':
        return 'rounded-full';
      case 'rectangular':
        return 'rounded-lg';
      case 'card':
        return 'rounded-xl p-6';
      case 'table':
        return 'h-12 rounded';
      default:
        return 'rounded';
    }
  };

  const getDefaultHeight = () => {
    if (height) return height;
    switch (variant) {
      case 'text':
        return '1rem';
      case 'circular':
        return width;
      case 'rectangular':
        return '8rem';
      case 'card':
        return '12rem';
      case 'table':
        return '3rem';
      default:
        return '1rem';
    }
  };

  const skeletonElement = (
    <div
      className={`
        bg-gradient-to-r from-slate-200 via-slate-300 to-slate-200
        dark:from-slate-800 dark:via-slate-700 dark:to-slate-800
        ${getVariantClasses()}
        ${animate ? 'animate-pulse' : ''}
        ${className}
      `}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof getDefaultHeight() === 'number' ? `${getDefaultHeight()}px` : getDefaultHeight(),
      }}
    />
  );

  if (count > 1) {
    return (
      <div className="space-y-3">
        {Array.from({ length: count }).map((_, i) => (
          <React.Fragment key={i}>{skeletonElement}</React.Fragment>
        ))}
      </div>
    );
  }

  return skeletonElement;
};

/**
 * Skeleton Card - Full card loading state
 */
export const SkeletonCard: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div className={`bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 ${className}`}>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Skeleton variant="circular" width={48} height={48} />
          <Skeleton variant="rectangular" width={80} height={32} />
        </div>
        
        {/* Title */}
        <Skeleton variant="text" width="60%" height={24} />
        
        {/* Content */}
        <div className="space-y-2">
          <Skeleton variant="text" width="100%" />
          <Skeleton variant="text" width="90%" />
          <Skeleton variant="text" width="75%" />
        </div>
        
        {/* Footer */}
        <div className="flex gap-2 pt-4">
          <Skeleton variant="rectangular" width={100} height={36} />
          <Skeleton variant="rectangular" width={100} height={36} />
        </div>
      </div>
    </div>
  );
};

/**
 * Skeleton Table - Table loading state
 */
export const SkeletonTable: React.FC<{ rows?: number; columns?: number; className?: string }> = ({
  rows = 5,
  columns = 4,
  className = '',
}) => {
  return (
    <div className={`bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 p-4">
        <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
          {Array.from({ length: columns }).map((_, i) => (
            <Skeleton key={i} variant="text" width="80%" height={20} />
          ))}
        </div>
      </div>
      
      {/* Rows */}
      <div className="divide-y divide-slate-200 dark:divide-slate-800">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="p-4">
            <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
              {Array.from({ length: columns }).map((_, colIndex) => (
                <Skeleton key={colIndex} variant="text" width="90%" />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * Skeleton List - List loading state
 */
export const SkeletonList: React.FC<{ items?: number; withAvatar?: boolean; className?: string }> = ({
  items = 5,
  withAvatar = false,
  className = '',
}) => {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: items }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-4 p-4 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800"
        >
          {withAvatar && <Skeleton variant="circular" width={40} height={40} />}
          <div className="flex-1 space-y-2">
            <Skeleton variant="text" width="40%" height={20} />
            <Skeleton variant="text" width="70%" />
          </div>
          <Skeleton variant="rectangular" width={80} height={32} />
        </div>
      ))}
    </div>
  );
};

/**
 * Skeleton Dashboard - Full dashboard loading state
 */
export const SkeletonDashboard: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
      
      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6">
          <Skeleton variant="text" width="30%" height={24} className="mb-4" />
          <Skeleton variant="rectangular" height={300} />
        </div>
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6">
          <Skeleton variant="text" width="30%" height={24} className="mb-4" />
          <Skeleton variant="rectangular" height={300} />
        </div>
      </div>
      
      {/* Table */}
      <SkeletonTable rows={5} columns={5} />
    </div>
  );
};

/**
 * Skeleton with Shimmer Effect - More premium animation
 */
export const SkeletonShimmer: React.FC<SkeletonProps> = (props) => {
  return (
    <motion.div
      initial={{ opacity: 0.6 }}
      animate={{
        opacity: [0.6, 1, 0.6],
        backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
      }}
      transition={{
        duration: 2,
        repeat: Infinity,
        ease: 'linear',
      }}
      style={{
        background: 'linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%)',
        backgroundSize: '200% 100%',
      }}
    >
      <Skeleton {...props} animate={false} />
    </motion.div>
  );
};

export default Skeleton;
