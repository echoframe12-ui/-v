import React from 'react'
import type { MoodStatus } from '../contracts/oceanic'

interface MoodBadgeProps {
  status: MoodStatus
  size?: 'sm' | 'md' | 'lg'
  pulse?: boolean
}

export const MoodBadge: React.FC<MoodBadgeProps> = ({
  status,
  size = 'md',
  pulse = true,
}) => {
  const isClear = status === 'clear'

  const sizeMap = {
    sm: { badge: '0.6rem', dot: 6 },
    md: { badge: '0.72rem', dot: 8 },
    lg: { badge: '0.85rem', dot: 10 },
  }

  const s = sizeMap[size]

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.4rem',
        padding: '0.2rem 0.6rem',
        border: `1px solid ${isClear ? '#2d5a3d' : '#5a2d2d'}`,
        background: isClear
          ? 'rgba(45, 90, 61, 0.15)'
          : 'rgba(90, 45, 45, 0.15)',
        backdropFilter: 'blur(8px)',
        fontSize: s.badge,
        fontFamily: '"IBM Plex Mono", monospace',
        letterSpacing: '0.1em',
        textTransform: 'uppercase',
        color: isClear ? '#7fbf7f' : '#bf7f7f',
        transition: 'all 0.4s ease',
      }}
    >
      <span
        style={{
          width: s.dot,
          height: s.dot,
          borderRadius: '50%',
          background: isClear ? '#7fbf7f' : '#bf7f7f',
          boxShadow: isClear
            ? '0 0 8px rgba(127, 191, 127, 0.6)'
            : '0 0 8px rgba(191, 127, 127, 0.6)',
          animation: pulse ? 'moodPulse 2s ease-in-out infinite' : 'none',
        }}
      />
      {status}
    </span>
  )
}

export default MoodBadge
