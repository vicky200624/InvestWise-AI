import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

export interface ChartDataPoint {
  name: string;
  value: number | string;
  color?: string;
  hex_color?: string;
}

export interface PortfolioDonutProps {
  data?: ChartDataPoint[];
}

const defaultData = [
  { name: 'Stocks', value: 65, color: '#8b5cf6' },
  { name: 'Mutual Funds', value: 20, color: '#06d6a0' },
  { name: 'Gold', value: 10, color: '#f59e0b' },
  { name: 'REITs', value: 5, color: '#ef4444' },
];

export function PortfolioDonut({ data = defaultData }: PortfolioDonutProps) {
  // Ensure the mapped data strictly provides exactly what Recharts expects
  const chartData = data.map((item, idx) => ({
    name: item.name,
    value: typeof item.value === 'number' ? item.value : Number(item.value) || 0,
    color: item.hex_color || item.color || defaultData[idx % defaultData.length].color,
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
            stroke="none"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'var(--color-surface-elevated)', 
              border: '1px solid var(--color-border)', 
              borderRadius: '8px' 
            }}
            itemStyle={{ color: '#fff' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export default PortfolioDonut;