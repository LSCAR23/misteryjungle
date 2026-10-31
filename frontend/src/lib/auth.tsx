"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import { apiFetch, TOKEN_KEY, USER_KEY } from "./api";
import type { LoginResponse, Usuario } from "./types";

interface AuthCtx {
  usuario: Usuario | null;
  cargando: boolean;
  login: (username: string, password: string) => Promise<Usuario>;
  logout: () => void;
}

const Ctx = createContext<AuthCtx | null>(null);

function readUser(): Usuario | null {
  try {
    if (!window.localStorage.getItem(TOKEN_KEY)) return null;
    const raw = window.localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as Usuario) : null;
  } catch {
    return null;
  }
}

function writeUser(u: Usuario) {
  try {
    window.localStorage.setItem(USER_KEY, JSON.stringify(u));
  } catch {
    /* ignore */
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    const stored = readUser();
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setUsuario(stored);
    setCargando(false);
    if (!stored) return;
    let cancelled = false;
    apiFetch<Usuario>("/auth/me")
      .then((u) => {
        if (cancelled) return;
        writeUser(u);
        setUsuario(u);
      })
      .catch(() => {
        /* un 401 ya redirige en apiFetch; otros errores se ignoran */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const res = await apiFetch<LoginResponse>("/auth/login", {
      method: "POST",
      body: { username, password },
    });
    try {
      window.localStorage.setItem(TOKEN_KEY, res.access_token);
    } catch {
      /* ignore */
    }
    writeUser(res.usuario);
    setUsuario(res.usuario);
    return res.usuario;
  }, []);

  const logout = useCallback(() => {
    try {
      window.localStorage.removeItem(TOKEN_KEY);
      window.localStorage.removeItem(USER_KEY);
    } catch {
      /* ignore */
    }
    setUsuario(null);
    router.replace("/login");
  }, [router]);

  const value = useMemo(
    () => ({ usuario, cargando, login, logout }),
    [usuario, cargando, login, logout],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthCtx {
  const c = useContext(Ctx);
  if (!c) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return c;
}
