"use client";

import { useEffect, useId, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { cn } from "./cn";

export interface SheetProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
}

const FOCUSABLE =
  "a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex='-1'])";

const noopSubscribe = () => () => {};

export function Sheet({ open, onClose, title, children, footer }: SheetProps) {
  const isClient = useSyncExternalStore(noopSubscribe, () => true, () => false);
  const [rendered, setRendered] = useState(false);
  const [shown, setShown] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  const titleId = useId();

  useEffect(() => {
    onCloseRef.current = onClose;
  });

  // Montaje / desmontaje animado
  useEffect(() => {
    let t: ReturnType<typeof setTimeout> | undefined;
    let raf = 0;
    if (open) {
      raf = requestAnimationFrame(() => {
        setRendered(true);
        raf = requestAnimationFrame(() => setShown(true));
      });
    } else {
      raf = requestAnimationFrame(() => {
        setShown(false);
        t = setTimeout(() => setRendered(false), 200);
      });
    }
    return () => {
      cancelAnimationFrame(raf);
      if (t) clearTimeout(t);
    };
  }, [open]);

  // Scroll lock, foco, Esc y trampa de foco
  useEffect(() => {
    if (!open || !rendered) return;
    const previous = document.activeElement as HTMLElement | null;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const panel = panelRef.current;
    const first = panel?.querySelector<HTMLElement>(FOCUSABLE);
    (first ?? panel)?.focus();

    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.stopPropagation();
        onCloseRef.current();
        return;
      }
      if (e.key !== "Tab" || !panel) return;
      const items = Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE));
      if (items.length === 0) {
        e.preventDefault();
        return;
      }
      const a = items[0];
      const z = items[items.length - 1];
      if (e.shiftKey && (document.activeElement === a || document.activeElement === panel)) {
        e.preventDefault();
        z.focus();
      } else if (!e.shiftKey && document.activeElement === z) {
        e.preventDefault();
        a.focus();
      }
    }
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
      previous?.focus?.();
    };
  }, [open, rendered]);

  if (!isClient || !rendered) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-end justify-center md:items-center md:p-6">
      <div
        onClick={onClose}
        aria-hidden="true"
        className={cn(
          "absolute inset-0 bg-black/50 transition-opacity duration-200",
          shown ? "opacity-100" : "opacity-0",
        )}
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className={cn(
          "relative flex max-h-[90dvh] w-full flex-col rounded-t-3xl bg-bg text-ink shadow-xl outline-none",
          "transition-[transform,opacity] duration-200 ease-out md:max-w-lg md:rounded-3xl",
          shown
            ? "translate-y-0 opacity-100"
            : "translate-y-full opacity-100 md:translate-y-4 md:opacity-0",
        )}
      >
        <div className="flex justify-center pt-2.5 md:hidden" aria-hidden="true">
          <span className="h-1.5 w-10 rounded-full bg-border" />
        </div>
        <div className="flex items-center justify-between gap-3 px-5 pb-2 pt-3 md:pt-5">
          <h2 id={titleId} className="font-display text-2xl font-bold uppercase tracking-wide">
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="-mr-2 inline-flex size-11 items-center justify-center rounded-full text-ink-muted hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red"
          >
            <X className="size-5" />
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-5 py-2">{children}</div>
        {footer ? (
          <div className="border-t border-border px-5 pb-[calc(env(safe-area-inset-bottom)+1rem)] pt-3">
            {footer}
          </div>
        ) : (
          <div className="pb-[env(safe-area-inset-bottom)]" />
        )}
      </div>
    </div>,
    document.body,
  );
}
