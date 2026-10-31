export type Categoria = "Scooter" | "Moto" | "ATV" | "UTV" | "Camion";
export type UbicacionReal =
  | "Playa Chiquita"
  | "Puerto Viejo"
  | "Playa Negra"
  | "B.Azul"
  | "Taller Nico";
export type UbicacionNoActualizada = "Ubicación no actualizada";
export type Ubicacion = UbicacionReal | UbicacionNoActualizada;
export type EstadoPlaca = "Rentada" | "Disponible" | "Fuera de Servicio";
export type TarifaCodigo = "5H" | "DIA" | "24H" | "2D" | "3D" | "1S" | "10D" | "MES";

export const CATEGORIAS: readonly { value: Categoria; label: string }[] = [
  { value: "Scooter", label: "Scooter" },
  { value: "Moto", label: "Moto" },
  { value: "ATV", label: "ATV" },
  { value: "UTV", label: "UTV" },
  { value: "Camion", label: "Camión" },
];

export const UBICACIONES_REALES: readonly UbicacionReal[] = [
  "Playa Chiquita",
  "Puerto Viejo",
  "Playa Negra",
  "B.Azul",
  "Taller Nico",
];

export const UBICACION_NO_ACTUALIZADA: UbicacionNoActualizada =
  "Ubicación no actualizada";

export const TARIFAS: readonly {
  codigo: TarifaCodigo;
  etiqueta: string;
  horas: number | null;
}[] = [
  { codigo: "5H", etiqueta: "5 horas", horas: 5 },
  { codigo: "DIA", etiqueta: "Día (8am–5:30pm)", horas: null },
  { codigo: "24H", etiqueta: "24 horas", horas: 24 },
  { codigo: "2D", etiqueta: "2 días", horas: 48 },
  { codigo: "3D", etiqueta: "3 días", horas: 72 },
  { codigo: "1S", etiqueta: "1 semana", horas: 168 },
  { codigo: "10D", etiqueta: "10 días", horas: 240 },
  { codigo: "MES", etiqueta: "Mes", horas: 720 },
];

export const ESTADOS_PLACA: readonly EstadoPlaca[] = [
  "Disponible",
  "Rentada",
  "Fuera de Servicio",
];
