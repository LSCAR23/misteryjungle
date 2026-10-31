"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Spinner } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import BottomNav from "./BottomNav";
import Header from "./Header";
import Sidebar from "./Sidebar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { usuario, cargando } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const blockedAdmin =
    !!usuario && usuario.rol === "empleado" && pathname.startsWith("/admin");

  useEffect(() => {
    if (cargando) return;
    if (!usuario) router.replace("/login");
    else if (blockedAdmin) router.replace("/disponibilidad");
  }, [cargando, usuario, blockedAdmin, router]);

  if (cargando) {
    return (
      <div className="flex min-h-dvh flex-col items-center justify-center gap-4 bg-bg">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/logo.png" alt="Mistery Jungle" width={64} height={64} className="size-16 object-contain" />
        <Spinner className="size-6 text-red" />
      </div>
    );
  }
  if (!usuario || blockedAdmin) return null;

  return (
    <div className="min-h-dvh bg-bg text-ink lg:flex">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <Header />
        <main className="mx-auto max-w-6xl px-4 py-4 pb-[calc(env(safe-area-inset-bottom)+80px)] md:px-6 md:py-6 lg:pb-6">
          {children}
        </main>
      </div>
      <BottomNav />
    </div>
  );
}
