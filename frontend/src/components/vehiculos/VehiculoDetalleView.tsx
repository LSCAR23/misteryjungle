"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import useSWR, { useSWRConfig } from "swr";
import { toast } from "sonner";
import { AlertTriangle, SearchX } from "lucide-react";
import { Button, EmptyState, PageHeader, Sheet, Skeleton, cn } from "@/components/ui";
import { ApiError, apiFetch, swrFetcher } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { CATEGORIAS } from "@/lib/constants";
import type { EstadoPlaca, Placa, VehiculoDetalle } from "@/lib/types";
import RentarSheet from "@/components/rentas/RentarSheet";
import VehicleImage from "./VehicleImage";
import PreciosTable from "./PreciosTable";
import PlacaCard from "./PlacaCard";
import ActionBar from "./ActionBar";
import EditarPlacaSheet from "./EditarPlacaSheet";

type Accion = "fuera_servicio" | "habilitar";

export default function VehiculoDetalleView({ vehiculoId, backHref }: { vehiculoId: string; backHref: string }) {
  const { usuario } = useAuth();
  const isAdmin = usuario?.rol === "admin";
  const { mutate: globalMutate } = useSWRConfig();
  const { data, error, isLoading, mutate } = useSWR<VehiculoDetalle>(`/vehiculos/${vehiculoId}`, swrFetcher);

  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [filtro, setFiltro] = useState<string>("Todas");
  const [editando, setEditando] = useState<Placa | null>(null);
  const [rentarOpen, setRentarOpen] = useState(false);
  const [confirmar, setConfirmar] = useState<Accion | null>(null);
  const [enviando, setEnviando] = useState(false);

  const visibles = useMemo(
    () => (data?.placas ?? []).filter((p) => isAdmin || p.estado !== "Fuera de Servicio"),
    [data, isAdmin],
  );

  const ubicaciones = useMemo(() => {
    const m = new Map<string, number>();
    for (const p of visibles) m.set(p.ubicacion_actual, (m.get(p.ubicacion_actual) ?? 0) + 1);
    return [...m.entries()];
  }, [visibles]);

  const filtradas = useMemo(
    () => (filtro === "Todas" ? visibles : visibles.filter((p) => p.ubicacion_actual === filtro)),
    [visibles, filtro],
  );

  const placasById = useMemo(() => new Map((data?.placas ?? []).map((p) => [p.id, p])), [data]);
  const selPlacas = [...selected].map((id) => placasById.get(id)).filter((p): p is Placa => !!p);
  const selEstado: EstadoPlaca | null = selPlacas[0]?.estado ?? null;

  const canSelect = (p: Placa) => p.estado === "Disponible" || (isAdmin && p.estado === "Fuera de Servicio");

  function toggle(p: Placa) {
    if (selected.has(p.id)) {
      const next = new Set(selected);
      next.delete(p.id);
      setSelected(next);
      return;
    }
    if (selected.size > 0 && selEstado !== p.estado) {
      toast.message("Se limpió la selección: no puedes mezclar estados");
      setSelected(new Set([p.id]));
      return;
    }
    setSelected(new Set(selected).add(p.id));
  }

  const objetivo: EstadoPlaca = selEstado ?? "Disponible";
  const seleccionables = filtradas.filter((p) => canSelect(p) && p.estado === objetivo);
  const todasSel = seleccionables.length > 0 && seleccionables.every((p) => selected.has(p.id));

  function seleccionarTodas() {
    setSelected(todasSel ? new Set() : new Set(seleccionables.map((p) => p.id)));
  }

  function revalidar() {
    void mutate();
    void globalMutate((key) => typeof key === "string" && key.startsWith("/disponibilidad"));
  }

  async function ejecutar() {
    if (!confirmar) return;
    const n = selected.size;
    setEnviando(true);
    try {
      await apiFetch("/placas/estado", { method: "POST", body: { placa_ids: [...selected], accion: confirmar } });
      toast.success(
        confirmar === "fuera_servicio"
          ? `${n} ${n === 1 ? "placa puesta fuera de servicio" : "placas puestas fuera de servicio"}`
          : `${n} ${n === 1 ? "placa habilitada" : "placas habilitadas"}`,
      );
      setSelected(new Set());
      setConfirmar(null);
    } catch (e) {
      toast.error(e instanceof ApiError ? e.detail : "No se pudo completar la acción");
      if (e instanceof ApiError && e.status === 409) {
        setSelected(new Set());
        setConfirmar(null);
      }
    } finally {
      setEnviando(false);
      revalidar();
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-40" />
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="aspect-[3/2] w-full" />
          <div className="space-y-3">
            <Skeleton className="h-9 w-3/4" />
            <Skeleton className="h-5 w-1/2" />
            <Skeleton className="h-5 w-2/3" />
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    const notFound = error instanceof ApiError && error.status === 404;
    return notFound ? (
      <EmptyState
        icon={<SearchX />}
        title="Vehículo no encontrado"
        action={
          <Link href={backHref}>
            <Button variant="outline">Volver</Button>
          </Link>
        }
      />
    ) : (
      <EmptyState
        icon={<AlertTriangle />}
        title="No se pudo cargar"
        description={error instanceof ApiError ? error.detail : undefined}
        action={<Button onClick={() => void mutate()}>Reintentar</Button>}
      />
    );
  }

  const disp = data.placas.filter((p) => p.estado === "Disponible").length;
  const rent = data.placas.filter((p) => p.estado === "Rentada").length;
  const fuera = data.placas.filter((p) => p.estado === "Fuera de Servicio").length;
  const catLabel = CATEGORIAS.find((c) => c.value === data.categoria)?.label ?? data.categoria;
  const nombre = `${data.marca} ${data.modelo}`;
  const nSel = selected.size;
  const chips: [string, number][] = [["Todas", visibles.length], ...ubicaciones];

  return (
    <div className="pb-48 lg:pb-32">
      <PageHeader title={nombre} backHref={backHref} className="md:hidden" />
      <div className="grid gap-4 md:grid-cols-2 md:items-center">
        <div className="overflow-hidden rounded-2xl border border-border">
          <VehicleImage src={data.imagen} categoria={data.categoria} alt={nombre} priority sizes="(min-width: 768px) 50vw, 100vw" />
        </div>
        <div>
          <div className="hidden md:block">
            <PageHeader title={nombre} backHref={backHref} className="mb-3" />
          </div>
          <p className="text-ink-muted">
            {data.cilindrada} cc · {catLabel}
          </p>
          <p className="mt-2 text-sm font-semibold tabular-nums">
            <span className="text-ok">{disp} {disp === 1 ? "disponible" : "disponibles"}</span> · {rent} {rent === 1 ? "rentada" : "rentadas"} · {fuera} fuera de servicio
          </p>
        </div>
      </div>

      <div className="mt-4">
        <PreciosTable precios={data.precios} />
      </div>

      <div className="mt-5 flex flex-wrap gap-2" role="group" aria-label="Filtrar por ubicación">
        {chips.map(([u, c]) => (
          <button
            key={u}
            type="button"
            aria-pressed={filtro === u}
            onClick={() => setFiltro(u)}
            className={cn(
              "min-h-11 rounded-full border px-4 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red",
              filtro === u ? "border-red bg-red text-white" : "border-border bg-bg hover:bg-surface",
            )}
          >
            {u} <span className="tabular-nums">· {c}</span>
          </button>
        ))}
      </div>

      <div className="mt-4 flex items-center justify-between gap-3">
        <h2 className="font-display text-xl font-bold uppercase tracking-wide">Placas</h2>
        {seleccionables.length > 0 && (
          <Button variant="outline" size="sm" className="min-h-11" onClick={seleccionarTodas}>
            {todasSel ? "Quitar selección" : "Seleccionar todas"}
          </Button>
        )}
      </div>

      {filtradas.length === 0 ? (
        <EmptyState title="Sin placas" description="No hay placas para este filtro." />
      ) : (
        <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {filtradas.map((p) => (
            <PlacaCard
              key={p.id}
              placa={p}
              selected={selected.has(p.id)}
              selectable={canSelect(p)}
              onToggle={() => toggle(p)}
              onEdit={isAdmin ? () => setEditando(p) : undefined}
            />
          ))}
        </div>
      )}

      <ActionBar
        count={nSel}
        estado={selEstado}
        isAdmin={isAdmin}
        onClear={() => setSelected(new Set())}
        onRentar={() => setRentarOpen(true)}
        onFueraServicio={() => setConfirmar("fuera_servicio")}
        onHabilitar={() => setConfirmar("habilitar")}
      />

      <EditarPlacaSheet placa={editando} onClose={() => setEditando(null)} onSaved={revalidar} />

      <RentarSheet
        open={rentarOpen}
        onClose={() => setRentarOpen(false)}
        placas={selPlacas}
        vehiculo={data}
        onDone={() => {
          setRentarOpen(false);
          setSelected(new Set());
          revalidar();
        }}
      />

      <Sheet
        open={confirmar !== null}
        onClose={() => !enviando && setConfirmar(null)}
        title="Confirmar"
        footer={
          <div className="flex gap-2">
            <Button variant="outline" fullWidth onClick={() => setConfirmar(null)} disabled={enviando}>
              Cancelar
            </Button>
            <Button fullWidth loading={enviando} onClick={ejecutar}>
              Confirmar
            </Button>
          </div>
        }
      >
        <p className="py-4 text-lg">
          {confirmar === "habilitar"
            ? `¿Habilitar ${nSel} ${nSel === 1 ? "placa" : "placas"}?`
            : `¿Poner ${nSel} ${nSel === 1 ? "placa" : "placas"} fuera de servicio?`}
        </p>
      </Sheet>
    </div>
  );
}
