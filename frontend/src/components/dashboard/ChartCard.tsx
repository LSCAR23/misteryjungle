import type { ReactNode } from "react";
import { Card, cn } from "@/components/ui";

export function ChartCard({
  title,
  children,
  className,
}: {
  title: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn("min-w-0 p-4", className)}>
      <h2 className="mb-3 font-display text-lg font-bold uppercase tracking-wide">{title}</h2>
      <div className="h-60 w-full min-w-0 md:h-70">{children}</div>
    </Card>
  );
}
