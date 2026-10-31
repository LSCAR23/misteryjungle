import type { ReactNode } from "react";
import { Card } from "@/components/ui";

export interface HighlightCardProps {
  icon: ReactNode;
  label: string;
  title?: string | null;
  detail?: string;
}

export function HighlightCard({ icon, label, title, detail }: HighlightCardProps) {
  return (
    <Card className="flex items-start gap-3 p-4">
      <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-red-soft text-red [&>svg]:size-5">
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{label}</p>
        {title ? (
          <>
            <p className="truncate text-base font-bold">{title}</p>
            {detail && <p className="truncate text-sm text-ink-muted">{detail}</p>}
          </>
        ) : (
          <p className="text-base text-ink-muted">Sin datos</p>
        )}
      </div>
    </Card>
  );
}
