import { ChevronDown } from "lucide-react";
import { TARIFAS } from "@/lib/constants";
import { formatMoney } from "@/lib/format";
import type { Precio } from "@/lib/types";

export default function PreciosTable({ precios }: { precios: Precio[] }) {
  const rows = TARIFAS.map((t) => ({
    ...t,
    monto: precios.find((p) => p.tarifa === t.codigo)?.monto,
  })).filter((r) => r.monto !== undefined);

  return (
    <details className="group rounded-2xl border border-border bg-bg">
      <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between px-4 font-semibold [&::-webkit-details-marker]:hidden">
        Tabla de precios
        <ChevronDown className="size-5 text-ink-muted transition-transform group-open:rotate-180" aria-hidden="true" />
      </summary>
      <ul className="divide-y divide-border border-t border-border">
        {rows.map((r) => (
          <li key={r.codigo} className="flex items-center justify-between px-4 py-2.5 text-sm">
            <span>{r.etiqueta}</span>
            <span className="font-semibold tabular-nums">{formatMoney(r.monto as number)}</span>
          </li>
        ))}
      </ul>
    </details>
  );
}
