import { defineConfig, devices } from "@playwright/test";

// Requiere la app corriendo (docker compose + npm run dev) y E2E_PASSWORD con la contraseña de los usuarios demo.
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  workers: 1,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    timezoneId: "Europe/Madrid", // a propósito distinta a CR: la app no debe depender de la zona del dispositivo
  },
  projects: [
    { name: "movil", use: { ...devices["Pixel 7"] } },
    { name: "desktop", use: { viewport: { width: 1280, height: 800 } } },
  ],
});
