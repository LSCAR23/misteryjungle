import Link from "next/link";
import { Card, cn } from "@/components/ui";
import { categoriaLabel, categoriaToSlug } from "@/lib/categorias";
import { imagenCategoria } from "@/lib/imagenes";
import type { CategoriaResumen } from "@/lib/types";

export default function CategoriaCard({ resumen }: { resumen: CategoriaResumen }) {
  const { categoria, disponibles, total } = resumen;
  const pct = total > 0 ? Math.round((disponibles / total) * 100) : 0;
  const vacio = disponibles === 0;
  const img = imagenCategoria(categoria);
  return (
    <Link
      href={`/disponibilidad/${categoriaToSlug(categoria)}`}
      className="block rounded-2xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red"
    >
      <Card interactive className={cn("flex h-full flex-col gap-3 p-4", vacio && "opacity-60")}>
        <div className="flex aspect-[3/2] items-center justify-center rounded-xl bg-surface">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={img.src}
            srcSet={img.srcSet || undefined}
            sizes="(min-width: 1024px) 20vw, (min-width: 768px) 33vw, 50vw"
            alt=""
            decoding="async"
            className="size-full object-contain p-[12%] dark:invert"
          />
        </div>
        <h2 className="font-display text-xl font-bold uppercase tracking-wide">{categoriaLabel(categoria)}</h2>
        <div className="flex items-baseline gap-1.5">
          <span className={cn("font-display text-4xl font-bold tabular-nums", vacio && "text-ink-muted")}>
            {disponibles}
          </span>
          <span className="text-sm text-ink-muted">de {total} {total === 1 ? "disponible" : "disponibles"}</span>
        </div>
        <div
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={total}
          aria-valuenow={disponibles}
          aria-label={`${disponibles} de ${total} disponibles`}
          className="h-1.5 w-full overflow-hidden rounded-full bg-surface-2"
        >
          <div className="h-full rounded-full bg-red" style={{ width: `${pct}%` }} />
        </div>
      </Card>
    </Link>
  );
}
