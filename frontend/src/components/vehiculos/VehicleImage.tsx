"use client";

import { useState } from "react";
import type { Categoria } from "@/lib/constants";
import { cn } from "@/components/ui/cn";

export interface VehicleImageProps {
  src: string | null;
  categoria: Categoria;
  alt: string;
  className?: string;
}

export default function VehicleImage({ src, categoria, alt, className }: VehicleImageProps) {
  const placeholder = `/vehiculos/placeholders/${categoria}.svg`;
  const [failedSrc, setFailedSrc] = useState<string | null>(null);
  const usePlaceholder = !src || failedSrc === src;
  const finalSrc = usePlaceholder ? placeholder : src;

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
        key={finalSrc}
        src={finalSrc}
        alt={alt}
        loading="lazy"
        onError={() => {
          if (!usePlaceholder && src) setFailedSrc(src);
        }}
        className={cn("size-full object-contain", usePlaceholder && "p-[12%] opacity-60 dark:invert")}
      />
    </div>
  );
}
