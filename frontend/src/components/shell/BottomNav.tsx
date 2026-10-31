"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Ellipsis, LogOut } from "lucide-react";
import { Sheet, cn } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { usePendientes } from "@/lib/usePendientes";
import { CountBadge, NAV_ITEMS, isActive, type NavItem } from "./NavItems";

const itemCls =
  "relative flex min-h-14 flex-1 flex-col items-center justify-center gap-0.5 text-[11px] font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-red";

function NavLink({ item, active, count }: { item: NavItem; active: boolean; count: number }) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      aria-current={active ? "page" : undefined}
      className={cn(itemCls, active ? "text-red" : "text-ink-muted")}
    >
      <span className="relative">
        <Icon className="size-6" />
        {item.badge && count > 0 ? (
          <span className="absolute -right-3 -top-1.5">
            <CountBadge count={count} />
          </span>
        ) : null}
      </span>
      {item.label}
    </Link>
  );
}

export default function BottomNav() {
  const pathname = usePathname();
  const { usuario, logout } = useAuth();
  const pendientes = usePendientes();
  const [more, setMore] = useState(false);
  const isAdmin = usuario?.rol === "admin";

  const items = NAV_ITEMS.filter(
    (i) => !i.adminOnly || (isAdmin && i.href === "/admin/dashboard"),
  );
  const extra = NAV_ITEMS.filter((i) => i.adminOnly && i.href !== "/admin/dashboard");
  const moreActive = extra.some((i) => isActive(pathname, i.href));

  return (
    <>
      <nav
        aria-label="Navegación principal"
        className="fixed inset-x-0 bottom-0 z-30 border-t border-border bg-bg pb-[env(safe-area-inset-bottom)] lg:hidden"
      >
        <div className="mx-auto flex max-w-xl">
          {items.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              active={isActive(pathname, item.href)}
              count={pendientes}
            />
          ))}
          {isAdmin ? (
            <button
              type="button"
              onClick={() => setMore(true)}
              className={cn(itemCls, moreActive ? "text-red" : "text-ink-muted")}
            >
              <Ellipsis className="size-6" />
              Más
            </button>
          ) : null}
        </div>
      </nav>
      <Sheet open={more} onClose={() => setMore(false)} title="Más">
        <ul className="flex flex-col gap-1 pb-2">
          {extra.map((item) => {
            const Icon = item.icon;
            const active = isActive(pathname, item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  onClick={() => setMore(false)}
                  className={cn(
                    "flex min-h-14 items-center gap-3 rounded-2xl px-4 text-base font-semibold",
                    active ? "bg-red-soft text-red" : "text-ink hover:bg-surface",
                  )}
                >
                  <Icon className="size-6" />
                  {item.label}
                </Link>
              </li>
            );
          })}
          <li>
            <button
              type="button"
              onClick={() => {
                setMore(false);
                logout();
              }}
              className="flex min-h-14 w-full items-center gap-3 rounded-2xl px-4 text-base font-semibold text-red hover:bg-red-soft"
            >
              <LogOut className="size-6" />
              Cerrar sesión
            </button>
          </li>
        </ul>
      </Sheet>
    </>
  );
}
