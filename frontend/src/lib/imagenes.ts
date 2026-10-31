import type { Categoria } from "@/lib/constants";
import { IMAGENES_CATEGORIAS, IMAGENES_VEHICULOS } from "@/lib/imagenes.generated";

export interface ImagenOptimizada {
  src: string;
  srcSet: string;
}

function armar(anchos: Record<string, string> | undefined): ImagenOptimizada | null {
  if (!anchos) return null;
  const pares = Object.entries(anchos).sort((a, b) => Number(a[0]) - Number(b[0]));
  if (pares.length === 0) return null;
  return {
    src: pares[pares.length - 1][1],
    srcSet: pares.map(([w, url]) => `${url} ${w}w`).join(", "),
  };
}

/** Versión WebP optimizada de la imagen de un vehículo (`/vehiculos/<slug>.png`), si existe. */
export function imagenVehiculo(src: string | null): ImagenOptimizada | null {
  const m = src?.match(/^\/vehiculos\/([a-z0-9-]+)\.png$/);
  return m ? armar(IMAGENES_VEHICULOS[m[1]]) : null;
}

/** Silueta de la categoría (WebP optimizado, o el SVG antiguo como respaldo). */
export function imagenCategoria(categoria: Categoria): ImagenOptimizada {
  return armar(IMAGENES_CATEGORIAS[categoria]) ?? { src: `/vehiculos/placeholders/${categoria}.svg`, srcSet: "" };
}
