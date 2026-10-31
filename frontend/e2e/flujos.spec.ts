import { expect, test, type Page } from "@playwright/test";

const PASSWORD = process.env.E2E_PASSWORD ?? "";

async function login(page: Page, usuario: string) {
  await page.goto("/login");
  await page.getByLabel(/usuario/i).fill(usuario);
  await page.getByLabel(/contraseña/i).first().fill(PASSWORD);
  await page.getByRole("button", { name: /entrar/i }).click();
  await page.waitForURL((u) => !u.pathname.startsWith("/login"));
}

function erroresDePagina(page: Page) {
  const errores: string[] = [];
  page.on("pageerror", (e) => errores.push(e.message));
  return errores;
}

test.beforeAll(() => {
  if (!PASSWORD) throw new Error("Define E2E_PASSWORD para correr las pruebas e2e");
});

test("empleado: no entra a admin y renta una scooter", async ({ page }) => {
  const errores = erroresDePagina(page);
  await login(page, "oscar");
  await expect(page).toHaveURL(/\/disponibilidad$/);

  await page.goto("/admin/dashboard");
  await expect(page).toHaveURL(/\/disponibilidad$/);

  await page.getByRole("link", { name: /scooter/i }).first().click();
  await page.getByRole("link", { name: /honda navi/i }).click();
  const casilla = page.getByRole("checkbox").first();
  await casilla.evaluate((el: HTMLInputElement) => el.click());
  await page.getByRole("button", { name: /^rentar/i }).click();
  await page.getByRole("button", { name: /\+24 h/i }).click();
  const confirmar = page.getByRole("button", { name: /confirmar renta · \$/i });
  await expect(confirmar).toBeEnabled({ timeout: 10_000 });
  await confirmar.click();
  await expect(page.getByText(/renta registrada/i)).toBeVisible();
  expect(errores).toEqual([]);
});

test("admin: las pantallas cargan sin errores", async ({ page }) => {
  const errores = erroresDePagina(page);
  await login(page, "ivan");
  await expect(page).toHaveURL(/\/admin\/dashboard$/);
  await expect(page.getByText(/vehículo más popular/i)).toBeVisible();

  for (const ruta of ["/recibir", "/admin/usuarios", "/admin/vehiculos", "/admin/vehiculos/nuevo", "/admin/usuarios/nuevo"]) {
    await page.goto(ruta);
    await expect(page.locator("h1").first()).toBeVisible();
  }
  expect(errores).toEqual([]);
});
