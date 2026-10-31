import { CATEGORIAS, type Categoria } from "./constants";

export function categoriaToSlug(c: Categoria): string {
  return c.toLowerCase();
}

export function slugToCategoria(s: string): Categoria | undefined {
  const slug = s.toLowerCase();
  return CATEGORIAS.find((c) => c.value.toLowerCase() === slug)?.value;
}

export function categoriaLabel(c: Categoria): string {
  return CATEGORIAS.find((x) => x.value === c)?.label ?? c;
}
