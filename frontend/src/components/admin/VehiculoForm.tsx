"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useSWRConfig } from "swr";
import { Minus, Plus } from "lucide-react";
import { toast } from "sonner";
import { ApiError, apiFetch } from "@/lib/api";
import {
  CATEGORIAS,
  TARIFAS,
  UBICACIONES_REALES,
  type Categoria,
  type TarifaCodigo,
  type UbicacionReal,
} from "@/lib/constants";
import type { VehiculoDetalle } from "@/lib/types";
import { Button, Card, FieldError, FieldHint, Input, Label, Select, cn } from "@/components/ui";
import VehicleImage from "@/components/vehiculos/VehicleImage";

function slugify(s: string): string {
  return s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

interface PlacaRow {
  placa: string;
  ubicacion: UbicacionReal;
}

const MAX_PLACAS = 50;

export default function VehiculoForm() {
  const router = useRouter();
  const { mutate } = useSWRConfig();
  const [marca, setMarca] = useState("Honda");
  const [modelo, setModelo] = useState("");
  const [cilindrada, setCilindrada] = useState("");
  const [categoria, setCategoria] = useState<Categoria>("Scooter");
  const [imagen, setImagen] = useState("");
  const [precios, setPrecios] = useState<Partial<Record<TarifaCodigo, string>>>({});
  const [placas, setPlacas] = useState<PlacaRow[]>([{ placa: "", ubicacion: "Taller Nico" }]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const slug = slugify(`${marca}-${modelo}`);
  const previewSrc = imagen.trim() || (slug ? `/vehiculos/${slug}.png` : null);

  function setCantidad(n: number) {
    const c = Math.min(MAX_PLACAS, Math.max(1, n));
    setPlacas((prev) =>
      c <= prev.length
        ? prev.slice(0, c)
        : [
            ...prev,
            ...Array.from({ length: c - prev.length }, () => ({
              placa: "",
              ubicacion: prev[prev.length - 1]?.ubicacion ?? ("Taller Nico" as UbicacionReal),
            })),
          ],
    );
  }

  function updatePlaca(i: number, patch: Partial<PlacaRow>) {
    setPlacas((prev) => prev.map((p, idx) => (idx === i ? { ...p, ...patch } : p)));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const cc = Number(cilindrada);
    const preciosOut = TARIFAS.flatMap((t) => {
      const raw = (precios[t.codigo] ?? "").trim();
      if (!raw) return [];
      return [{ tarifa: t.codigo, monto: Number(raw) }];
    });

    let msg: string | null = null;
    if (!marca.trim()) msg = "La marca es obligatoria";
    else if (!modelo.trim()) msg = "El modelo es obligatorio";
    else if (!Number.isInteger(cc) || cc <= 0) msg = "La cilindrada debe ser un número mayor a 0";
    else if (preciosOut.length === 0) msg = "Agrega al menos un precio";
    else if (preciosOut.some((p) => !Number.isFinite(p.monto) || p.monto <= 0))
      msg = "Los precios deben ser mayores a 0";
    setError(msg);
    if (msg) {
      toast.error(msg);
      return;
    }

    setSaving(true);
    try {
      await apiFetch<VehiculoDetalle>("/vehiculos", {
        method: "POST",
        body: {
          marca: marca.trim(),
          modelo: modelo.trim(),
          cilindrada: cc,
          categoria,
          imagen: imagen.trim() || null,
          precios: preciosOut,
          placas: placas.map((p) => ({
            placa: p.placa.trim() || undefined,
            ubicacion_actual: p.ubicacion,
          })),
        },
      });
      toast.success("Vehículo creado");
      await mutate(
        (key) => typeof key === "string" && (key.startsWith("/vehiculos") || key.startsWith("/disponibilidad")),
      );
      router.push("/admin/vehiculos");
    } catch (err) {
      const m = err instanceof ApiError ? err.detail : "No se pudo crear el vehículo";
      setError(m);
      toast.error(m);
      setSaving(false);
    }
  }

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-4 pb-24 lg:pb-0">
      <Card className="space-y-4 p-4">
        <h2 className="font-display text-xl font-bold uppercase tracking-wide">Datos</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="marca">Marca</Label>
            <Input id="marca" value={marca} onChange={(e) => setMarca(e.target.value)} maxLength={50} />
          </div>
          <div>
            <Label htmlFor="modelo">Modelo</Label>
            <Input id="modelo" value={modelo} onChange={(e) => setModelo(e.target.value)} maxLength={80} />
          </div>
        </div>
        <div>
          <Label htmlFor="cilindrada">Cilindrada (cc)</Label>
          <Input
            id="cilindrada"
            type="number"
            inputMode="numeric"
            min={1}
            value={cilindrada}
            onChange={(e) => setCilindrada(e.target.value)}
          />
        </div>
        <div>
          <Label id="categoria-label">Categoría</Label>
          <div role="group" aria-labelledby="categoria-label" className="grid grid-cols-6 gap-2">
            {CATEGORIAS.map((c, i) => {
              const active = c.value === categoria;
              return (
                <button
                  key={c.value}
                  type="button"
                  aria-pressed={active}
                  onClick={() => setCategoria(c.value)}
                  className={cn(
                    "col-span-2 min-h-11 rounded-xl border text-sm font-semibold transition-colors",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red",
                    i === 3 && "col-start-2",
                    active
                      ? "border-red bg-red text-white"
                      : "border-border bg-surface text-ink-muted hover:text-ink",
                  )}
                >
                  {c.label}
                </button>
              );
            })}
          </div>
        </div>
      </Card>

      <Card className="space-y-3 p-4">
        <h2 className="font-display text-xl font-bold uppercase tracking-wide">Imagen</h2>
        <div>
          <Label htmlFor="imagen">Ruta de la imagen (opcional)</Label>
          <Input
            id="imagen"
            value={imagen}
            onChange={(e) => setImagen(e.target.value)}
            placeholder={slug ? `/vehiculos/${slug}.png` : "/vehiculos/marca-modelo.png"}
            autoCapitalize="none"
            spellCheck={false}
          />
          <FieldHint>
            Deja vacío para usar /vehiculos/{"{slug}"}.png — coloca el PNG sin fondo en frontend/public/vehiculos/
          </FieldHint>
        </div>
        <VehicleImage
          src={previewSrc}
          categoria={categoria}
          alt="Vista previa"
          className="mx-auto max-w-xs rounded-xl"
        />
      </Card>

      <Card className="space-y-3 p-4">
        <h2 className="font-display text-xl font-bold uppercase tracking-wide">Precios</h2>
        <FieldHint className="mt-0">Al menos una tarifa es obligatoria.</FieldHint>
        <div className="space-y-2">
          {TARIFAS.map((t) => (
            <div key={t.codigo} className="flex items-center gap-3">
              <label htmlFor={`precio-${t.codigo}`} className="flex-1 text-sm font-semibold">
                {t.etiqueta}
              </label>
              <div className="relative w-36">
                <span
                  aria-hidden="true"
                  className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink-muted"
                >
                  $
                </span>
                <Input
                  id={`precio-${t.codigo}`}
                  type="number"
                  inputMode="decimal"
                  min={0}
                  step="any"
                  value={precios[t.codigo] ?? ""}
                  onChange={(e) => setPrecios((p) => ({ ...p, [t.codigo]: e.target.value }))}
                  className="pl-8"
                />
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card className="space-y-3 p-4">
        <h2 className="font-display text-xl font-bold uppercase tracking-wide">Placas</h2>
        <div className="flex items-center justify-between gap-3">
          <span className="text-sm font-semibold">Cantidad</span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              aria-label="Menos unidades"
              disabled={placas.length <= 1}
              onClick={() => setCantidad(placas.length - 1)}
              className="size-11 px-0"
            >
              <Minus className="size-5" />
            </Button>
            <span className="w-10 text-center text-lg font-bold tabular-nums" aria-live="polite">
              {placas.length}
            </span>
            <Button
              variant="outline"
              aria-label="Más unidades"
              disabled={placas.length >= MAX_PLACAS}
              onClick={() => setCantidad(placas.length + 1)}
              className="size-11 px-0"
            >
              <Plus className="size-5" />
            </Button>
          </div>
        </div>
        {placas.length > 1 && (
          <div className="flex items-center gap-3">
            <label htmlFor="aplicar-todas" className="flex-1 text-sm text-ink-muted">
              Aplicar ubicación a todas
            </label>
            <div className="w-44">
              <Select
                id="aplicar-todas"
                value=""
                onChange={(e) => {
                  const u = e.target.value as UbicacionReal;
                  if (u) setPlacas((prev) => prev.map((p) => ({ ...p, ubicacion: u })));
                }}
              >
                <option value="">Elegir…</option>
                {UBICACIONES_REALES.map((u) => (
                  <option key={u} value={u}>
                    {u}
                  </option>
                ))}
              </Select>
            </div>
          </div>
        )}
        <ul className="space-y-2">
          {placas.map((p, i) => (
            <li key={i} className="grid grid-cols-[2rem_1fr] items-center gap-x-2 gap-y-2 sm:grid-cols-[2rem_1fr_1fr]">
              <span className="text-sm font-semibold text-ink-muted tabular-nums">{i + 1}</span>
              <Input
                value={p.placa}
                onChange={(e) => updatePlaca(i, { placa: e.target.value })}
                placeholder="NUEVA"
                maxLength={20}
                autoCapitalize="characters"
                aria-label={`Placa ${i + 1}`}
              />
              <div className="col-start-2 sm:col-start-auto">
                <Select
                  value={p.ubicacion}
                  onChange={(e) => updatePlaca(i, { ubicacion: e.target.value as UbicacionReal })}
                  aria-label={`Ubicación de placa ${i + 1}`}
                >
                  {UBICACIONES_REALES.map((u) => (
                    <option key={u} value={u}>
                      {u}
                    </option>
                  ))}
                </Select>
              </div>
            </li>
          ))}
        </ul>
      </Card>

      {error && <FieldError>{error}</FieldError>}

      <div className="fixed inset-x-0 bottom-[calc(4rem+env(safe-area-inset-bottom))] z-20 border-t border-border bg-bg/95 p-3 backdrop-blur lg:static lg:border-0 lg:bg-transparent lg:p-0 lg:backdrop-blur-none">
        <Button type="submit" size="lg" fullWidth loading={saving}>
          Crear vehículo
        </Button>
      </div>
    </form>
  );
}
