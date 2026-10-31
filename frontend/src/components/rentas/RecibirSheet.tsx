"use client";

import { useState } from "react";
import { MapPin } from "lucide-react";
import { toast } from "sonner";
import { Sheet, Spinner } from "@/components/ui";
import { apiFetch, ApiError } from "@/lib/api";
import { UBICACIONES_REALES } from "@/lib/constants";

interface Props {
  open: boolean;
  onClose: () => void;
  rentaIds: string[];
  placaIds: string[];
  onDone: () => void;
}

export function RecibirSheet({ open, onClose, rentaIds, placaIds, onDone }: Props) {
  const [busy, setBusy] = useState<string | null>(null);
  const total = rentaIds.length + placaIds.length;

  async function elegir(ubicacion: string) {
    if (busy) return;
    setBusy(ubicacion);
    try {
      const res = await apiFetch<{ rentas_finalizadas: number; placas_actualizadas: number }>("/recibir", {
        method: "POST",
        body: {
          renta_ids: rentaIds.length ? rentaIds : undefined,
          placa_ids: placaIds.length ? placaIds : undefined,
          ubicacion,
        },
      });
      toast.success(`Recibidos: ${res?.placas_actualizadas ?? total}`);
      onDone();
    } catch (e) {
      toast.error(e instanceof ApiError ? e.detail : "No se pudo completar la acción");
    } finally {
      setBusy(null);
    }
  }

  return (
    <Sheet open={open} onClose={busy ? () => {} : onClose} title="Recibir en…">
      <p className="mb-3 text-sm text-ink-muted">
        {total} {total === 1 ? "vehículo" : "vehículos"}. Elige dónde quedó.
      </p>
      <div className="flex flex-col gap-2 pb-4">
        {UBICACIONES_REALES.map((u) => (
          <button
            key={u}
            type="button"
            disabled={busy !== null}
            onClick={() => elegir(u)}
            className="flex h-14 w-full items-center gap-3 rounded-xl border border-border bg-surface px-4 text-left text-base font-semibold hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red disabled:opacity-50"
          >
            {busy === u ? <Spinner className="size-5" /> : <MapPin className="size-5 text-red" aria-hidden="true" />}
            {u}
          </button>
        ))}
      </div>
    </Sheet>
  );
}
