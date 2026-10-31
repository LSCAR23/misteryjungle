"use client";

import { useParams } from "next/navigation";
import VehiculoDetalleView from "@/components/vehiculos/VehiculoDetalleView";

export default function Page() {
  const params = useParams<{ categoria: string; vehiculoId: string }>();
  return (
    <VehiculoDetalleView
      vehiculoId={params.vehiculoId}
      backHref={`/disponibilidad/${params.categoria}`}
    />
  );
}
