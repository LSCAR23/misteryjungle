// Costa Rica es UTC−6 fijo (sin horario de verano). Nunca se usa la zona del dispositivo.
const CR_OFFSET_MS = 6 * 60 * 60 * 1000;
const TZ = "America/Costa_Rica";

const p2 = (n: number) => String(n).padStart(2, "0");

/** Date cuyos campos getUTC* representan la hora de pared de CR. */
function crWall(ms: number): Date {
  return new Date(ms - CR_OFFSET_MS);
}

function wallToInput(w: Date): string {
  return `${w.getUTCFullYear()}-${p2(w.getUTCMonth() + 1)}-${p2(w.getUTCDate())}T${p2(w.getUTCHours())}:${p2(w.getUTCMinutes())}`;
}

export function crInputToISO(v: string): string {
  return `${v.slice(0, 16)}:00-06:00`;
}

export function isoToCrInput(iso: string): string {
  return wallToInput(crWall(new Date(iso).getTime()));
}

export function nowCrInput(): string {
  return wallToInput(crWall(Date.now()));
}

export function addHoursCrInput(baseIso: string, h: number): string {
  return wallToInput(crWall(new Date(baseIso).getTime() + h * 3_600_000));
}

export function todayAtCrInput(hh: number, mm: number): string {
  const w = crWall(Date.now());
  return `${w.getUTCFullYear()}-${p2(w.getUTCMonth() + 1)}-${p2(w.getUTCDate())}T${p2(hh)}:${p2(mm)}`;
}

export function formatCR(iso: string, opts?: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat("es-CR", {
    timeZone: TZ,
    ...(opts ?? {
      weekday: "short",
      day: "numeric",
      month: "short",
      hour: "numeric",
      minute: "2-digit",
    }),
  }).format(new Date(iso));
}

export function formatHoraCR(iso: string): string {
  return formatCR(iso, { hour: "numeric", minute: "2-digit" });
}

export function isTodayCR(iso: string): boolean {
  const a = crWall(new Date(iso).getTime());
  const b = crWall(Date.now());
  return (
    a.getUTCFullYear() === b.getUTCFullYear() &&
    a.getUTCMonth() === b.getUTCMonth() &&
    a.getUTCDate() === b.getUTCDate()
  );
}
