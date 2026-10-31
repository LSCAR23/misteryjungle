"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { AlertTriangle } from "lucide-react";
import { Button, FieldError, FieldHint, Input, Label, Sheet, Skeleton } from "@/components/ui";
import { ApiError, apiFetch } from "@/lib/api";
import { formatMoney, formatPlaca, pluralize } from "@/lib/format";
import {
  addHoursCrInput,
  crInputToISO,
  formatCR,
  nowCrInput,
  todayAtCrInput,
} from "@/lib/time";
import type { CotizacionResp, Placa, Renta, Vehiculo } from "@/lib/types";

const MIN_MS = 15 * 60_000;

interface QuoteState {
  key: string;
  resp: CotizacionResp | null;
  error: string | null;
}

export default function RentarSheet({
  open,
  onClose,
  placas,
  vehiculo,
  onDone,
}: {
  open: boolean;
  onClose: () => void;
  placas: Placa[];
  vehiculo: Vehiculo;
  onDone: () => void;
}) {
  const [fin, setFin] = useState("");
  const [now, setNow] = useState(() => new Date().toISOString());
  const [quote, setQuote] = useState<QuoteState | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [prevOpen, setPrevOpen] = useState(false);

  // Reinicia el estado cada vez que se abre
  if (open !== prevOpen) {
    setPrevOpen(open);
    if (open) {
      setFin("");
      setQuote(null);
      setSubmitting(false);
      setNow(new Date().toISOString());
    }
  }

  useEffect(() => {
    if (!open) return;
    const t = setInterval(() => setNow(new Date().toISOString()), 30_000);
    return () => clearInterval(t);
  }, [open]);

  const placaIds = useMemo(() => placas.map((p) => p.id), [placas]);
  const idsKey = placaIds.join(",");
  const sinUbicacion = placas.some((p) => p.ubicacion_actual === "Ubicación no actualizada");

  const finMs = fin ? Date.parse(crInputToISO(fin)) : NaN;
  const nowMs = Date.parse(now);
  const hasFin = !Number.isNaN(finMs);
  const tooSoon = hasFin && finMs <= nowMs + MIN_MS;
  const valid = hasFin && !tooSoon;
  const key = `${idsKey}|${fin}`;

  useEffect(() => {
    if (!open || !valid) return;
    const ctrl = new AbortController();
    const t = setTimeout(async () => {
      try {
        const resp = await apiFetch<CotizacionResp>("/rentas/cotizar", {
          method: "POST",
          body: { placa_ids: idsKey.split(","), fin: crInputToISO(fin) },
          signal: ctrl.signal,
        });
        setQuote({ key, resp, error: null });
      } catch (e) {
        if (e instanceof DOMException && e.name === "AbortError") return;
        setQuote({
          key,
          resp: null,
          error: e instanceof ApiError ? e.detail : "No se pudo calcular el precio",
        });
      }
    }, 300);
    return () => {
      clearTimeout(t);
      ctrl.abort();
    };
  }, [open, valid, fin, idsKey, key]);

  const current = valid && quote?.key === key ? quote : null;
  const loadingQuote = valid && !current;
  const total = current?.resp?.total ?? null;
  const finLabel = hasFin ? formatCR(crInputToISO(fin)) : "";

  async function confirmar() {
    if (!valid || submitting) return;
    setSubmitting(true);
    try {
      const rentas = await apiFetch<Renta[]>("/rentas", {
        method: "POST",
        body: { placa_ids: placaIds, fin: crInputToISO(fin) },
      });
      const n = rentas.length || placaIds.length;
      toast.success(`Renta registrada: ${n} ${pluralize(n, "placa", "placas")} hasta ${finLabel}`);
      onDone();
      onClose();
    } catch (e) {
      const detail = e instanceof ApiError ? e.detail : "No se pudo registrar la renta";
      toast.error(detail);
      if (e instanceof ApiError && e.status === 409) {
        onDone();
        onClose();
      } else {
        setSubmitting(false);
      }
    }
  }

  const nowInput = nowCrInput();
  const chips: { label: string; value: () => string }[] = [
    { label: "+5 h", value: () => addHoursCrInput(new Date().toISOString(), 5) },
  ];
  if (nowInput.slice(11) < "17:00") {
    chips.push({ label: "Hoy 5:30 pm", value: () => todayAtCrInput(17, 30) });
  }
  chips.push(
    { label: "+24 h", value: () => addHoursCrInput(new Date().toISOString(), 24) },
    { label: "+3 días", value: () => addHoursCrInput(new Date().toISOString(), 72) },
    { label: "+1 semana", value: () => addHoursCrInput(new Date().toISOString(), 168) },
  );

  const footer = (
    <div>
      <Button
        size="lg"
        fullWidth
        loading={submitting}
        disabled={!valid || loadingQuote || !current?.resp}
        onClick={confirmar}
      >
        {total !== null ? `Confirmar renta · ${formatMoney(total)}` : "Confirmar renta"}
      </Button>
      {!hasFin && <FieldHint className="text-center">Elige la fecha y hora de devolución</FieldHint>}
    </div>
  );

  return (
    <Sheet
      open={open}
      onClose={onClose}
      title={`Rentar ${vehiculo.marca} ${vehiculo.modelo}`}
      footer={footer}
    >
      <div className="space-y-5 pb-2">
        <div>
          <div className="flex flex-wrap gap-2">
            {placas.map((p) => (
              <span
                key={p.id}
                className="rounded-full border border-border bg-surface px-3 py-1 text-sm font-semibold tabular-nums"
              >
                {formatPlaca(p)}
              </span>
            ))}
          </div>
          {sinUbicacion && (
            <p className="mt-2 flex items-start gap-1.5 text-sm font-medium text-amber-600 dark:text-amber-400">
              <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
              Ubicación no actualizada en alguna placa seleccionada
            </p>
          )}
        </div>

        <p className="text-sm">
          <span className="font-semibold">Inicio:</span>{" "}
          <span className="text-ink-muted">Ahora · {formatCR(now)}</span>
        </p>

        <div>
          <Label htmlFor="rentar-fin">Fin</Label>
          <Input
            id="rentar-fin"
            type="datetime-local"
            value={fin}
            min={nowInput}
            onChange={(e) => setFin(e.target.value)}
            aria-invalid={tooSoon || !!current?.error || undefined}
          />
          <div className="-mx-5 mt-3 flex gap-2 overflow-x-auto px-5 pb-1">
            {chips.map((c) => (
              <button
                key={c.label}
                type="button"
                onClick={() => setFin(c.value())}
                className="min-h-10 shrink-0 rounded-full border border-border bg-surface px-4 text-sm font-semibold hover:bg-surface-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red"
              >
                {c.label}
              </button>
            ))}
          </div>
          {tooSoon && <FieldError>La devolución debe ser al menos 15 minutos después de ahora</FieldError>}
          {current?.error && <FieldError>{current.error}</FieldError>}
        </div>

        {loadingQuote && (
          <div className="space-y-2" aria-busy="true" aria-label="Calculando precio">
            {placas.map((p) => (
              <Skeleton key={p.id} className="h-12" />
            ))}
            <Skeleton className="h-14" />
          </div>
        )}

        {current?.resp && (
          <div>
            <ul className="divide-y divide-border rounded-xl border border-border">
              {current.resp.items.map((it) => (
                <li key={it.placa_id} className="flex items-start justify-between gap-3 px-4 py-3">
                  <div className="min-w-0">
                    <p className="font-semibold tabular-nums">{it.placa}</p>
                    <p className="text-sm text-ink-muted">{it.desglose}</p>
                  </div>
                  <p className="shrink-0 font-semibold tabular-nums">{formatMoney(it.monto)}</p>
                </li>
              ))}
            </ul>
            <div className="mt-3 flex items-baseline justify-between">
              <span className="text-sm font-semibold uppercase tracking-wide text-ink-muted">Total</span>
              <span className="font-display text-4xl font-bold tabular-nums">
                {formatMoney(current.resp.total)}
              </span>
            </div>
          </div>
        )}
      </div>
    </Sheet>
  );
}
