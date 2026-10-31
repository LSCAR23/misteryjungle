import type { HTMLAttributes } from "react";
import { cn } from "./cn";

export type BadgeTone = "neutral" | "red" | "ok" | "warn" | "off";

const tones: Record<BadgeTone, string> = {
  neutral: "bg-surface-2 text-ink",
  red: "bg-red-soft text-red",
  ok: "bg-ok/15 text-ok",
  warn: "bg-warn/15 text-warn",
  off: "bg-off/15 text-off",
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: BadgeTone;
}

export function Badge({ tone = "neutral", className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold tabular-nums",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}
