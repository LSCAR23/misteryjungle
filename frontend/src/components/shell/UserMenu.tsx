"use client";

import { useEffect, useRef, useState } from "react";
import { LogOut, User } from "lucide-react";
import { Badge, cn } from "@/components/ui";
import { useAuth } from "@/lib/auth";

export default function UserMenu() {
  const { usuario, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (!usuario) return null;

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        aria-label="Menú de usuario"
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "inline-flex size-11 items-center justify-center rounded-full text-ink transition-colors hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red",
          open && "bg-surface",
        )}
      >
        <User className="size-5" />
      </button>
      {open ? (
        <div
          role="menu"
          className="absolute right-0 top-full z-50 mt-2 w-60 rounded-2xl border border-border bg-bg p-2 shadow-lg"
        >
          <div className="flex items-center justify-between gap-2 px-3 py-2">
            <span className="truncate text-sm font-semibold">{usuario.username}</span>
            <Badge tone={usuario.rol === "admin" ? "red" : "neutral"}>{usuario.rol}</Badge>
          </div>
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              setOpen(false);
              logout();
            }}
            className="flex min-h-11 w-full items-center gap-2 rounded-xl px-3 text-sm font-medium text-red hover:bg-red-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red"
          >
            <LogOut className="size-4" />
            Cerrar sesión
          </button>
        </div>
      ) : null}
    </div>
  );
}
