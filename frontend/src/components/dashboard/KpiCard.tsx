import type { ReactNode } from "react";
import Link from "next/link";
import { Card, cn } from "@/components/ui";

export interface KpiCardProps {
  label: string;
  value: string;
  sub?: ReactNode;
  tone?: "default" | "warn";
  href?: string;
}

export function KpiCard({ label, value, sub, tone = "default", href }: KpiCardProps) {
  const body = (
    <Card
      interactive={!!href}
      className={cn("h-full p-4", tone === "warn" && "border-warn/50")}
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{label}</p>
      <p
        className={cn(
          "mt-1 truncate font-display text-3xl font-bold tabular-nums",
          tone === "warn" && "text-warn",
        )}
      >
        {value}
      </p>
      {sub && <div className="mt-1 text-sm text-ink-muted">{sub}</div>}
    </Card>
  );
  return href ? (
    <Link
      href={href}
      className="block rounded-2xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red"
    >
      {body}
    </Link>
  ) : (
    body
  );
}
