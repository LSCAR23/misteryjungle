import {
  Bike,
  LayoutDashboard,
  PackageCheck,
  Truck,
  Users,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  adminOnly?: boolean;
  badge?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/disponibilidad", label: "Disponibilidad", icon: Bike },
  { href: "/recibir", label: "Recibir", icon: PackageCheck, badge: true },
  { href: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard, adminOnly: true },
  { href: "/admin/vehiculos", label: "Vehículos", icon: Truck, adminOnly: true },
  { href: "/admin/usuarios", label: "Usuarios", icon: Users, adminOnly: true },
];

export function isActive(pathname: string, href: string): boolean {
  return pathname.startsWith(href);
}

export function navFor(isAdmin: boolean): NavItem[] {
  return NAV_ITEMS.filter((i) => !i.adminOnly || isAdmin);
}

export function CountBadge({ count }: { count: number }) {
  if (count <= 0) return null;
  return (
    <span
      aria-label={`${count} pendientes`}
      className="inline-flex min-w-5 items-center justify-center rounded-full bg-red px-1.5 text-[11px] font-bold leading-5 text-white tabular-nums"
    >
      {count > 99 ? "99+" : count}
    </span>
  );
}
