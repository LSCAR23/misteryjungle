export function formatMoney(n: number): string {
  const whole = Number.isInteger(n);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: whole ? 0 : 2,
    maximumFractionDigits: whole ? 0 : 2,
  }).format(n);
}

export function formatPlaca(p: { placa: string; id: string }): string {
  return p.placa === "NUEVA"
    ? `NUEVA · ${p.id.slice(-4).toUpperCase()}`
    : p.placa;
}

export function pluralize(n: number, sing: string, plur: string): string {
  return n === 1 ? sing : plur;
}
