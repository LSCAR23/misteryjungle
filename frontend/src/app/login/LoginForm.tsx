"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth";
import type { Usuario } from "@/lib/types";

const destino = (u: Usuario) =>
  u.rol === "admin" ? "/admin/dashboard" : "/disponibilidad";

export default function LoginForm() {
  const router = useRouter();
  const { usuario, cargando, login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [verPass, setVerPass] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [lento, setLento] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!cargando && usuario) router.replace(destino(usuario));
  }, [cargando, usuario, router]);

  useEffect(() => {
    if (!enviando) return;
    const t = setTimeout(() => setLento(true), 3000);
    return () => {
      clearTimeout(t);
      setLento(false);
    };
  }, [enviando]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (enviando) return;
    setError(null);
    setEnviando(true);
    try {
      const u = await login(username.trim(), password);
      router.replace(destino(u));
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo iniciar sesión");
      setEnviando(false);
    }
  }

  const input =
    "h-12 w-full rounded-xl border border-border bg-bg px-4 text-base text-ink placeholder:text-ink-muted focus:border-red focus:outline-none focus:ring-2 focus:ring-red/30";

  return (
    <div className="relative z-10 w-full max-w-sm rounded-2xl border border-border bg-surface p-6 shadow-sm sm:p-8">
      <div className="flex flex-col items-center text-center">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/logo.png"
          alt="Mistery Jungle"
          width={120}
          height={120}
          className="h-[120px] w-auto"
        />
        <h1 className="mt-4 font-display text-3xl font-bold uppercase tracking-wide">
          Disponibilidad de flota
        </h1>
      </div>

      <form onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
        <div className="space-y-1.5">
          <label htmlFor="username" className="text-sm font-medium">
            Usuario
          </label>
          <input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            autoCapitalize="none"
            autoCorrect="off"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className={input}
          />
        </div>
        <div className="space-y-1.5">
          <label htmlFor="password" className="text-sm font-medium">
            Contraseña
          </label>
          <div className="relative">
            <input
              id="password"
              name="password"
              type={verPass ? "text" : "password"}
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={`${input} pr-12`}
            />
            <button
              type="button"
              onClick={() => setVerPass((v) => !v)}
              aria-label={verPass ? "Ocultar contraseña" : "Mostrar contraseña"}
              className="absolute right-1 top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center rounded-lg text-ink-muted hover:text-ink"
            >
              {verPass ? <EyeOff size={20} /> : <Eye size={20} />}
            </button>
          </div>
        </div>

        {error && (
          <p
            role="alert"
            className="rounded-lg bg-red-soft px-3 py-2 text-sm font-medium text-red"
          >
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={enviando || !username || !password}
          className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-red text-base font-bold text-white transition-colors hover:bg-red-hover disabled:cursor-not-allowed disabled:opacity-60"
        >
          {enviando ? (
            <>
              <Loader2 size={20} className="animate-spin" /> Entrando…
            </>
          ) : (
            "Entrar"
          )}
        </button>

        {enviando && lento && (
          <p className="text-center text-sm text-ink-muted" aria-live="polite">
            Conectando con el servidor… (puede tardar hasta un minuto)
          </p>
        )}
      </form>
    </div>
  );
}
