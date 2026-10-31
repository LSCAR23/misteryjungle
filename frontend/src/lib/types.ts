import type {
  Categoria,
  EstadoPlaca,
  TarifaCodigo,
  Ubicacion,
} from "./constants";

export type { Categoria, EstadoPlaca, TarifaCodigo, Ubicacion };
export type { UbicacionReal, UbicacionNoActualizada } from "./constants";

export type Rol = "admin" | "empleado";
export type EstadoRenta = "activa" | "vencida_sin_recibir" | "finalizada";

export interface Usuario {
  id: string;
  username: string;
  rol: Rol;
  activo: boolean;
  created_at: string;
}

export interface Precio {
  tarifa: TarifaCodigo;
  monto: number;
}

export interface Placa {
  id: string;
  placa: string;
  vehiculo_id: string;
  estado: EstadoPlaca;
  ubicacion_actual: Ubicacion;
  fecha_hora_finalizacion: string | null;
}

export interface Vehiculo {
  id: string;
  marca: string;
  modelo: string;
  slug: string;
  imagen: string | null;
  cilindrada: number;
  categoria: Categoria;
  cantidad: number;
  precios: Precio[];
}

export interface VehiculoDetalle extends Vehiculo {
  placas: Placa[];
}

export interface CategoriaResumen {
  categoria: Categoria;
  disponibles: number;
  total: number;
}

export interface VehiculoDisponibilidad extends Vehiculo {
  disponibles: number;
  por_ubicacion: { ubicacion: Ubicacion; disponibles: number }[];
}

export interface Cotizacion {
  placa_id: string;
  vehiculo: string;
  placa: string;
  monto: number;
  desglose: string;
}

export interface CotizacionResp {
  inicio: string;
  fin: string;
  items: Cotizacion[];
  total: number;
}

export interface Renta {
  id: string;
  placa_id: string;
  placa: string;
  vehiculo_id: string;
  vehiculo: string;
  categoria: Categoria;
  usuario: string;
  inicio: string;
  fin_programado: string;
  fin_real: string | null;
  monto: number;
  desglose: string;
  estado: EstadoRenta;
  ubicacion_placa: Ubicacion;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  usuario: Usuario;
}

export interface RecibirResponse {
  vencidas: Renta[];
  hoy: Renta[];
  sin_ubicacion: (Placa & { vehiculo: string })[];
}

export interface Metricas {
  kpis: {
    ingresos_mes_actual: number;
    ingresos_mes_anterior: number;
    rentas_mes_actual: number;
    ocupacion_actual: number;
    unidades_total: number;
    unidades_rentadas: number;
    unidades_fuera_servicio: number;
    pendientes_recibir: number;
    duracion_promedio_horas: number;
    ticket_promedio: number;
  };
  vehiculo_mas_popular: { vehiculo: string; rentas: number } | null;
  vehiculo_mas_ingresos: { vehiculo: string; ingresos: number } | null;
  usuario_top: { usuario: string; rentas: number; ingresos: number } | null;
  mes_top: { mes: string; rentas: number; ingresos: number } | null;
  por_mes: { mes: string; rentas: number; ingresos: number }[];
  por_vehiculo: {
    vehiculo: string;
    categoria: Categoria;
    rentas: number;
    ingresos: number;
  }[];
  por_categoria: { categoria: Categoria; rentas: number; ingresos: number }[];
  por_usuario: { usuario: string; rentas: number; ingresos: number }[];
  por_dia_semana: { dia: string; rentas: number }[];
  disponibles_por_ubicacion: { ubicacion: Ubicacion; disponibles: number }[];
}
