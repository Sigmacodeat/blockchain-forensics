import React from 'react'

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={["rounded-lg border border-border bg-card text-card-foreground shadow-sm", className].filter(Boolean).join(' ')} {...props} />
)

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={["flex flex-col space-y-1 p-4", className].filter(Boolean).join(' ')} {...props} />
)

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ className, ...props }) => (
  <h3 className={["text-lg font-semibold leading-none tracking-tight", className].filter(Boolean).join(' ')} {...props} />
)

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({ className, ...props }) => (
  <p className={["text-sm text-muted-foreground", className].filter(Boolean).join(' ')} {...props} />
)

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <div className={["p-4 pt-0", className].filter(Boolean).join(' ')} {...props} />
)

export default Card
