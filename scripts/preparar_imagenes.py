"""Prepara las imágenes de vehículos y categorías para la app.

Vehículos (`imagenes_vehiculos/`):
  - recorta el espacio transparente y deja un margen;
  - guarda el PNG de respaldo en `frontend/public/vehiculos/<slug>.png` (ruta que guarda la BD);
  - genera WebP livianos de 400 y 800 px en `frontend/public/img/vehiculos/`.
Categorías (`imagenes_categorias/`): WebP de 320 y 640 px en `frontend/public/img/categorias/`.

Los WebP llevan un hash del contenido en el nombre, así se pueden cachear "para siempre"
(si cambias la foto cambia el nombre). El mapa de archivos se escribe en
`frontend/src/lib/imagenes.generated.ts`.

Uso: python scripts/preparar_imagenes.py
"""
import hashlib
import io
import json
import re
import shutil
import sys
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN_VEH = RAIZ / "imagenes_vehiculos"
ORIGEN_CAT = RAIZ / "imagenes_categorias"
PUBLIC = RAIZ / "frontend" / "public"
DEST_PNG = PUBLIC / "vehiculos"
DEST_IMG = PUBLIC / "img"
MANIFIESTO = RAIZ / "frontend" / "src" / "lib" / "imagenes.generated.ts"

# Palabra clave en el nombre del archivo (minúsculas) -> slug del vehículo. El orden importa.
REGLAS = [
    (r"deluxe|crew", "honda-pioneer-deluxe-crew"),
    (r"pioneer", "honda-pioneer-4x4"),
    (r"talon.*(4wd|-4\b|x-4|4 ?plazas|4seat)", "honda-talon-4wd"),
    (r"talon", "honda-talon-4x4"),
    (r"rincon", "honda-rincon-4x4"),
    (r"trx|rancher|fourtrax", "honda-trx-4x4"),
    (r"crf ?300|rally", "honda-crf300-rally"),
    (r"crf ?250", "honda-crf250"),
    (r"xr ?190", "honda-xr190"),
    (r"cbf|cb ?150", "honda-cbf150s"),
    (r"elite", "honda-elite"),
    (r"navi", "honda-navi"),
    (r"isuzu|camion|camión|truck|serie ?q", "isuzu-serie-q"),
]
# Nombre del archivo de categoría (minúsculas, sin extensión) -> valor del enum Categoria
CATEGORIAS = {"scooter": "Scooter", "moto": "Moto", "atv": "ATV", "utv": "UTV", "camion": "Camion", "camión": "Camion"}

PNG_ANCHO_MAX = 800
ANCHOS_VEH = (400, 800)
ANCHOS_CAT = (320, 640)
MARGEN = 0.04


def slug_para(nombre: str) -> str | None:
    n = nombre.lower()
    for patron, slug in REGLAS:
        if re.search(patron, n):
            return slug
    return None


def recortar(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    caja = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if caja:
        im = im.crop(caja)
    m = int(max(im.size) * MARGEN)
    lienzo = Image.new("RGBA", (im.width + 2 * m, im.height + 2 * m), (0, 0, 0, 0))
    lienzo.paste(im, (m, m))
    return lienzo


def a_ancho(im: Image.Image, ancho: int) -> Image.Image:
    if im.width <= ancho:
        return im
    return im.resize((ancho, round(im.height * ancho / im.width)), Image.LANCZOS)


def guardar_webp(im: Image.Image, carpeta: Path, base: str, ancho: int) -> str:
    buf = io.BytesIO()
    a_ancho(im, ancho).save(buf, "WEBP", quality=80, method=6)
    datos = buf.getvalue()
    h = hashlib.sha1(datos).hexdigest()[:8]
    nombre = f"{base}-{ancho}.{h}.webp"
    (carpeta / nombre).write_bytes(datos)
    return f"/{carpeta.relative_to(PUBLIC).as_posix()}/{nombre}"


def limpiar(carpeta: Path) -> None:
    if carpeta.exists():
        shutil.rmtree(carpeta)
    carpeta.mkdir(parents=True)


def main() -> int:
    DEST_PNG.mkdir(parents=True, exist_ok=True)
    limpiar(DEST_IMG / "vehiculos")
    limpiar(DEST_IMG / "categorias")
    vehiculos: dict[str, dict[str, str]] = {}
    categorias: dict[str, dict[str, str]] = {}
    sin_asignar = []

    for archivo in sorted(ORIGEN_VEH.glob("*.png")):
        slug = slug_para(archivo.name)
        if not slug:
            sin_asignar.append(archivo.name)
            continue
        im = recortar(Image.open(archivo))
        a_ancho(im, PNG_ANCHO_MAX).save(DEST_PNG / f"{slug}.png", optimize=True)
        vehiculos[slug] = {str(w): guardar_webp(im, DEST_IMG / "vehiculos", slug, w) for w in ANCHOS_VEH}
        kb = sum((PUBLIC / u.lstrip("/")).stat().st_size for u in vehiculos[slug].values()) // 1024
        print(f"vehículo  {archivo.name}  ->  {slug}  (webp {kb} KB en total)")

    for archivo in sorted(ORIGEN_CAT.glob("*.png")):
        cat = CATEGORIAS.get(archivo.stem.lower())
        if not cat:
            sin_asignar.append(archivo.name)
            continue
        im = recortar(Image.open(archivo))
        categorias[cat] = {str(w): guardar_webp(im, DEST_IMG / "categorias", cat.lower(), w) for w in ANCHOS_CAT}
        print(f"categoría {archivo.name}  ->  {cat}")

    MANIFIESTO.write_text(
        "// Generado por scripts/preparar_imagenes.py. No editar a mano.\n"
        "// Rutas WebP optimizadas por ancho (px).\n"
        f"export const IMAGENES_VEHICULOS: Record<string, Record<string, string>> = {json.dumps(vehiculos, indent=2)};\n\n"
        f"export const IMAGENES_CATEGORIAS: Record<string, Record<string, string>> = {json.dumps(categorias, indent=2)};\n",
        encoding="utf-8",
    )
    print(f"manifiesto -> {MANIFIESTO.relative_to(RAIZ)}")
    for nombre in sin_asignar:
        print(f"SIN ASIGNAR (renómbralo con el modelo o la categoría): {nombre}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
