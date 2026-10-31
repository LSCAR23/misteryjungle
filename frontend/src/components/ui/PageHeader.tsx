import type { ReactNode } from "react";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { cn } from "./cn";

export interface PageHeaderProps {
  title: string;
  subtitle?: string;
  backHref?: string;
  backLabel?: string;
  actions?: ReactNode;
  className?: string;
}

export function PageHeader({ title, subtitle, backHref, backLabel = "Volver", actions, className }: PageHeaderProps) {
  return (
    <header className={cn("mb-5", className)}>
      {backHref && (
        <Link
          href={backHref}
          className="-ml-2 mb-1 inline-flex min-h-11 items-center gap-1 rounded-lg px-2 text-sm font-semibold text-ink-muted hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red"
        >
          <ChevronLeft className="size-5" aria-hidden="true" />
          {backLabel}
        </Link>
      )}
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            <span className="racing-stripe" aria-hidden="true" />
            <h1 className="truncate font-display text-3xl font-bold uppercase tracking-wide">{title}</h1>
          </div>
          {subtitle && <p className="mt-1 text-sm text-ink-muted">{subtitle}</p>}
        </div>
        {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
      </div>
    </header>
  );
}
