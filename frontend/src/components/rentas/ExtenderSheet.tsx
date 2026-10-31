"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { AlertTriangle } from "lucide-react";
import { Button, FieldError, FieldHint, Input, Label, Sheet, Skeleton } from "@/components/ui";
import { ApiError, apiFetch } from "@/lib/api";
import { formatMoney, formatPlaca } from "@/lib/format";
import {
  addHoursCrInput,
  crInputToISO,
  formatCR,
  isoToCrInput,
  nowCrInput,
  todayAtCrInput,
} from "@/lib/time";
import type { CotizacionResp, Renta } from "@/lib/types";

const MIN_MS = 15 * 60_000;

interface QuoteState {
  key: string;
  resp: CotizacionResp | null;
  error: string | null;
}

export default function ExtenderSheet({
  open,
  onClose,
  renta,
  onDone,
}: {
  open: boolean;
  onClose: () => void;
  renta: Renta | null;
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

  const rentaId = renta?.id ?? "";
  const finProgMs = renta ? Date.parse(renta.fin_programado) : NaN;
  const nowMs = Date.parse(now);
  const baseMs = Math.max(nowMs, Number.isNaN(finProgMs) ? 0 : finProgMs);
  const baseIso = new Date(baseMs).toISOString();

  const finMs = fin ? Date.parse(crInputToISO(fin)) : NaN;
  const hasFin = !Number.isNaN(finMs);
  const tooSoon = hasFin && finMs <= baseMs + MIN_MS;
  const valid = !!renta && hasFin && !tooSoon;
  const key = `${rentaId}|${fin}`;

  useEffect(() => {
    if (!open || !valid || !rentaId) return;
    const ctrl = new AbortController();
    const t = setTimeout(async () => {
      try {
        const resp = await apiFetch<CotizacionResp>(`/rentas/${rentaId}/extender/cotizar`, {
          method: "POST",
          body: { fin: crInputToISO(fin) },
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
  }, [open, valid, fin, rentaId, key]);

  const current = valid && quote?.key === key ? quote : null;
  const loadingQuote = valid && !current;
  const total = current?.resp?.total ?? null;
  const finLabel = hasFin ? formatCR(crInputToISO(fin)) : "";

  async function confirmar() {
    if (!valid || submitting || !renta) return;
    setSubmitting(true);
    try {
      await apiFetch<Renta>(`/rentas/${renta.id}/extender`, {
        method: "POST",
        body: { fin: crInputToISO(fin) },
      });
      toast.success(`Renta extendida hasta ${finLabel}`);
      onDone();
      onClose();
    } catch (e) {
      const detail = e instanceof ApiError ? e.detail : "No se pudo extender la renta";
      if (e instanceof ApiError && e.status === 409) {
        toast.error(detail);
        onDone();
        onClose();
      } else {
        setQuote({ key, resp: null, error: detail });
        setSubmitting(false);
      }
    }
  }

  const baseInput = isoToCrInput(baseIso);
  const chips: { label: string; value: () => string }[] = [
    { label: "+5 h", value: () => addHoursCrInput(baseIso, 5) },
  ];
  if (baseInput.slice(0, 10) === nowCrInput().slice(0, 10) && baseInput.slice(11) < "17:00") {
    chips.push({ label: "Hoy 5:30 pm", value: () => todayAtCrInput(17, 30) });
  }
  chips.push(
    { label: "+24 h", value: () => addHoursCrInput(baseIso, 24) },
    { label: "+3 días", value: () => addHoursCrInput(baseIso, 72) },
    { label: "+1 semana", value: () => addHoursCrInput(baseIso, 168) },
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
        {total !== null ? `Extender · ${formatMoney(total)}` : "Extender"}
      </Button>
      {!hasFin && <FieldHint className="text-center">Elige la nueva fecha y hora de devolución</FieldHint>}
    </div>
  );

  const vencida = renta?.estado === "vencida_sin_recibir";
  const item = current?.resp?.items[0];

  return (
    <Sheet open={open} onClose={onClose} title="Extender renta" footer={footer}>
      {renta && (
        <div className="space-y-5 pb-2">
          <p className="text-sm text-ink-muted">
            {renta.vehiculo} · {formatPlaca({ placa: renta.placa, id: renta.placa_id })}
          </p>

          <div>
            <p className="text-sm">
              <span className="font-semibold">Fin actual:</span>{" "}
              <span className="text-ink-muted">{formatCR(renta.fin_programado)}</span>
            </p>
            {vencida && (
              <p className="mt-2 flex items-start gap-1.5 text-sm font-medium text-amber-600 dark:text-amber-400">
                <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
                Renta vencida: la extensión empieza desde el fin anterior
              </p>
            )}
          </div>

          <div>
            <Label htmlFor="extender-fin">Nuevo fin</Label>
            <Input
              id="extender-fin"
              type="datetime-local"
              value={fin}
              min={baseInput}
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
            {tooSoon && (
              <FieldError>La nueva devolución debe ser al menos 15 minutos después del fin actual</FieldError>
            )}
            {current?.error && <FieldError>{current.error}</FieldError>}
          </div>

          {loadingQuote && (
            <div className="space-y-2" aria-busy="true" aria-label="Calculando precio">
              <Skeleton className="h-12" />
              <Skeleton className="h-14" />
            </div>
          )}

          {current?.resp && (
            <div>
              {item && <p className="text-sm text-ink-muted">{item.desglose}</p>}
              <div className="mt-3 flex items-baseline justify-between">
                <span className="text-sm font-semibold uppercase tracking-wide text-ink-muted">Monto</span>
                <span className="font-display text-4xl font-bold tabular-nums">
                  {formatMoney(current.resp.total)}
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </Sheet>
  );
}
