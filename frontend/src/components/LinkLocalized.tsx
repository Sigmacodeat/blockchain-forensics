import React from 'react'
import { Link, LinkProps } from 'react-router-dom'
import { useLocalePath } from '@/hooks/useLocalePath'

type Props = LinkProps & { to: string }

export default function LinkLocalized({ to, ...rest }: Props) {
  const localePath = useLocalePath()
  const localized = localePath(to)
  return <Link to={localized} {...rest} />
}
