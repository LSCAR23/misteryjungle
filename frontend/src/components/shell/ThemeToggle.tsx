"use client";

import { useSyncExternalStore } from "react";
import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";

const noopSubscribe = () => () => {};

export default function ThemeToggle() {
  const mounted = useSyncExternalStore(noopSubscribe, () => true, () => false);
  const { resolvedTheme, setTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      aria-label="Cambiar tema"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="inline-flex size-11 items-center justify-center rounded-full text-ink transition-colors hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red"
    >
      {mounted ? isDark ? <Sun className="size-5" /> : <Moon className="size-5" /> : <span className="size-5" />}
    </button>
  );
}
