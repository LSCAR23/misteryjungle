"use client";

import { useState } from "react";
import type { Categoria } from "@/lib/constants";
import { imagenCategoria, imagenVehiculo } from "@/lib/imagenes";
import { cn } from "@/components/ui/cn";

export interface VehicleImageProps {
  src: string | null;
  categoria: Categoria;
  alt: string;
  className?: string;
  /** Imagen principal visible al cargar: se descarga primero en vez de en diferido. */
  priority?: boolean;
  /** Ancho aproximado en pantalla, para que el navegador elija el tamaño (atributo `sizes`). */
  sizes?: string;
}

// Orden de intento: WebP optimizado -> PNG original -> silueta de la categoría.
type Etapa = "optimizada" | "original" | "silueta";

export default function VehicleImage({
  src,
  categoria,
  alt,
  className,
  priority = false,
  sizes = "(min-width: 1280px) 33vw, (min-width: 768px) 50vw, 100vw",
}: VehicleImageProps) {
  const optimizada = imagenVehiculo(src);
  const inicial: Etapa = optimizada ? "optimizada" : src ? "original" : "silueta";
  const [fallo, setFallo] = useState<{ src: string | null; etapa: Etapa } | null>(null);
  // Si cambia `src`, se vuelve a empezar desde la mejor opción.
  const etapa = fallo && fallo.src === src ? fallo.etapa : inicial;

  const silueta = imagenCategoria(categoria);
  const actual =
    etapa === "optimizada" && optimizada
      ? optimizada
      : etapa === "original" && src
        ? { src, srcSet: "" }
        : silueta;
  const esSilueta = etapa === "silueta";

  function siguiente() {
    if (etapa === "optimizada") setFallo({ src, etapa: src ? "original" : "silueta" });
    else if (etapa === "original") setFallo({ src, etapa: "silueta" });
  }

  return (
    <div
      className={cn(
        "flex aspect-[3/2] w-full items-center justify-center overflow-hidden",
        "bg-[radial-gradient(ellipse_at_center,#ffffff_0%,#e9e9e9_100%)] dark:bg-[radial-gradient(ellipse_at_center,#222222_0%,#121212_100%)]",
        className,
      )}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        key={actual.src}
        src={actual.src}
        srcSet={actual.srcSet || undefined}
        sizes={actual.srcSet ? sizes : undefined}
        alt={alt}
        loading={priority ? "eager" : "lazy"}
        fetchPriority={priority ? "high" : "auto"}
        decoding="async"
        onError={siguiente}
        className={cn("size-full object-contain", esSilueta && "p-[14%] opacity-50 dark:invert")}
      />
    </div>
  );
}
