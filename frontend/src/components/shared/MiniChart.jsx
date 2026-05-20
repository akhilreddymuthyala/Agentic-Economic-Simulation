import React from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from 'recharts'

export default function MiniChart({ data, dataKey, color, label, height = 90, referenceValue }) {
  return (
    <div style={{ background: '#0b1120', border: '1px solid #1a2744', borderRadius: 4, padding: '12px 16px' }}>
      <div style={{ fontSize: 9, color: '#64748b', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 10 }}>
        {label}
      </div>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="2 2" stroke="#1a2744" />
          <XAxis dataKey="tick" hide />
          <YAxis hide domain={['auto', 'auto']} />
          {referenceValue && (
            <ReferenceLine y={referenceValue} stroke="#1a2744" strokeDasharray="4 4" />
          )}
          <Tooltip
            contentStyle={{ background: '#0b1120', border: '1px solid #1a2744', fontSize: 10 }}
            labelStyle={{ color: '#64748b' }}
            itemStyle={{ color }}
          />
          <Line type="monotone" dataKey={dataKey} stroke={color} dot={false} strokeWidth={1.5} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}