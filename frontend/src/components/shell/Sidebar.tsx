"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut } from "lucide-react";
import { Badge, cn } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { usePendientes } from "@/lib/usePendientes";
import { CountBadge, isActive, navFor } from "./NavItems";
import ThemeToggle from "./ThemeToggle";

export default function Sidebar() {
  const pathname = usePathname();
  const { usuario, logout } = useAuth();
  const pendientes = usePendientes();
  const items = navFor(usuario?.rol === "admin");

  return (
    <aside className="sticky top-0 hidden h-dvh w-64 shrink-0 flex-col border-r border-t-2 border-border border-t-red bg-bg lg:flex">
      <div className="flex items-center gap-3 px-5 py-5">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/logo.png" alt="" width={40} height={40} className="size-10 rounded-md object-contain" />
        <span className="font-display text-2xl font-bold uppercase leading-none tracking-wide">
          MISTERY JUNGLE
        </span>
      </div>
      <nav aria-label="Navegación principal" className="flex-1 overflow-y-auto px-3 py-2">
        <ul className="flex flex-col gap-1">
          {items.map((item) => {
            const Icon = item.icon;
            const active = isActive(pathname, item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red",
                    active ? "bg-red-soft text-red" : "text-ink hover:bg-surface",
                  )}
                >
                  <Icon className="size-5" />
                  <span className="flex-1">{item.label}</span>
                  {item.badge ? <CountBadge count={pendientes} /> : null}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="border-t border-border p-3">
        {usuario ? (
          <div className="flex items-center justify-between gap-2 px-2 pb-2">
            <span className="truncate text-sm font-semibold">{usuario.username}</span>
            <Badge tone={usuario.rol === "admin" ? "red" : "neutral"}>{usuario.rol}</Badge>
          </div>
        ) : null}
        <div className="flex items-center gap-1">
          <ThemeToggle />
          <button
            type="button"
            onClick={logout}
            className="flex min-h-11 flex-1 items-center gap-2 rounded-xl px-3 text-sm font-medium text-red hover:bg-red-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red"
          >
            <LogOut className="size-4" />
            Cerrar sesión
          </button>
        </div>
      </div>
    </aside>
  );
}
