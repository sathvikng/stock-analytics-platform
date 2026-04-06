"use client";
import { StepData } from "../lib/types";

const STEP_LABELS: Record<string, string> = {
  symbol_resolution: "Resolving symbols",
  sql_generation: "Analyzing query",
  sql_execution: "Querying database",
  chart_build: "Building chart",
};

interface Props {
  steps: StepData[];
  isComplete: boolean;
}

export default function StreamingMessage({ steps, isComplete }: Props) {
  return (
    <div className="space-y-2 py-1 min-w-[180px]">
      {steps.map((step, i) => (
        <div key={i} className="flex items-center gap-2 text-xs">
          {step.status === "running" ? (
            <span className="step-spinner" />
          ) : (
            <span className="step-check">✓</span>
          )}
          <span className={step.status === "done" ? "text-secondary" : "text-primary"}>
            {STEP_LABELS[step.step] ?? step.step}
            {step.result ? `: ${step.result}` : ""}
          </span>
        </div>
      ))}
      {!isComplete && steps.length === 0 && (
        <div className="flex items-center gap-1.5">
          <span className="dot-pulse" />
          <span className="text-xs text-secondary">Thinking…</span>
        </div>
      )}
    </div>
  );
}
