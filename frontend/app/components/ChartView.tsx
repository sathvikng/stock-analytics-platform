"use client";
import { ChartConfig, TableData } from "../lib/types";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, Legend, ResponsiveContainer,
} from "recharts";

const COLORS = ["#6366f1", "#22d3ee", "#f59e0b", "#10b981", "#f43f5e", "#a78bfa"];

function toChartData(data: TableData): Record<string, string | number>[] {
  return data.rows.map((row) =>
    Object.fromEntries(
      data.columns.map((col, i) => [col, isNaN(Number(row[i])) ? row[i] ?? "" : Number(row[i])])
    )
  );
}

export default function ChartView({ data, config }: { data: TableData; config: ChartConfig }) {
  const chartData = toChartData(data);
  const tooltipStyle = {
    background: "rgba(10,10,20,0.95)",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: "8px",
  };

  if (config.chart_type === "pie") {
    const key = config.series[0] ?? data.columns[1];
    return (
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie data={chartData} dataKey={key} nameKey={config.x_key} cx="50%" cy="50%" outerRadius={100} label>
            {chartData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
          </Pie>
          <Tooltip contentStyle={tooltipStyle} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    );
  }
  const Chart = config.chart_type === "bar" ? BarChart : LineChart;
  const Series = config.chart_type === "bar" ? Bar : Line;
  return (
    <ResponsiveContainer width="100%" height={260}>
      <Chart data={chartData}>
        <XAxis dataKey={config.x_key} tick={{ fill: "#94a3b8", fontSize: 11 }} />
        <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
        <Tooltip contentStyle={tooltipStyle} />
        <Legend />
        {config.series.map((s, i) => (
          <Series
            key={s}
            dataKey={s}
            stroke={COLORS[i % COLORS.length]}
            fill={COLORS[i % COLORS.length]}
            dot={false}
            type="monotone"
          />
        ))}
      </Chart>
    </ResponsiveContainer>
  );
}
