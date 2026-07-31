import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const defaultData = [

  { name: 'Stocks', value: 65, color: '#8b5cf6' },
  { name: 'Mutual Funds', value: 20, color: '#06d6a0' },
  { name: 'Gold', value: 10, color: '#f59e0b' },
  { name: 'REITs', value: 5, color: '#ef4444' },
];

export interface PortfolioDonutProps {
  data?: Array<{ name: string; value: number; color?: string; hex_color?: string }>;
}

export function PortfolioDonut({ data = defaultData }: PortfolioDonutProps) {
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
            contentStyle={{ backgroundColor: 'var(--color-surface-elevated)', border: '1px solid var(--color-border)', borderRadius: '8px' }}
            itemStyle={{ color: '#fff' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

