"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { Button, cn } from "@/components/ui";
import type { EstadoPlaca } from "@/lib/types";

export interface ActionBarProps {
  count: number;
  estado: EstadoPlaca | null;
  isAdmin: boolean;
  onClear: () => void;
  onRentar: () => void;
  onFueraServicio: () => void;
  onHabilitar: () => void;
}

export default function ActionBar({ count, estado, isAdmin, onClear, onRentar, onFueraServicio, onHabilitar }: ActionBarProps) {
  const [shown, setShown] = useState(false);
  const visible = count > 0;
  useEffect(() => {
    if (!visible) return;
    const raf = requestAnimationFrame(() => setShown(true));
    return () => {
      cancelAnimationFrame(raf);
      setShown(false);
    };
  }, [visible]);

  if (!visible) return null;
  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-[calc(env(safe-area-inset-bottom)+72px)] z-30 flex justify-center px-3 lg:bottom-4 lg:pl-64">
      <div
        role="region"
        aria-label="Acciones de selección"
        className={cn(
          "pointer-events-auto flex w-full max-w-2xl items-center gap-2 rounded-2xl border border-border bg-bg p-2 pl-4 shadow-lg transition-all duration-200",
          shown ? "translate-y-0 opacity-100" : "translate-y-6 opacity-0",
        )}
      >
        <p className="min-w-0 flex-1 text-sm font-semibold tabular-nums">
          {count} {count === 1 ? "seleccionada" : "seleccionadas"}
        </p>
        <button
          type="button"
          onClick={onClear}
          aria-label="Limpiar selección"
          className="inline-flex size-11 shrink-0 items-center justify-center rounded-full text-ink-muted hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red"
        >
          <X className="size-5" />
        </button>
        {estado === "Disponible" && (
          <>
            {isAdmin && (
              <Button variant="outline" onClick={onFueraServicio}>
                Fuera de servicio
              </Button>
            )}
            <Button onClick={onRentar}>Rentar</Button>
          </>
        )}
        {estado === "Fuera de Servicio" && isAdmin && <Button onClick={onHabilitar}>Habilitar</Button>}
      </div>
    </div>
  );
}
