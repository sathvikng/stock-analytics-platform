"use client";
import { TableData } from "../lib/types";

export default function DataTable({ data }: { data: TableData }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-glass max-h-72">
      <table className="min-w-full text-sm text-left">
        <thead className="sticky top-0" style={{ background: "rgba(10,10,20,0.85)" }}>
          <tr>
            {data.columns.map((col) => (
              <th key={col} className="px-3 py-2 font-semibold whitespace-nowrap text-secondary">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.rows.map((row, i) => (
            <tr
              key={i}
              className="border-t border-glass hover:bg-white/5 transition-colors"
            >
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-1.5 text-primary whitespace-nowrap">
                  {cell ?? "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
