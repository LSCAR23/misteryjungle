import type { HTMLAttributes } from "react";
import { cn } from "./cn";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  interactive?: boolean;
}

export function Card({ interactive, className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-border bg-bg shadow-sm dark:shadow-none",
        interactive &&
          "cursor-pointer transition-transform duration-150 hover:bg-surface active:scale-[0.99]",
        className,
      )}
      {...props}
    />
  );
}
