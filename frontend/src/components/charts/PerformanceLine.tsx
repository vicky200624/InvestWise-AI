import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const defaultData = [
  { date: '1', value: 4000 }, { date: '5', value: 4200 },
  { date: '10', value: 4100 }, { date: '15', value: 4500 },
  { date: '20', value: 4800 }, { date: '25', value: 4700 },
  { date: '30', value: 5200 },
];

export interface PerformanceLineProps {
  data?: Array<{ date?: string; month?: string; value?: number; return?: number }>;
}

export function PerformanceLine({ data = defaultData }: PerformanceLineProps) {
  const chartData = (data && data.length > 0 ? data : defaultData).map((item: any) => ({
    date: item.date || item.month || '',
    value: typeof item.value === 'number' ? item.value : (item.return || 0),
  }));


  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
          <XAxis dataKey="date" stroke="var(--color-text-secondary)" tick={{fontSize: 12}} axisLine={false} tickLine={false} />
          <YAxis stroke="var(--color-text-secondary)" tick={{fontSize: 12}} axisLine={false} tickLine={false} tickFormatter={(val) => `$${val}`} />
          <Tooltip 
            contentStyle={{ backgroundColor: 'var(--color-surface-elevated)', border: '1px solid var(--color-border)', borderRadius: '8px' }}
            labelStyle={{ color: 'var(--color-text-secondary)' }}
          />
          <Line type="monotone" dataKey="value" stroke="var(--color-primary)" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: 'var(--color-primary)' }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

