"use client";

import useSWR from "swr";
import { swrFetcher } from "./api";
import { useAuth } from "./auth";
import type { RecibirResponse } from "./types";

export function usePendientes(): number {
  const { usuario } = useAuth();
  const { data } = useSWR<RecibirResponse>(
    usuario ? "/recibir" : null,
    swrFetcher,
    { refreshInterval: 60000, shouldRetryOnError: false },
  );
  if (!data) return 0;
  return (
    (data.vencidas?.length ?? 0) +
    (data.hoy?.length ?? 0) +
    (data.sin_ubicacion?.length ?? 0)
  );
}
